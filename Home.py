import streamlit as st
import google.auth
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from google_auth_oauthlib.flow import InstalledAppFlow
import google.auth.transport.requests
import os
import json
import datetime
from typing import Dict, Any # Import typing
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from utils.logger import app_logger as logger
from utils.auth import is_group_member, get_directory_service
from utils.config import REGNUM_ADMIN_GROUP

# Define the path where the secret is mounted
SECRET_CREDENTIALS_PATH = '/oauth/google_credentials.json' # Updated path
# Fallback for local development (optional)
LOCAL_CREDENTIALS_PATH = 'utils/google_credentials.json' # Local fallback remains the same

# Function to get OAuth flow for auth middleware
def get_flow():
    try:
        # First try to load from the credentials file
        if os.path.exists(SECRET_CREDENTIALS_PATH) or os.path.exists(LOCAL_CREDENTIALS_PATH):
            credentials_path = SECRET_CREDENTIALS_PATH if os.path.exists(SECRET_CREDENTIALS_PATH) else LOCAL_CREDENTIALS_PATH
            logger.info(f"Creating flow from credentials file: {credentials_path}")
            
            flow_obj = Flow.from_client_secrets_file(
                credentials_path,
                scopes=[
                    'openid', 
                    'https://www.googleapis.com/auth/userinfo.email', 
                    'https://www.googleapis.com/auth/userinfo.profile',
                    'https://www.googleapis.com/auth/admin.directory.group.member.readonly'
                ],
                redirect_uri=os.environ.get('REDIRECT_URL', 'https://regnum-front-85382560394.us-west1.run.app')
            )
            return flow_obj
        
        # If no credentials file exists, try to use environment variables
        elif os.environ.get('GOOGLE_CLIENT_ID') and os.environ.get('GOOGLE_CLIENT_SECRET'):
            logger.info("Creating flow from environment variables")
            
            # Create client config dictionary from environment variables
            client_config = {
                "web": {
                    "client_id": os.environ.get('GOOGLE_CLIENT_ID'),
                    "client_secret": os.environ.get('GOOGLE_CLIENT_SECRET'),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "redirect_uris": [os.environ.get('REDIRECT_URL', 'https://regnum-front-85382560394.us-west1.run.app')],
                }
            }
            
            flow_obj = Flow.from_client_config(
                client_config,
                scopes=[
                    'openid', 
                    'https://www.googleapis.com/auth/userinfo.email', 
                    'https://www.googleapis.com/auth/userinfo.profile',
                    'https://www.googleapis.com/auth/admin.directory.group.member.readonly'
                ],
                redirect_uri=os.environ.get('REDIRECT_URL', 'https://regnum-front-85382560394.us-west1.run.app')
            )
            return flow_obj
        else:
            raise ValueError("No OAuth credentials available - either set environment variables GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET or provide a credentials file")
    except Exception as e:
        logger.error(f"Failed to create OAuth flow: {str(e)}")
        st.error(f"Authentication error: {e}")
        st.stop()

# Load client secrets and configure flow
try:
    # Use the same get_flow function for consistency
    flow = get_flow()
    logger.info("OAuth flow configured successfully")
