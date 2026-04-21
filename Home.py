import streamlit as st
from utils.jwt_auth import require_authentication, logout_user
from utils.logger import app_logger as logger


def home_content():
    user = require_authentication()

    st.title("WKRegnum - West Kingdom Regnum Portal")

    col1, col2 = st.columns([3, 1])
    with col1:
        st.success(f"Welcome, {user['name']} ({user['email']})")
    with col2:
        if st.button("Logout"):
            logout_user()
            st.rerun()

    logger.info(f"Authenticated access granted to WKRegnum Portal for user: {user['email']}")

    st.markdown("## Welcome to the West Kingdom Regnum Portal")
    st.success("Welcome to the West Kingdom Regnum Portal!")

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
- Generate reports
- Manage group memberships
- Submit duty requests
""")


st.set_page_config(page_title="WKRegnum - West Kingdom Regnum Portal")

pg = st.navigation(
    {
        "Portal": [
            st.Page(home_content, title="Home", default=True),
            st.Page("pages/0_Login.py", title="Login"),
            st.Page("pages/1_Groups.py", title="Groups"),
            st.Page("pages/2_Regnum.py", title="Regnum"),
        ],
        "Forms": [
            st.Page("pages/5_Duty_Request.py", title="Duty Request"),
            st.Page(
                "pages/6_West_Email_Account_Request.py",
                title="West Email Account Request",
                url_path="wk-email",
            ),
        ],
    }
)
pg.run()
