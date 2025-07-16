import streamlit as st
from functools import wraps
from utils.jwt_auth import require_authentication, logout_user, is_authenticated, get_current_user
from utils.logger import app_logger as logger

def protected_page(func):
    """Decorator to protect pages with JWT authentication"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Require authentication
        user = require_authentication()
        
        # Add logout button to sidebar
        with st.sidebar:
            st.markdown("---")
            st.markdown(f"**Logged in as:**")
            st.markdown(f"👤 {user['name']}")
            st.markdown(f"📧 {user['email']}")
            st.markdown(f"🔑 {user['role'].title()}")
            
            if st.button("🚪 Logout", use_container_width=True):
                logout_user()
                st.rerun()
        
        # Call the original function with user context
        return func(user, *args, **kwargs)
    
    return wrapper

def public_page(func):
    """Decorator for public pages (no authentication required)"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Add info about authentication status
        if is_authenticated():
            user = get_current_user()
            with st.sidebar:
                st.success(f"Logged in as: {user['name']}")
                if st.button("🏠 Go to Dashboard"):
                    st.switch_page("Home.py")
                if st.button("🚪 Logout"):
                    logout_user()
                    st.rerun()
        else:
            with st.sidebar:
                st.info("You are accessing this page as a guest")
                if st.button("🔐 Login"):
                    st.switch_page("pages/0_Login.py")
        
        # Call the original function
        return func(*args, **kwargs)
    
    return wrapper

def admin_required(func):
    """Decorator to require admin role"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = require_authentication()
        
        if user['role'] != 'admin':
            st.error("🚫 Admin Access Required")
            st.info("You need administrator privileges to access this page.")
            st.stop()
        
        return func(user, *args, **kwargs)
    
    return wrapper