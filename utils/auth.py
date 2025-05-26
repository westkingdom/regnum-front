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
            logger.info(f"🔌 Building directory service with user credentials")
            # Check if the required scope is available
            required_scope = 'https://www.googleapis.com/auth/admin.directory.group.member.readonly'
            if hasattr(credentials, 'scopes') and required_scope in credentials.scopes:
                logger.info(f"✅ User credentials have required scope")
                return build('admin', 'directory_v1', credentials=credentials)
            else:
                logger.warning(f"⚠️ User credentials missing required scope: {required_scope}")
                # Fall back to service account if user creds lack proper scope
                logger.info(f"🔄 Falling back to service account")
        
        # Use service account with domain-wide delegation
        import os
        # Try Cloud Run path first, then local development path
        sa_file = SERVICE_ACCOUNT_FILE if os.path.exists(SERVICE_ACCOUNT_FILE) else LOCAL_SERVICE_ACCOUNT_FILE
        
        logger.info(f"🔑 Looking for service account file at: {sa_file}")
        logger.info(f"🔑 Cloud Run path exists: {os.path.exists(SERVICE_ACCOUNT_FILE)}")
        logger.info(f"🔑 Local path exists: {os.path.exists(LOCAL_SERVICE_ACCOUNT_FILE)}")
        
        if not os.path.exists(sa_file):
            logger.error(f"❌ Service account file not found at {sa_file}")
            # Check volumes
            try:
                if os.path.exists('/secrets'):
                    logger.info(f"📁 Contents of /secrets directory:")
                    for root, dirs, files in os.walk('/secrets'):
                        for file in files:
                            logger.info(f"  - {os.path.join(root, file)}")
                else:
                    logger.warning(f"⚠️ /secrets directory does not exist")
            except Exception as e:
                logger.error(f"❌ Error checking /secrets directory: {e}")
            return None
            
        # Create service account credentials with domain-wide delegation
        scopes = [
            'https://www.googleapis.com/auth/admin.directory.group.readonly',
            'https://www.googleapis.com/auth/admin.directory.group.member.readonly',
            'https://www.googleapis.com/auth/admin.directory.user.readonly'
        ]
        
        logger.info(f"🔑 Loading service account from: {sa_file}")
        
        try:
            # Check if file is readable
            with open(sa_file, 'r') as f:
                # Just read a few characters to check access
                content_start = f.read(10)
                logger.info(f"✅ Service account file is readable")
        except Exception as e:
            logger.error(f"❌ Error reading service account file: {e}")
            return None
        
        try:
            sa_credentials = service_account.Credentials.from_service_account_file(
                sa_file, 
                scopes=scopes,
                subject=impersonate_user  # Impersonate an admin
            )
            logger.info(f"✅ Service account credentials created successfully")
        except Exception as e:
            logger.error(f"❌ Error creating service account credentials: {e}")
            return None
        
        # Build and return the service
        logger.info(f"🔌 Building directory service with service account impersonating {impersonate_user}")
        directory_service = build('admin', 'directory_v1', credentials=sa_credentials)
        logger.info(f"✅ Directory service created successfully")
        return directory_service
    
    except Exception as e:
        logger.error(f"❌ Error creating directory service: {e}")
        import traceback
        logger.error(f"❌ Stack trace: {traceback.format_exc()}")
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
    # Start with detailed logging to help diagnose issues
    logger.info(f"🔍 Checking if {email} is a member of group {group_id}")
    
    # Check for bypass environment variable for development/testing
    bypass_check = os.environ.get('BYPASS_GROUP_CHECK', '').lower() == 'true'
    if bypass_check:
        # In bypass mode, automatically grant access to @westkingdom.org emails
        logger.info(f"📢 BYPASS_GROUP_CHECK is enabled in environment: {os.environ.get('BYPASS_GROUP_CHECK', 'not set')}")
        if email and email.lower().endswith('@westkingdom.org'):
            logger.warning(f"⚠️ BYPASS_GROUP_CHECK enabled: Auto-approving {email} for group {group_id}")
            return True
    else:
        logger.info(f"📢 BYPASS_GROUP_CHECK is disabled or not set: {os.environ.get('BYPASS_GROUP_CHECK', 'not set')}")
    
    if not email or not group_id:
        logger.warning(f"❌ Missing email or group_id: email={email}, group_id={group_id}")
        return False
    
    # Normalize email addresses for comparison
    email = email.lower().strip()
    group_id = group_id.lower().strip()
    logger.info(f"🔄 Normalized values: email={email}, group_id={group_id}")
    
    # Check cache first
    cache_key = f"{email}:{group_id}"
    if cache_key in GROUP_MEMBERSHIP_CACHE:
        cached_result, timestamp = GROUP_MEMBERSHIP_CACHE[cache_key]
        # Check if cache is still valid
        if time.time() - timestamp < GROUP_MEMBERSHIP_CACHE_TTL:
            logger.info(f"📋 Using cached result for {email}:{group_id} = {cached_result}")
            return cached_result
        else:
            logger.info(f"📋 Cache expired for {email}:{group_id}, will check again")
    
    try:
        # Get Directory API service
        logger.info(f"🔌 Getting Directory API service")
        service = get_directory_service()
        if not service:
            logger.error("❌ Failed to create directory service - check service account permissions")
            return False
        logger.info(f"✅ Directory API service created successfully")
        
        # Check direct membership first (faster)
        try:
            logger.info(f"🔍 Checking direct membership for {email} in group {group_id}")
            member = service.members().get(groupKey=group_id, memberKey=email).execute()
            # If we get here, the user is a member
            logger.info(f"✅ User {email} is a direct member of group {group_id}")
            GROUP_MEMBERSHIP_CACHE[cache_key] = (True, time.time())
            return True
        except HttpError as e:
            if e.status_code == 404:
                logger.info(f"ℹ️ User {email} is not a direct member of group {group_id}, checking nested groups")
                # Member not found, continue to check nested groups
                pass
            elif e.status_code == 401 or e.status_code == 403:
                # Not authorized - likely an issue with service account permissions
                logger.error(f"❌ Service account permission error: {e}")
                logger.error(f"❌ Make sure service account has domain-wide delegation and correct scopes")
                return False
            else:
                logger.error(f"❌ Error checking direct group membership: {e}")
                return False
        
        # Check membership through nested groups (slower)
        try:
            # List all members of the group
            logger.info(f"🔍 Checking all members and nested groups for {group_id}")
            request = service.members().list(groupKey=group_id, includeDerivedMembership=True)
            members = []
            
            # Handle pagination
            while request is not None:
                logger.info(f"📄 Fetching page of group members")
                response = request.execute()
                current_members = response.get('members', [])
                
                if not current_members:
                    logger.warning(f"⚠️ No members found in group {group_id} or response missing 'members' key")
                else:
                    logger.info(f"ℹ️ Found {len(current_members)} members in this page")
                
                members.extend(current_members)
                
                # Get the next page of results
                request = service.members().list_next(request, response)
                if request:
                    logger.info("📄 More pages of members available, continuing...")
            
            # Check if user's email is in the list
            logger.info(f"🔍 Checking if {email} is in the member list of size {len(members)}")
            
            # For debugging, log a few member emails
            if members and len(members) > 0:
                sample_size = min(5, len(members))
                sample_members = [member.get('email', 'unknown') for member in members[:sample_size]]
                logger.info(f"📋 Sample of members (first {sample_size}): {', '.join(sample_members)}")
            
            is_member = any(
                member.get('email', '').lower() == email.lower() 
                for member in members
            )
            
            # Cache the result
            GROUP_MEMBERSHIP_CACHE[cache_key] = (is_member, time.time())
            
            if is_member:
                logger.info(f"✅ User {email} found in members list of group {group_id}")
            else:
                logger.warning(f"❌ User {email} NOT found in members list of group {group_id}")
                
            return is_member
            
        except HttpError as e:
            # Handle authorization errors
            if e.status_code == 401 or e.status_code == 403:
                logger.error(f"❌ Service account permission error listing members: {e}")
                return False
            else:
                logger.error(f"❌ Error checking group membership: {e}")
                return False
            
    except Exception as e:
        logger.error(f"❌ Unexpected error checking group membership: {e}")
        # Log the stack trace for debugging
        import traceback
        logger.error(f"❌ Stack trace: {traceback.format_exc()}")
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