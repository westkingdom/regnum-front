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
    Decorator that enforces JWT authentication before allowing access to a page.

    Usage:
        @require_group_membership()
        def my_app_page():
            st.title("Protected Page")

    Args:
        group_id: Reserved for future group-based authorization (currently unused).
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            from utils.jwt_auth import get_current_user, require_authentication
            user = get_current_user()
            if not user:
                require_authentication()
                return  # require_authentication calls st.stop() internally

            st.session_state['user_email'] = user['email']
            st.session_state['user_name'] = user['name']
            st.session_state['is_admin'] = (user.get('role') == 'admin')
            return func(*args, **kwargs)
        return wrapper
    return decorator