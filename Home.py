import streamlit as st
import google.auth
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
import google.auth.transport.requests
import os
import json
import datetime
from typing import Dict, Any # Import typing
from googleapiclient.discovery import build
from utils.logger import app_logger as logger
from utils.auth import is_group_member
from utils.config import REGNUM_ADMIN_GROUP

# Define the path where the secret is mounted
SECRET_CREDENTIALS_PATH = '/oauth/google_credentials.json' # Updated path
# Fallback for local development (optional)
LOCAL_CREDENTIALS_PATH = 'utils/google_credentials.json' # Local fallback remains the same

# Determine the correct path
credentials_path = SECRET_CREDENTIALS_PATH if os.path.exists(SECRET_CREDENTIALS_PATH) else LOCAL_CREDENTIALS_PATH

# Load client secrets and configure flow
try:
    flow = Flow.from_client_secrets_file(
        credentials_path,
        scopes=[
            'openid', 
            'https://www.googleapis.com/auth/userinfo.email', 
            'https://www.googleapis.com/auth/userinfo.profile',
            'https://www.googleapis.com/auth/admin.directory.group.member.readonly'  # Add Directory API scope
        ],
        redirect_uri=os.environ.get('REDIRECT_URI', 'https://regnum.westkingdom.org')
    )
    logger.info("OAuth flow configured successfully")
except FileNotFoundError:
    logger.error(f"OAuth credentials file not found at {credentials_path}")
    st.error(f"OAuth Credentials file not found at {credentials_path}. Ensure the secret is mounted correctly or the local file exists.")
    st.stop()
except Exception as e:
    logger.error(f"Error loading OAuth credentials: {str(e)}")
    st.error(f"Error loading OAuth credentials: {e}")
    st.stop()


def verify_organization(idinfo: Dict[str, Any]) -> bool:
    """
    Checks if the authenticated user belongs to the 'westkingdom.org' domain.

    Args:
        idinfo: The dictionary containing the user's ID token information,
                typically obtained from `id_token.verify_oauth2_token`.

    Returns:
        True if the 'hd' (hosted domain) claim in the token matches 'westkingdom.org',
        False otherwise.
    """
    return idinfo.get('hd') == 'westkingdom.org'


def is_member_of_group(email: str, group_id: str = '00kgcv8k1r9idky', credentials=None) -> bool:
    """
    Checks if the user is a member of the specified Google Group.
    
    Args:
        email: The user's email address to check
        group_id: The Google Group email address
        credentials: OAuth credentials with appropriate scopes
        
    Returns:
        True if the user is a member of the group, False otherwise
    """
    try:
        # Need Directory API scope for this to work
        # 'https://www.googleapis.com/auth/admin.directory.group.member.readonly'
        service = build('admin', 'directory_v1', credentials=credentials)
        
        # List all members of the group
        results = service.members().list(groupKey=group_id).execute()
        members = results.get('members', [])
        
        # Check if user's email is in the group
        return any(member.get('email', '').lower() == email.lower() for member in members)
    except Exception as e:
        print(f"ERROR: Failed to check group membership: {e}")
        # Default to deny on error
        return False


# --- Streamlit App Logic ---
st.set_page_config(page_title="Regnum Home") # Set a page title
st.title("West Kingdom Regnum Portal") # Updated title

# --- Authentication Flow ---

# 1. Handle OAuth Callback
# Check if 'code' is in query params (meaning user is returning from Google Auth)
# and if we don't already have credentials stored in the session state.
query_params = st.query_params
if 'code' in query_params and 'credentials' not in st.session_state:
    try:
        logger.info("OAuth code received, attempting to fetch token")
        flow.fetch_token(code=query_params['code'])
        st.session_state['credentials'] = flow.credentials
        logger.info("Token fetched successfully, storing credentials in session state")
        # Clear query params after fetching token to prevent re-processing
        st.query_params.clear()
        st.rerun() # Rerun to process the newly logged-in state immediately
    except Exception as e:
        logger.error(f"Error fetching OAuth token: {str(e)}")
        st.error(f"Error fetching OAuth token: {e}")

