import streamlit as st
import google.auth
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
import google.auth.transport.requests
import os
import json
from utils.logger import app_logger as logger
from utils.auth import is_group_member
from utils.config import REGNUM_ADMIN_GROUP

# --- Page Configuration ---
st.set_page_config(page_title="WKRegnum - West Kingdom Regnum Portal")

# Define the path where the secret is mounted
SECRET_CREDENTIALS_PATH = '/oauth/google_credentials.json'
# Fallback for local development
LOCAL_CREDENTIALS_PATH = 'utils/google_credentials.json'

# Determine the correct path
credentials_path = SECRET_CREDENTIALS_PATH if os.path.exists(SECRET_CREDENTIALS_PATH) else LOCAL_CREDENTIALS_PATH

# Load client secrets and configure OAuth flow
try:
    # Configure the OAuth 2.0 flow using the determined path
    flow = Flow.from_client_secrets_file(
        credentials_path,
        scopes=[
            'openid', 
            'https://www.googleapis.com/auth/userinfo.email', 
            'https://www.googleapis.com/auth/userinfo.profile',
            'https://www.googleapis.com/auth/admin.directory.group.member.readonly'
        ],
        redirect_uri=os.environ.get('REDIRECT_URL', 'https://wkregnum-njxuammdla-uw.a.run.app')
    )
    logger.info("OAuth flow configured successfully")
except FileNotFoundError:
    logger.error(f"Credentials file not found at {credentials_path}")
    st.error(f"Credentials file not found at {credentials_path}. Please ensure the OAuth credentials are properly configured.")
    st.stop()
except Exception as e:
    logger.error(f"Error loading credentials: {str(e)}")
    st.error(f"Error loading credentials: {e}")
    st.stop()

def verify_organization(idinfo):
    """
    Checks if the authenticated user belongs to the 'westkingdom.org' domain.
    
    Args:
        idinfo: The dictionary containing the user's ID token information
        
    Returns:
        True if the 'hd' claim in the token matches 'westkingdom.org', False otherwise
    """
    return idinfo.get('hd') == 'westkingdom.org'

# --- Main App Logic ---
st.title("WKRegnum - West Kingdom Regnum Portal")

# Handle OAuth callback
query_params = st.query_params
if 'code' in query_params and 'credentials' not in st.session_state:
    try:
        logger.info("OAuth code received, attempting to fetch token")
        flow.fetch_token(code=query_params['code'])
        st.session_state['credentials'] = flow.credentials
        logger.info("Token fetched successfully")
        # Clear query params after fetching token
        st.query_params.clear()
        st.rerun()
    except Exception as e:
        logger.error(f"Error fetching OAuth token: {str(e)}")
        st.error(f"Error fetching OAuth token: {e}")

