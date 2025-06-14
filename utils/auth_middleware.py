import streamlit as st
from functools import wraps
from utils.logger import app_logger as logger
import os

def verify_organization(idinfo):
    """
    Legacy function - now always returns True for public access.
    """
    return True

def check_user_domain(email):
    """
    Legacy function - now always returns True for public access.
    """
    return True

def check_group_membership(email, group_name="regnum-site"):
    """
    Legacy function - now always returns True for public access.
    """
    logger.info(f"Public access granted for group membership check: {email} in {group_name}")
    return True

def require_auth(flow_provider):
    """
    Authentication middleware decorator - now grants public access to all users.
    
    Args:
        flow_provider: Function that returns the configured OAuth flow (unused)
    
    Returns:
        A decorator function that grants access to all users
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.info("Public access granted - authentication bypassed")
            
            # Ensure session state is initialized for public access
            if 'user_email' not in st.session_state:
                st.session_state['user_email'] = 'public@westkingdom.org'
                st.session_state['user_name'] = 'Public User'
                st.session_state['is_admin'] = True
            
            # Call the wrapped function
            return func(*args, **kwargs)
        return wrapper
    return decorator

def require_group_auth(flow_provider, group_name=None, message=None):
    """
    Group authentication middleware decorator - now grants public access to all users.
    
    Args:
        flow_provider: Function that returns the configured OAuth flow (unused)
        group_name: Name of the required group (unused)
        message: Custom message to display on access denial (unused)
    
    Returns:
        A decorator function that grants access to all users
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.info("Public access granted - group authentication bypassed")
            
            # Ensure session state is initialized for public access
            if 'user_email' not in st.session_state:
                st.session_state['user_email'] = 'public@westkingdom.org'
                st.session_state['user_name'] = 'Public User'
                st.session_state['is_admin'] = True
            
            # Grant admin access to all users
            st.session_state['is_admin'] = True
            
            # Call the wrapped function
            return func(*args, **kwargs)
        return wrapper
    return decorator

def service_account_auth(func):
    """
    Legacy authentication middleware - now grants public access to all users.
    
    Args:
        func: The function to decorate
    
    Returns:
        A decorated function that grants access to all users
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info("Public access granted - service account authentication bypassed")
        
        # Ensure session state is initialized for public access
        if 'user_email' not in st.session_state:
            st.session_state['user_email'] = 'public@westkingdom.org'
            st.session_state['user_name'] = 'Public User'
            st.session_state['is_admin'] = True
        
        # User has public access, proceed
        return func(*args, **kwargs)
    
    return wrapper