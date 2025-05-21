import streamlit as st
import google.auth
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
import google.auth.transport.requests
import os
import json
import datetime
from typing import Dict, Any # Import typing
from utils.logger import app_logger as logger

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
        scopes=['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile'],
        # IMPORTANT: Update redirect_uri for Cloud Run deployment
        # Get the Cloud Run service URL after first deployment and add it as an
        # authorized redirect URI in Google Cloud OAuth Client ID settings.
        redirect_uri=os.environ.get('REDIRECT_URL', 'https://regnum-front-85382560394.us-west1.run.app')
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


# Function to get OAuth flow for auth middleware
def get_flow():
    try:
        flow_obj = Flow.from_client_secrets_file(
            credentials_path,
            scopes=['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile'],
            redirect_uri=os.environ.get('REDIRECT_URL', 'https://regnum-front-85382560394.us-west1.run.app')
        )
        return flow_obj
    except Exception as e:
        logger.error(f"Failed to create OAuth flow: {str(e)}")
        st.error(f"Authentication error: {e}")
        st.stop()

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

# Display explicit warning about needing westkingdom.org account
st.warning("You must be logged in with a @westkingdom.org Google account to access this application.")

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

        # Verify organization
        if verify_organization(id_info):
            logger.info(f"User {user_email} authenticated successfully")
            
            # Check if user is member of regnum-site group for specific pages
            from utils.auth_middleware import check_group_membership
            
            # Display appropriate content based on authentication and group membership
            st.success(f"Welcome {id_info.get('name')} ({user_email})")
            st.write("You are authenticated.")
            # --- Main Application Content (for authenticated users) ---
            st.markdown("---")
            st.header("Application Links")
            
            is_regnum_site_member = check_group_membership(user_email, "regnum-site")
            
            # Always show Duty Request page
            st.page_link("pages/5_Duty_Request.py", label="Request New Duty/Job", icon="✅")
            
            # Only show restricted pages if user is in regnum-site group
            if is_regnum_site_member:
                st.page_link("pages/1_Groups.py", label="Manage Groups and Members", icon="👥")
                st.page_link("pages/2_Regnum.py", label="Regnum Data Entry", icon="📝")
            else:
                st.warning("Note: You don't have access to administration pages. Access to Groups and Regnum pages requires membership in the regnum-site group.")

            st.markdown("---")
            if st.button("Logout"):
                logger.info(f"User {user_email} logging out")
                del st.session_state['credentials']
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