# Check if the user is authenticated
if 'credentials' not in st.session_state:
    # User is not authenticated - show login
    st.markdown("## Welcome to the West Kingdom Regnum Portal")
    st.info("Please authenticate with your @westkingdom.org Google account to access the application.")
    
    try:
        auth_url, _ = flow.authorization_url(prompt='consent')
        logger.info("User not authenticated, displaying login link")
        
        # Create a more prominent login button
        st.markdown("### Authentication Required")
        st.markdown("You must log in with your **@westkingdom.org** Google account to access this application.")
        
        # Use a button-like link for better UX
        st.markdown(f"""
        <div style="text-align: center; margin: 20px 0;">
            <a href="{auth_url}" target="_self" style="
                background-color: #4285f4;
                color: white;
                padding: 12px 24px;
                text-decoration: none;
                border-radius: 4px;
                font-weight: bold;
                display: inline-block;
            ">🔐 Login with Google</a>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### About WKRegnum")
        st.markdown("""
        This application provides access to the West Kingdom's officer roster and reporting system. Here you can:
        
        - View current officers and deputies
        - Search for officers by title or branch
        - Access office email templates
        - Generate reports
        - Manage group memberships (admin only)
        """)
        
    except Exception as e:
        logger.error(f"Error generating authorization URL: {str(e)}")
        st.error(f"Error generating authorization URL: {e}")

else:
    # User has credentials - verify and show authenticated content
    credentials = st.session_state['credentials']
    request = google.auth.transport.requests.Request()

    try:
        logger.info("Verifying ID token")
        id_info = id_token.verify_oauth2_token(
            credentials.id_token, request, credentials.client_id
        )
        
        user_email = id_info.get('email', 'unknown')
        user_name = id_info.get('name', 'Unknown User')
        logger.info(f"Token verified for user: {user_email}")

        # Verify organization
        if verify_organization(id_info):
            logger.info(f"User {user_email} authenticated successfully")
            
            # Store user information in session state
            st.session_state['user_email'] = user_email
            st.session_state['user_name'] = user_name
            
            # Check if user is an admin (member of regnum-site group)
            is_admin = is_group_member(user_email, REGNUM_ADMIN_GROUP)
            st.session_state['is_admin'] = is_admin
            
            # Display welcome message
            st.success(f"Welcome {user_name} ({user_email})")
            
            if is_admin:
                st.info("🔑 You have administrative access to all features.")
            else:
                st.info("👤 You have basic user access. Some features may be restricted.")
            
            # Main application content
            st.markdown("---")
            st.markdown("## Application Features")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📋 Available to All Users")
                st.markdown("""
                - **Regnum Viewer**: Browse the current officer roster
                - **Search**: Find officers by title or branch
                - **Reports**: Generate basic reports
                """)
            
            with col2:
                st.markdown("### 🔧 Administrative Features")
                if is_admin:
                    st.markdown("""
                    - **Group Management**: Manage Google Groups
                    - **Officer Management**: Add/edit officer information
                    - **Email Templates**: Configure email templates
                    - **Advanced Reports**: Generate detailed reports
                    """)
                else:
                    st.markdown("""
                    - *Administrative features require membership*
                    - *in the regnum-site Google Group*
                    - *Contact webminister@westkingdom.org for access*
                    """)
            
            st.markdown("---")
            st.markdown("### Navigation")
            st.markdown("Use the sidebar menu to navigate between different sections of the application.")
            
            # Logout button
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("🚪 Logout", type="secondary"):
                    logger.info(f"User {user_email} logging out")
                    # Clear all session state
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    st.rerun()
                    
        else:
            logger.warning(f"Access denied for non-WK user: {user_email}")
            st.error("Access denied. You must use a @westkingdom.org Google account.")
            st.warning("Only users with @westkingdom.org email addresses can access this application.")
            
            if st.button("🚪 Logout"):
                # Clear credentials and try again
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

    except ValueError as e:
        # Token expired or invalid
        logger.warning(f"ID token verification failed: {str(e)}")
        st.warning(f"Session expired or invalid: {e}. Please login again.")
        
        # Clear invalid credentials
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
        # Show login again
        try:
            auth_url, _ = flow.authorization_url(prompt='consent')
            st.markdown(f'<a href="{auth_url}" target="_self">🔐 Login with Google</a>', unsafe_allow_html=True)
        except Exception as url_e:
            logger.error(f"Error generating re-login URL: {str(url_e)}")
            st.error(f"Error generating re-login URL: {url_e}")
            
    except Exception as e:
        logger.error(f"An error occurred during authentication verification: {str(e)}")
        st.error(f"An error occurred during authentication verification: {e}")
        
        if st.button("🚪 Clear Session and Retry"):
            # Clear all session state and retry
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# Health check endpoint for Cloud Run
def health_check():
    """Return a 200 status for Cloud Run health checks"""
    return {"status": "ok"}

# This is only called by Cloud Run health checks
if os.environ.get('K_SERVICE') and os.environ.get('HEALTH_CHECK') == 'true':
    health_check()