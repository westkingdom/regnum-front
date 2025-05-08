import streamlit as st
from functools import wraps
import time
from google.oauth2 import id_token
import google.auth.transport.requests
from utils.logger import app_logger as logger
import requests
import os

def verify_organization(idinfo):
    """
    Checks if the authenticated user belongs to the 'westkingdom.org' domain.
    
    Args:
        idinfo: The dictionary containing the user's ID token information
        
    Returns:
        True if the 'hd' claim in the token matches 'westkingdom.org', False otherwise
    """
    return idinfo.get('hd') == 'westkingdom.org'

def check_group_membership(email, group_name="regnum-site"):
    """
    Checks if a user is a member of a specific Google Group.
    
    Args:
        email: The email address of the user to check
        group_name: The Google Group name to check membership for (default: regnum-site)
        
    Returns:
        True if the user is a member of the specified group, False otherwise
    """
    from utils.queries import get_group_members, get_all_groups
    
    try:
        logger.info(f"Checking if {email} is a member of {group_name} group")
        
        # Get the group ID from the name
        _, group_name_to_id = get_all_groups()
        
        # If the group name doesn't exist in our mapping, we can't check membership
        if group_name not in group_name_to_id:
            logger.warning(f"Group {group_name} not found in group mapping")
            return False
            
        group_id = group_name_to_id[group_name]
        
        # Get members of the group
        response = get_group_members(group_id)
        
        if not response or 'members' not in response:
            logger.warning(f"Failed to get members for group {group_name} (ID: {group_id})")
            return False
            
        members = response.get('members', [])
        
        # Check if the user's email is in the members list
        for member in members:
            if member.get('email', '').lower() == email.lower():
                logger.info(f"User {email} is a member of {group_name} group")
                return True
                
        logger.info(f"User {email} is NOT a member of {group_name} group")
        return False
    except Exception as e:
        logger.error(f"Error checking group membership: {str(e)}")
        return False

def require_auth(flow_provider):
    """
    Authentication middleware decorator that ensures users are logged in.
    
    Args:
        flow_provider: A function that returns the OAuth flow object
    
    Returns:
        A decorator function that checks authentication status
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if 'credentials' not in st.session_state:
                logger.info("User not authenticated, redirecting to login")
                st.error("Please login to access this page")
                try:
                    flow = flow_provider()
                    auth_url, _ = flow.authorization_url(prompt='consent')
                    st.markdown(f'<a href="{auth_url}" target="_self">Login with Google</a>', unsafe_allow_html=True)
                except Exception as e:
                    logger.error(f"Error generating authorization URL: {str(e)}")
                    st.error(f"Error generating authorization URL: {e}")
                st.stop()
            else:
                # Verify the token is still valid
                credentials = st.session_state['credentials']
                request = google.auth.transport.requests.Request()
                
                try:
                    id_info = id_token.verify_oauth2_token(
                        credentials.id_token, request, credentials.client_id
                    )
                    
                    # Check if token is expired
                    if 'exp' in id_info and time.time() > id_info['exp']:
                        logger.warning("Token expired, redirecting to login")
                        del st.session_state['credentials']
                        st.rerun()
                        
                    # Verify organization
                    if not verify_organization(id_info):
                        logger.warning(f"Access denied for non-WK user: {id_info.get('email', 'unknown')}")
                        st.error("Access denied. User does not belong to westkingdom.org")
                        del st.session_state['credentials']
                        st.rerun()
                    
                    # Token is valid, let the function run
                    logger.debug(f"Authenticated access to {func.__name__} by {id_info.get('email', 'unknown')}")
                    
                except ValueError as e:
                    logger.warning(f"Token validation error: {str(e)}")
                    del st.session_state['credentials']
                    st.rerun()
                except Exception as e:
                    logger.error(f"Authentication error: {str(e)}")
                    st.error(f"Authentication error: {e}")
                    st.stop()
                    
            return func(*args, **kwargs)
        return wrapper
    return decorator

def require_group_auth(flow_provider, group_name="Regnum", message="Sorry, you are not allowed to view these pages. If you are looking to take on a new duty, click on Duty Request in the left menu."):
    """
    Authentication middleware decorator that ensures users are logged in AND members of a specific group.
    
    Args:
        flow_provider: A function that returns the OAuth flow object
        group_name: The Google Group name to check membership for (default: Regnum)
        message: The message to display if the user is not a member of the group
        
    Returns:
        A decorator function that checks authentication status and group membership
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if 'credentials' not in st.session_state:
                logger.info("User not authenticated, redirecting to login")
                st.error("Please login to access this page")
                try:
                    flow = flow_provider()
                    auth_url, _ = flow.authorization_url(prompt='consent')
                    st.markdown(f'<a href="{auth_url}" target="_self">Login with Google</a>', unsafe_allow_html=True)
                except Exception as e:
                    logger.error(f"Error generating authorization URL: {str(e)}")
                    st.error(f"Error generating authorization URL: {e}")
                st.stop()
            else:
                # Verify the token is still valid
                credentials = st.session_state['credentials']
                request = google.auth.transport.requests.Request()
                
                try:
                    id_info = id_token.verify_oauth2_token(
                        credentials.id_token, request, credentials.client_id
                    )
                    
                    # Check if token is expired
                    if 'exp' in id_info and time.time() > id_info['exp']:
                        logger.warning("Token expired, redirecting to login")
                        del st.session_state['credentials']
                        st.rerun()
                        
                    # Verify organization
                    if not verify_organization(id_info):
                        logger.warning(f"Access denied for non-WK user: {id_info.get('email', 'unknown')}")
                        st.error("Access denied. User does not belong to westkingdom.org")
                        del st.session_state['credentials']
                        st.rerun()
                    
                    # Check group membership
                    user_email = id_info.get('email', '')
                    if not check_group_membership(user_email, group_name):
                        logger.warning(f"Access denied for user {user_email}: Not a member of {group_name} group")
                        st.error(message)
                        # Link to Duty Request page
                        st.markdown('<a href="/Duty_Request" target="_self">Go to Duty Request</a>', unsafe_allow_html=True)
                        st.stop()
                    
                    # User is authenticated and has group membership, let the function run
                    logger.debug(f"Authenticated access to {func.__name__} by {user_email} (member of {group_name})")
                    
                except ValueError as e:
                    logger.warning(f"Token validation error: {str(e)}")
                    del st.session_state['credentials']
                    st.rerun()
                except Exception as e:
                    logger.error(f"Authentication error: {str(e)}")
                    st.error(f"Authentication error: {e}")
                    st.stop()
                    
            return func(*args, **kwargs)
        return wrapper
    return decorator