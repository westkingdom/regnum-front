import streamlit as st
import os
from utils.logger import app_logger as logger
from utils.jwt_auth import require_authentication, logout_user, is_authenticated

# --- Page Configuration ---
st.set_page_config(page_title="WKRegnum - West Kingdom Regnum Portal")

# --- Authentication Required ---
user = require_authentication()

# --- Main App Logic ---
st.title("WKRegnum - West Kingdom Regnum Portal")

# Display user info and logout button
col1, col2 = st.columns([3, 1])
with col1:
    st.success(f"Welcome, {user['name']} ({user['email']})")
with col2:
    if st.button("Logout"):
        logout_user()
        st.rerun()

logger.info(f"Authenticated access granted to WKRegnum Portal for user: {user['email']}")

# Display welcome message
st.markdown("## Welcome to the West Kingdom Regnum Portal")
st.success("Welcome to the West Kingdom Regnum Portal! This application is now publicly accessible.")

# Main application content
st.markdown("---")
st.markdown("## Application Features")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📋 Available Features")
    st.markdown("""
    - **Regnum Viewer**: Browse the current officer roster
    - **Search**: Find officers by title or branch
    - **Reports**: Generate basic reports
    - **Group Management**: Manage Google Groups
    - **Officer Management**: Add/edit officer information
    - **Email Templates**: Configure email templates
    """)

with col2:
    st.markdown("### 🔧 Administrative Features")
    st.markdown("""
    - **Group Management**: Manage Google Groups
    - **Officer Management**: Add/edit officer information
    - **Email Templates**: Configure email templates
    - **Advanced Reports**: Generate detailed reports
    - **Duty Requests**: Submit duty request forms
    """)

st.markdown("---")
st.markdown("### Navigation")
st.markdown("Use the sidebar menu to navigate between different sections of the application.")

st.markdown("---")
st.markdown("### About WKRegnum")
st.markdown("""
This application provides access to the West Kingdom's officer roster and reporting system. The application is now publicly accessible and provides full functionality to all users.

**Key Features:**
- View current officers and deputies
- Search for officers by title or branch
- Access office email templates
- Generate reports
- Manage group memberships
- Submit duty requests
""")

# Health check endpoint for Cloud Run
def health_check():
    """Return a 200 status for Cloud Run health checks"""
    return {"status": "ok"}

# This is only called by Cloud Run health checks
if os.environ.get('K_SERVICE') and os.environ.get('HEALTH_CHECK') == 'true':
    health_check()