# 2. Check if User is Authenticated (has credentials in session)
if 'credentials' not in st.session_state:
    # User is not logged in, display login link
    try:
        auth_url, _ = flow.authorization_url(
            prompt='consent', # Force prompt for account selection/consent
            # access_type='offline' # Optional: If you need refresh tokens
            )
        logger.info("User not authenticated, displaying login link")
        st.markdown(f"""
        <div style="display: flex; justify-content: center; align-items: center; height: 50vh;">
            <a href="{auth_url}" target="_self" style="padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px; font-size: 1.2em;">
                Login with Google (West Kingdom Account)
            </a>
        </div>
        """, unsafe_allow_html=True)
        st.info("You must log in with your @westkingdom.org Google account to access this application.")
    except Exception as e:
        logger.error(f"Error generating authorization URL: {str(e)}")
        st.error(f"Error generating authorization URL: {e}")

else:
    # User is logged in, verify token and organization
    credentials = st.session_state['credentials']
    request_session = google.auth.transport.requests.Request()

    try:
        logger.info("Verifying ID token")
        id_info = id_token.verify_oauth2_token(
            credentials.id_token, request_session, credentials.client_id
        )
        user_email = id_info.get('email', 'unknown')
        logger.info(f"Token verified for user: {user_email}")

        # Store email in session state for use in other pages
        st.session_state['user_email'] = user_email
        
        # Verify organization
        if verify_organization(id_info):
            # Check if user is member of regnum-site group
            is_admin = is_group_member(user_email, REGNUM_ADMIN_GROUP)
            st.session_state['is_admin'] = is_admin
            
            # Display welcome message
            st.success(f"Welcome {id_info.get('name')} ({user_email})")
            
            # Show admin status
            if is_admin:
                st.success("✅ You have admin access (member of regnum-site group)")
            else:
                st.warning("⚠️ You have basic access (not a member of regnum-site group)")
                
            # --- Main Application Content (for authenticated users) ---
            st.markdown("---")
            st.header("Application Links")
            st.page_link("pages/1_Groups.py", label="Manage Groups and Members", icon="👥")
            st.page_link("pages/2_Regnum.py", label="Regnum Data Entry", icon="📝")
            st.page_link("pages/5_Duty_Request.py", label="Request New Duty/Job", icon="✅")
            # Add more links or content here

            st.markdown("---")
            if st.button("Logout"):
                print(f"DEBUG: User {user_email} logging out.")
                del st.session_state['credentials']
                if 'user_email' in st.session_state:
                    del st.session_state['user_email']
                if 'is_admin' in st.session_state:
                    del st.session_state['is_admin']
                st.query_params.clear() # Clear params on logout as well
                st.rerun()
        else:
            # User belongs to wrong organization
            logger.warning(f"Access denied for non-WK user: {user_email}")
            st.error(f"Access Denied: User {user_email} does not belong to the required 'westkingdom.org' organization.")
            if st.button("Logout"):
                del st.session_state['credentials']
                st.query_params.clear()
                st.rerun()

    except ValueError as e:
        # Token expired or invalid signature/audience etc.
        logger.warning(f"ID token verification failed: {str(e)}")
        st.warning(f"Session expired or invalid: {e}. Please login again.")
        # Clear credentials to force re-login
        if 'credentials' in st.session_state:
            del st.session_state['credentials']
        st.query_params.clear()
        st.rerun() # Rerun to show login link again
    except Exception as e:
        # Catch-all for other verification errors
        logger.error(f"Error verifying token: {str(e)}")
        st.error(f"An error occurred during authentication verification: {e}")
        if st.button("Logout"):
            del st.session_state['credentials']
            st.query_params.clear()
            st.rerun() 

# Create a simple health check endpoint using Streamlit's routing
def health_check():
    """
    Provides a simple health check page accessible at /health.
    
    This needs to be accessed directly as a page, not through the FastAPI layer.
    For proper load balancer health checks, configure the health check URL to point to this.
    """
    logger.debug("Health check accessed")
    if st.query_params.get('check') == 'health':
        st.json({"status": "healthy", "timestamp": str(datetime.datetime.now())})
        st.stop()

# Call health check at the start of the app
health_check()