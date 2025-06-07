import logging
from typing import Dict, Any, Optional, List
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import credentials as google_credentials
from google.oauth2 import service_account
import streamlit as st
import time
import os

from utils.config import REGNUM_ADMIN_GROUP, BYPASS_GROUP_CHECK
from utils.logger import app_logger as logger

# Path to service account key file
SERVICE_ACCOUNT_FILE = '/secrets/sa/service_account.json'  # Cloud Run path
LOCAL_SERVICE_ACCOUNT_FILE = 'regnum-service-account-key.json'  # Local development path

# Configure logging
logger = logging.getLogger(__name__)

# Cache group membership results to reduce API calls
# Use TTL of 5 minutes (300 seconds)
GROUP_MEMBERSHIP_CACHE = {}
GROUP_MEMBERSHIP_CACHE_TTL = 300

def get_directory_service():
    """
    Creates and returns a Google Directory API service using service account credentials.
    The service account must have domain-wide delegation enabled.
    
    Returns:
        Google Directory API service object or None if failed
    """
    # Check if we should bypass authentication
    if BYPASS_GROUP_CHECK:
        logger.info("Bypassing Directory API service creation due to BYPASS_GROUP_CHECK=true")
        return None
    
    try:
        # Determine which service account file to use
        sa_key_path = SERVICE_ACCOUNT_FILE if os.path.exists(SERVICE_ACCOUNT_FILE) else LOCAL_SERVICE_ACCOUNT_FILE
        
        if not os.path.exists(sa_key_path):
            logger.error(f"Service account key file not found at {sa_key_path}")
            return None
        
        # Load service account credentials
        credentials = service_account.Credentials.from_service_account_file(
            sa_key_path,
            scopes=['https://www.googleapis.com/auth/admin.directory.group.member.readonly'],
            subject='webminister@westkingdom.org'  # Domain admin to impersonate
        )
        
        # Build the Directory API service
        service = build('admin', 'directory_v1', credentials=credentials)
        logger.info("Directory API service created successfully")
        return service
        
    except Exception as e:
        logger.error(f"Error creating Directory API service: {str(e)}")
        return None

def is_group_member(email, group_id):
    """
    Checks if a user is a member of a Google Group using the Directory API.
    
    Args:
        email: User email address to check
        group_id: Google Group ID or email address
        
    Returns:
        True if user is a member, False otherwise
    """
    # Check if we should bypass group membership checks
    if BYPASS_GROUP_CHECK:
        logger.info(f"Bypassing group membership check for {email} in group {group_id} due to BYPASS_GROUP_CHECK=true")
        return True
    
    # Check cache first
    cache_key = f"{email}:{group_id}"
    current_time = time.time()
    
    if cache_key in GROUP_MEMBERSHIP_CACHE:
        cached_result, cached_time = GROUP_MEMBERSHIP_CACHE[cache_key]
        if current_time - cached_time < GROUP_MEMBERSHIP_CACHE_TTL:
            logger.info(f"Using cached group membership result for {email} in {group_id}: {cached_result}")
            return cached_result
    
    try:
        service = get_directory_service()
        if not service:
            logger.warning("Could not create Directory API service, defaulting to False")
            return False
        
        # Try to get the member from the group
        logger.info(f"Checking if {email} is a member of group {group_id}")
        
        try:
            # Use the members().get() method to check membership
            result = service.members().get(groupKey=group_id, memberKey=email).execute()
            
            # If we get here without exception, the user is a member
            is_member = True
            logger.info(f"User {email} is a member of group {group_id}")
            
        except HttpError as e:
            if e.resp.status == 404:
                # 404 means the member is not in the group
                is_member = False
                logger.info(f"User {email} is NOT a member of group {group_id}")
            else:
                # Other HTTP errors
                logger.error(f"HTTP error checking group membership: {e}")
                is_member = False
        
        # Cache the result
        GROUP_MEMBERSHIP_CACHE[cache_key] = (is_member, current_time)
        return is_member
        
    except Exception as e:
        logger.error(f"Error checking group membership for {email} in {group_id}: {str(e)}")
        return False

def require_group_membership(group_id: str = REGNUM_ADMIN_GROUP):
    """
    Decorator function to require group membership for specific WKRegnum pages.
    
    Usage:
        @require_group_membership()
        def my_app_page():
            st.title("Protected Page")
            # Rest of your page
    
    Args:
        group_id: The email address of the required Google Group
        
    Returns:
        Function that checks membership and conditionally runs the decorated function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Ensure we have a session state
            if 'user_email' not in st.session_state or not st.session_state.user_email:
                st.error("You must be logged in to access this page.")
                st.info("Please return to the home page to authenticate.")
                st.stop()
            
            # Check if user is a member of the required group
            user_email = st.session_state.user_email
            if not is_group_member(user_email, group_id):
                # Use a more user-friendly error message
                friendly_group_name = "regnum-site" if group_id == REGNUM_ADMIN_GROUP else group_id
                st.error(f"Access denied: You must be a member of the '{friendly_group_name}' group to access this page.")
                
                # Add a helpful message about how to get access
                st.warning("If you need access to this page, please contact webminister@westkingdom.org to be added to the appropriate group.")
                
                # Add debug information if in development
                if os.environ.get('STREAMLIT_ENV') == 'development':
                    st.info(f"Debug: Checking membership for {user_email} in group {group_id}")
                
                st.stop()
            
            # If we get here, user has permission, so run the function
            return func(*args, **kwargs)
        return wrapper
    return decorator 