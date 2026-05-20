import streamlit as st
from functools import wraps
from utils.google_oauth import require_authentication, logout_user, is_authenticated, get_current_user


def protected_page(func):
    """Decorator for pages that require Google OAuth authentication."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = require_authentication()

        with st.sidebar:
            st.markdown("---")
            st.markdown("**Signed in as:**")
            st.markdown(f"👤 {user['name']}")
            st.markdown(f"📧 {user['email']}")
            if st.button("🚪 Sign Out", use_container_width=True):
                logout_user()
                st.rerun()

        return func(user, *args, **kwargs)

    return wrapper


def public_page(func):
    """Decorator for public pages — shows sign-in/out status in sidebar."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if is_authenticated():
            user = get_current_user()
            with st.sidebar:
                st.success(f"Signed in as: {user['name']}")
                if st.button("🏠 Go to Dashboard"):
                    st.switch_page("Home.py")
                if st.button("🚪 Sign Out"):
                    logout_user()
                    st.rerun()
        else:
            with st.sidebar:
                st.info("You are accessing this page as a guest")
                if st.button("🔐 Sign In"):
                    st.switch_page("pages/0_Login.py")

        return func(*args, **kwargs)

    return wrapper