except FileNotFoundError:
    logger.error(f"OAuth credentials not found")
    st.error(f"OAuth Credentials not found. Ensure the secret is mounted correctly, credentials file exists, or environment variables are set.")
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
        group_id: The Google Group ID
        credentials: OAuth credentials with appropriate scopes
        
    Returns:
        True if the user is a member of the group, False otherwise
    """
    try:
        logger.info(f"Checking if {email} is a member of group {group_id}")
        
        # Need Directory API scope for this to work
        # 'https://www.googleapis.com/auth/admin.directory.group.member.readonly'
        if credentials is None:
            # Use the service account method if no credentials provided
            service = get_directory_service()
            if not service:
                logger.error("Failed to create directory service with service account")
                return False
        else:
            # Use the provided user credentials
            service = build('admin', 'directory_v1', credentials=credentials)
        
        # Try direct membership check first
        try:
            logger.debug(f"Checking direct membership for {email} in group {group_id}")
            response = service.members().get(groupKey=group_id, memberKey=email).execute()
            # If we get here without exception, the user is a member
            logger.info(f"User {email} is a member of group {group_id}")
            return True
        except HttpError as e:
            if e.resp.status == 404:
                # User is not a direct member, continue to check full member list
                logger.info(f"User {email} is not a direct member of group {group_id}")
                pass
            else:
                logger.error(f"Error checking direct membership: {str(e)}")
                return False
        
        # List all members of the group
        try:
            logger.debug(f"Fetching all members of group {group_id}")
            results = service.members().list(groupKey=group_id, includeDerivedMembership=True).execute()
            members = results.get('members', [])
            
            # Check if user's email is in the group
            is_member = any(member.get('email', '').lower() == email.lower() for member in members)
            
            if is_member:
                logger.info(f"User {email} found in members list of group {group_id}")
            else:
                logger.info(f"User {email} NOT found in members list of group {group_id}")
                
            return is_member
        except Exception as e:
            logger.error(f"Error listing group members: {str(e)}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to check group membership: {e}")
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

        # Store email in session state for use in other pages
        st.session_state['user_email'] = user_email
        
        # Verify organization
        if verify_organization(id_info):
            # Check if user is member of regnum-site group using the new auth system
            is_admin = is_group_member(user_email, REGNUM_ADMIN_GROUP)
            st.session_state['is_admin'] = is_admin
            logger.info(f"User {user_email} authenticated successfully")
            
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
            
            # Always show Duty Request page
            st.page_link("pages/5_Duty_Request.py", label="Request New Duty/Job", icon="✅")
            
            # Only show restricted pages if user is in regnum-site group
            if is_admin:
                st.page_link("pages/1_Groups.py", label="Manage Groups and Members", icon="👥")
                st.page_link("pages/2_Regnum.py", label="Regnum Data Entry", icon="📝")
            else:
                st.warning("Note: You don't have access to administration pages. Access to Groups and Regnum pages requires membership in the regnum-site group.")
                
                # Show more helpful information about how to get access
                st.info("To request access to administrative functions, please contact webminister@westkingdom.org")
        else:
            # Not a Western Digital account
            logger.warning(f"User {user_email} attempted to access app with non-Western Kingdom account")
            st.error("You must use a @westkingdom.org email address to access this application.")
            st.warning("If you are a Kingdom officer without a westkingdom.org email, please contact webminister@westkingdom.org.")
            st.button("Logout", on_click=lambda: st.session_state.clear())
    except Exception as e:
        logger.error(f"Error verifying ID token: {str(e)}")
        st.error(f"Authentication error: {e}")

# Add health check and status, hidden from normal UI
if 'healthz' in st.query_params:
    health_check()

# Debug section for authentication and token issues (accessed via query param)
if 'debug' in st.query_params and st.query_params['debug'] == 'auth':
    st.markdown("---")
    st.subheader("Debug Information")
    
    with st.expander("Authentication Details"):
        if 'credentials' in st.session_state:
            st.write("Authentication Status: ✓ User is authenticated")
            credentials = st.session_state['credentials']
            st.json({
                "token_type": credentials.token_type,
                "expires_at": datetime.datetime.fromtimestamp(credentials.expiry).strftime('%Y-%m-%d %H:%M:%S'),
                "scopes": credentials.scopes if hasattr(credentials, 'scopes') else "Not available"
            })
        else:
            st.write("Authentication Status: ✗ User is not authenticated")
            
        if 'user_email' in st.session_state:
            st.write(f"User Email: {st.session_state.get('user_email')}")
        if 'is_admin' in st.session_state:
            st.write(f"Admin Access: {'Yes' if st.session_state.get('is_admin') else 'No'}")


def health_check():
    """
    Internal endpoint for health checks.
    Used by Google Cloud Run to determine if the service is healthy.
    """
    st.write("Service Status: Healthy")
    st.write(f"App Version: 1.0.0")
    st.write(f"Environment: {os.environ.get('ENVIRONMENT', 'Not set')}")
    st.write(f"Backend API: {os.environ.get('REGNUM_API_URL', 'Not set')}")
    # Hide the main UI components when displaying health check
    st.markdown("""
    <style>
        .main > div:first-child {display: none}
        header {visibility: hidden}
        footer {visibility: hidden}
    </style>
    """, unsafe_allow_html=True)