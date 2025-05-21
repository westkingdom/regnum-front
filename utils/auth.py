import logging
from typing import Dict, Any, Optional, List
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import credentials as google_credentials
from google.oauth2 import service_account
import streamlit as st
import time
import os

from utils.config import REGNUM_ADMIN_GROUP

# Path to service account key file
SERVICE_ACCOUNT_FILE = '/secrets/sa/service_account.json'  # Cloud Run path
LOCAL_SERVICE_ACCOUNT_FILE = 'regnum-service-account-key.json'  # Local development path

# Configure logging
logger = logging.getLogger(__name__)

# Cache group membership results to reduce API calls
# Use TTL of 5 minutes (300 seconds)
GROUP_MEMBERSHIP_CACHE = {}
GROUP_MEMBERSHIP_CACHE_TTL = 300

def get_directory_service(credentials=None, impersonate_user: str = "webminister@westkingdom.org") -> Optional[Any]:
    """
    Creates a Google Directory API service object.
    
    Args:
        credentials: User credentials from OAuth flow, if available
        impersonate_user: The admin user to impersonate if using service account
        
    Returns:
        A Directory API service object or None if creation fails
    """
    try:
        # If user credentials provided, use them directly
        if credentials and isinstance(credentials, google_credentials.Credentials):
            logger.info(f"Building directory service with user credentials")
            # Check if the required scope is available
            required_scope = 'https://www.googleapis.com/auth/admin.directory.group.member.readonly'
            if hasattr(credentials, 'scopes') and required_scope in credentials.scopes:
                logger.info(f"User credentials have required scope")
                return build('admin', 'directory_v1', credentials=credentials)
            else:
                logger.warning(f"User credentials missing required scope: {required_scope}")
                # Fall back to service account if user creds lack proper scope
                logger.info(f"Falling back to service account")
        
        # Use service account with domain-wide delegation
        import os
        # Try Cloud Run path first, then local development path
        sa_file = SERVICE_ACCOUNT_FILE if os.path.exists(SERVICE_ACCOUNT_FILE) else LOCAL_SERVICE_ACCOUNT_FILE
        
        if not os.path.exists(sa_file):
            logger.error(f"Service account file not found at {sa_file}")
            return None
            
        # Create service account credentials with domain-wide delegation
        scopes = [
            'https://www.googleapis.com/auth/admin.directory.group.readonly',
            'https://www.googleapis.com/auth/admin.directory.group.member.readonly',
            'https://www.googleapis.com/auth/admin.directory.user.readonly'
        ]
        
        logger.info(f"Loading service account from: {sa_file}")
        
        sa_credentials = service_account.Credentials.from_service_account_file(
            sa_file, 
            scopes=scopes,
            subject=impersonate_user  # Impersonate an admin
        )
        
        # Build and return the service
        logger.info(f"Building directory service with service account impersonating {impersonate_user}")
        return build('admin', 'directory_v1', credentials=sa_credentials)
    
    except Exception as e:
        logger.error(f"Error creating directory service: {e}")
        return None

def is_group_member(email: str, group_id: str = REGNUM_ADMIN_GROUP) -> bool:
    """
    Checks if a user is a member of the specified Google Group.
    
    This function uses caching to reduce API calls, with a TTL of 5 minutes.
    
    Args:
        email: The email address of the user to check
        group_id: The ID of the Google Group
        
    Returns:
        True if the user is a member, False otherwise
    """
    if not email or not group_id:
        return False
    
    # Normalize email addresses for comparison
    email = email.lower().strip()
    group_id = group_id.lower().strip()
    
    # Check cache first
    cache_key = f"{email}:{group_id}"
    if cache_key in GROUP_MEMBERSHIP_CACHE:
        cached_result, timestamp = GROUP_MEMBERSHIP_CACHE[cache_key]
        # Check if cache is still valid
        if time.time() - timestamp < GROUP_MEMBERSHIP_CACHE_TTL:
            return cached_result
    
    try:
        # Get Directory API service
        service = get_directory_service()
        if not service:
            logger.error("Failed to create directory service")
            return False
        
        # Check direct membership first (faster)
        try:
            member = service.members().get(groupKey=group_id, memberKey=email).execute()
            # If we get here, the user is a member
            GROUP_MEMBERSHIP_CACHE[cache_key] = (True, time.time())
            return True
        except HttpError as e:
            if e.status_code == 404:
                # Member not found, continue to check nested groups
                pass
            elif e.status_code == 401 or e.status_code == 403:
                # Not authorized - likely an issue with service account permissions
                logger.error(f"Service account permission error: {e}")
                return False
            else:
                logger.error(f"Error checking direct group membership: {e}")
                return False
        
        # Check membership through nested groups (slower)
        try:
            # List all members of the group
            request = service.members().list(groupKey=group_id, includeDerivedMembership=True)
            members = []
            
            # Handle pagination
            while request is not None:
                response = request.execute()
                current_members = response.get('members', [])
                members.extend(current_members)
                
                # Get the next page of results
                request = service.members().list_next(request, response)
            
            # Check if user's email is in the list
            is_member = any(
                member.get('email', '').lower() == email.lower() 
                for member in members
            )
            
            # Cache the result
            GROUP_MEMBERSHIP_CACHE[cache_key] = (is_member, time.time())
            return is_member
            
        except HttpError as e:
            # Handle authorization errors
            if e.status_code == 401 or e.status_code == 403:
                logger.error(f"Service account permission error: {e}")
                return False
            else:
                logger.error(f"Error checking group membership: {e}")
                return False
            
    except Exception as e:
        logger.error(f"Unexpected error checking group membership: {e}")
        return False

def require_group_membership(group_id: str = REGNUM_ADMIN_GROUP):
    """
    Decorator function to require group membership for specific Streamlit pages.
    
    Usage:
        @require_group_membership()
        def my_streamlit_page():
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
                st.stop()
            
            # Check if user is a member of the required group
            user_email = st.session_state.user_email
            if not is_group_member(user_email, group_id):
                # Use a more user-friendly error message
                friendly_group_name = "regnum-site" if group_id == REGNUM_ADMIN_GROUP else group_id
                st.error(f"Access denied: You must be a member of the '{friendly_group_name}' group to access this page.")
                
                # Add a helpful message about how to get access
                st.warning("If you need access to this page, please contact webminister@westkingdom.org to be added to the appropriate group.")
                st.stop()
            
            # If we get here, user has permission, so run the function
            return func(*args, **kwargs)
        return wrapper
    return decorator 