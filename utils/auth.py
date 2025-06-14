import logging
from typing import Dict, Any, Optional, List
import streamlit as st
import os
from utils.logger import app_logger as logger

# Configure logging
logger = logging.getLogger(__name__)

def get_directory_service():
    """
    Legacy function - now returns None as no directory service is needed for public access.
    
    Returns:
        None (no service needed for public access)
    """
    logger.info("Directory API service not needed for public access")
    return None

def is_group_member(email, group_id):
    """
    Legacy function - now always returns True for public access.
    
    Args:
        email: User email address to check (unused)
        group_id: Google Group ID or email address (unused)
        
    Returns:
        True (always grants access for public use)
    """
    logger.info(f"Public access granted for group membership check: {email} in group {group_id}")
    return True

def require_group_membership(group_id: str = None):
    """
    Decorator function - now grants public access to all users.
    
    Usage:
        @require_group_membership()
        def my_app_page():
            st.title("Public Page")
            # Rest of your page
    
    Args:
        group_id: The email address of the required Google Group (unused)
        
    Returns:
        Function that grants access to all users
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.info("Public access granted - group membership check bypassed")
            
            # Ensure session state is initialized for public access
            if 'user_email' not in st.session_state:
                st.session_state['user_email'] = 'public@westkingdom.org'
                st.session_state['user_name'] = 'Public User'
                st.session_state['is_admin'] = True
            
            # Grant access to all users
            return func(*args, **kwargs)
        return wrapper
    return decorator 