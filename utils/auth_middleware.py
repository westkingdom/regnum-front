import streamlit as st
from functools import wraps
import time
from google.oauth2 import id_token
import google.auth.transport.requests
from utils.logger import app_logger as logger
import requests
import os
from utils.config import REGNUM_ADMIN_GROUP, BYPASS_GROUP_CHECK
from utils.auth import get_directory_service, is_group_member

def verify_organization(idinfo):
    """
    Checks if the authenticated user belongs to the 'westkingdom.org' domain.
    
    Args:
        idinfo: The dictionary containing the user's ID token information
        
    Returns:
        True if the 'hd' claim in the token matches 'westkingdom.org', False otherwise
    """
    return idinfo.get('hd') == 'westkingdom.org'

def check_user_domain(email):
    """
    Checks if an email belongs to the westkingdom.org domain.
    Simple string check, no API calls needed.
    
    Args:
        email: Email address to check
        
    Returns:
        True if the email ends with @westkingdom.org, False otherwise
    """
    if not email:
        return False
    return email.lower().endswith('@westkingdom.org')

def check_group_membership(email, group_name="regnum-site"):
    """
    Checks if a user is a member of a specific Google Group.
    
    Args:
        email: The email address of the user to check
        group_name: The Google Group name to check membership for (default: regnum-site)
        
    Returns:
        True if the user is a member of the specified group, False otherwise
    """
    try:
        logger.info(f"Checking if {email} is a member of {group_name} group")
        
        # If the group is "regnum-site", use the direct ID from config
        if group_name == "regnum-site":
            # Use the is_group_member function that takes an ID directly
            return is_group_member(email, REGNUM_ADMIN_GROUP)
        
        # For other groups, use the existing name-based logic
        from utils.queries import get_all_groups
        
        # Get the group ID from the name
        _, group_name_to_id = get_all_groups()
        
        # If the group name doesn't exist in our mapping, we can't check membership
        if group_name not in group_name_to_id:
            logger.warning(f"Group {group_name} not found in group mapping")
            return False
            
        group_id = group_name_to_id[group_name]
        
        # Use the auth module's is_group_member function
        return is_group_member(email, group_id)
    except Exception as e:
        logger.error(f"Error checking group membership: {str(e)}")
        return False

def require_auth(flow_provider):
    """
    Authentication middleware decorator that requires valid Google OAuth authentication.
    
    Args:
        flow_provider: Function that returns the configured OAuth flow
    
    Returns:
        A decorator function that checks authentication status
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check if we should bypass authentication entirely
            if os.environ.get('BYPASS_AUTH', 'false').lower() == 'true':
                logger.info("Authentication bypassed due to BYPASS_AUTH=true")
                if 'user_email' not in st.session_state:
                    st.session_state['user_email'] = 'authenticated@westkingdom.org'
                return func(*args, **kwargs)
            
            # Check if user is already authenticated
            if 'credentials' not in st.session_state or 'user_email' not in st.session_state:
                st.error("Authentication required. Please return to the home page to log in.")
                st.info("You need to authenticate with your @westkingdom.org Google account to access this page.")
                
                # Provide a link back to home
                if st.button("Go to Login Page"):
                    st.switch_page("Home.py")
                
                st.stop()
            
            # Verify the credentials are still valid
            try:
                credentials = st.session_state['credentials']
                request = google.auth.transport.requests.Request()
                
                # Verify the ID token
                id_info = id_token.verify_oauth2_token(
                    credentials.id_token, request, credentials.client_id
                )
                
                # Check if token is expired
                current_time = time.time()
                if id_info.get('exp', 0) < current_time:
                    logger.warning("Token expired, clearing session")
                    del st.session_state['credentials']
                    del st.session_state['user_email']
                    st.error("Your session has expired. Please log in again.")
                    st.rerun()
                
                # Verify organization
                if not verify_organization(id_info):
                    st.error("Access denied. You must use a @westkingdom.org account.")
                    st.stop()
                
                # Update user email in session state
                st.session_state['user_email'] = id_info.get('email')
                
            except Exception as e:
                logger.error(f"Error verifying credentials: {str(e)}")
                # Clear invalid credentials
                if 'credentials' in st.session_state:
                    del st.session_state['credentials']
                if 'user_email' in st.session_state:
                    del st.session_state['user_email']
                st.error("Authentication error. Please log in again.")
                st.rerun()
            
            # Call the wrapped function
            return func(*args, **kwargs)
        return wrapper
    return decorator

def require_group_auth(flow_provider, group_name=None, message=None):
    """
    Group authentication middleware decorator that requires both authentication and group membership.
    
    Args:
        flow_provider: Function that returns the configured OAuth flow
        group_name: Name of the required group (defaults to "regnum-site")
        message: Custom message to display on access denial
    
    Returns:
        A decorator function that checks authentication and group membership
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # First, ensure basic authentication
            auth_decorator = require_auth(flow_provider)
            auth_wrapper = auth_decorator(lambda: None)
            
            try:
                auth_wrapper()  # This will handle authentication or stop execution
            except:
                return  # Authentication failed, stop here
            
            # Check if we should bypass group checks
            if BYPASS_GROUP_CHECK:
                logger.info("Group authentication bypassed due to BYPASS_GROUP_CHECK=true")
                st.session_state['is_admin'] = True
                return func(*args, **kwargs)
            
            # Now check group membership
            user_email = st.session_state.get('user_email')
            if not user_email:
                st.error("No user email found in session. Please log in again.")
                st.stop()
            
            # Determine which group to check
            target_group = group_name or "regnum-site"
            
            # Check group membership
            if not check_group_membership(user_email, target_group):
                # Display custom message or default
                if message:
                    st.error(message)
                else:
                    st.error(f"Access denied: You must be a member of the '{target_group}' group to access this page.")
                
                st.warning("If you need access to this page, please contact webminister@westkingdom.org to be added to the appropriate group.")
                
                # Show current user info for debugging
                st.info(f"Current user: {user_email}")
                
                # Add debug information if in development
                if os.environ.get('STREAMLIT_ENV') == 'development':
                    st.info(f"Debug: Checking membership for {user_email} in group {target_group}")
                    
                    # Add a temporary bypass for development
                    if st.button("🚨 Development Bypass (DO NOT USE IN PRODUCTION)"):
                        st.session_state['is_admin'] = True
                        st.warning("Group check bypassed for development. This should not be available in production!")
                        st.rerun()
                
                st.stop()
            
            # User has proper group membership
            st.session_state['is_admin'] = True
            logger.info(f"User {user_email} has access to {target_group} group")
            
            # Call the wrapped function
            return func(*args, **kwargs)
        return wrapper
    return decorator

def service_account_auth(func):
    """
    Legacy authentication middleware - kept for backward compatibility.
    Now redirects to proper OAuth flow.
    
    Args:
        func: The function to decorate
    
    Returns:
        A decorated function that ensures proper authentication
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.warning("service_account_auth is deprecated. Please use require_auth instead.")
        
        # Check if user is authenticated via OAuth
        if 'credentials' not in st.session_state or 'user_email' not in st.session_state:
            st.error("Authentication required. Please return to the home page to log in with Google.")
            st.info("This page requires Google OAuth authentication with your @westkingdom.org account.")
            
            if st.button("Go to Login Page"):
                st.switch_page("Home.py")
            
            st.stop()
        
        # User is authenticated, proceed
        return func(*args, **kwargs)
    
    return wrapper