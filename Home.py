import streamlit as st
import google.auth
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
import google.auth.transport.requests
import os
import json
from typing import Dict, Any # Import typing

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
        redirect_uri=os.environ.get('REDIRECT_URI', 'https://regnum-front-85382560394.us-west1.run.app') # Use env var or default
    )
except FileNotFoundError:
    st.error(f"OAuth Credentials file not found at {credentials_path}. Ensure the secret is mounted correctly or the local file exists.")
    st.stop()
except Exception as e:
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
        print("DEBUG: OAuth code received, attempting to fetch token...")
        flow.fetch_token(code=query_params['code'])
        st.session_state['credentials'] = flow.credentials
        print("DEBUG: Token fetched successfully, storing credentials in session state.")
        # Clear query params after fetching token to prevent re-processing
        st.query_params.clear()
        st.rerun() # Rerun to process the newly logged-in state immediately
    except Exception as e:
        st.error(f"Error fetching OAuth token: {e}")
        print(f"ERROR: fetching OAuth token: {e}") # Log error

# 2. Check if User is Authenticated (has credentials in session)
if 'credentials' not in st.session_state:
    # User is not logged in, display login link
    try:
        auth_url, _ = flow.authorization_url(
            prompt='consent', # Force prompt for account selection/consent
            # access_type='offline' # Optional: If you need refresh tokens
            )
        print(f"DEBUG: User not authenticated. Displaying login link: {auth_url}")
        st.markdown(f"""
        <div style="display: flex; justify-content: center; align-items: center; height: 50vh;">
            <a href="{auth_url}" target="_self" style="padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px; font-size: 1.2em;">
                Login with Google (West Kingdom Account)
            </a>
        </div>
        """, unsafe_allow_html=True)
        st.info("You must log in with your @westkingdom.org Google account to access this application.")
    except Exception as e:
        st.error(f"Error generating authorization URL: {e}")
        print(f"ERROR: generating auth URL: {e}") # Log error

else:
    # User is logged in, verify token and organization
    credentials = st.session_state['credentials']
    request_session = google.auth.transport.requests.Request()

    try:
        print("DEBUG: Verifying ID token...")
        id_info = id_token.verify_oauth2_token(
            credentials.id_token, request_session, credentials.client_id
        )
        print(f"DEBUG: Token verified for user: {id_info.get('email')}")

        # Verify organization
        if verify_organization(id_info):
            st.success(f"Welcome {id_info.get('name')} ({id_info.get('email')})")
            st.write("You are authenticated.")
            # --- Main Application Content (for authenticated users) ---
            st.markdown("---")
            st.header("Application Links")
            st.page_link("pages/1_Groups.py", label="Manage Groups and Members", icon="👥")
            st.page_link("pages/2_Regnum.py", label="Regnum Data Entry", icon="📝")
            st.page_link("pages/5_Duty_Request.py", label="Request New Duty/Job", icon="✅")
            # Add more links or content here

            st.markdown("---")
            if st.button("Logout"):
                print(f"DEBUG: User {id_info.get('email')} logging out.")
                del st.session_state['credentials']
                st.query_params.clear() # Clear params on logout as well
                st.rerun()
        else:
            # User belongs to wrong organization
            st.error(f"Access Denied: User {id_info.get('email')} does not belong to the required 'westkingdom.org' organization.")
            print(f"WARN: Access denied for non-WK user: {id_info.get('email')}")
            if st.button("Logout"):
                del st.session_state['credentials']
                st.query_params.clear()
                st.rerun()

    except ValueError as e:
        # Token expired or invalid signature/audience etc.
        st.warning(f"Session expired or invalid: {e}. Please login again.")
        print(f"WARN: ID token verification failed: {e}")
        # Clear credentials to force re-login
        if 'credentials' in st.session_state:
            del st.session_state['credentials']
        st.query_params.clear()
        st.rerun() # Rerun to show login link again
    except Exception as e:
        # Catch-all for other verification errors
        st.error(f"An error occurred during authentication verification: {e}")
        print(f"ERROR: Verifying token: {e}")
        if st.button("Logout"):
            del st.session_state['credentials']
            st.query_params.clear()
            st.rerun() 