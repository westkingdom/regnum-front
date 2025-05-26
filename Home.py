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
                redirect_uri=os.environ.get('REDIRECT_URL', 'https://wkregnum-njxuammdla-uw.a.run.app')
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
                    "redirect_uris": [os.environ.get('REDIRECT_URL', 'https://wkregnum-njxuammdla-uw.a.run.app')],
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
                redirect_uri=os.environ.get('REDIRECT_URL', 'https://wkregnum-njxuammdla-uw.a.run.app')
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
            # If we get here, the user is a member
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


# --- WKRegnum App Logic ---
st.set_page_config(page_title="WKRegnum - West Kingdom Regnum Portal") # Updated title
st.title("WKRegnum - West Kingdom Regnum Portal") # Updated title

# --- Authentication Flow ---

# 1. Handle OAuth Callback
# Check if 'code' is in query params (meaning user is returning from Google Auth)
# and if we don't already have credentials stored in the session state.
# Compatibility handling for different Streamlit versions
try:
    # Try using st.query_params (newer Streamlit versions)
    query_params = st.query_params
    code_param = query_params.get('code', None)
    
    # Function to clear query params in newer Streamlit versions
    def clear_query_params():
        st.query_params.clear()
except AttributeError:
    # Fallback for older Streamlit versions
    # Get parameters directly from URL using experimental_get_query_params
    query_params = st.experimental_get_query_params()
    code_param = query_params.get('code', [None])[0]  # Extract first element if it's a list
    
    # Function to clear query params in older Streamlit versions
    def clear_query_params():
        st.experimental_set_query_params()

# Handle the authentication code
if code_param and 'credentials' not in st.session_state:
    try:
        logger.info("OAuth code received, attempting to fetch token")
        flow.fetch_token(code=code_param)
        st.session_state['credentials'] = flow.credentials
        logger.info("Token fetched successfully, storing credentials in session state")
        # Clear query params after fetching token to prevent re-processing
        clear_query_params()
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

            # Display BYPASS_GROUP_CHECK status if it's enabled
            if os.environ.get('BYPASS_GROUP_CHECK', '').lower() == 'true':
                st.warning("⚠️ BYPASS_GROUP_CHECK is enabled - Group membership checks are bypassed for @westkingdom.org emails")
            
            # Add content for the Home page
            st.markdown("""
            ## Welcome to WKRegnum - The West Kingdom Regnum Portal
            
            This application provides access to the West Kingdom's officer roster and reporting system. Here you can:
            
            - View current officers and deputies
            - Search for officers by title or branch
            - Access office email templates
            - Generate reports
            
            Use the sidebar menu to navigate between different sections of the application.
            """)
            
            # Display admin specific message
            if is_admin:
                st.info("""
                ### Admin Functions
                
                As an administrator, you have access to additional features:
                - Manage officer information
                - Add or remove officers
                - Configure email templates
                - Edit branch information
                """)
        else:
            # Handle non-westkingdom.org users
            logger.warning(f"Non-westkingdom.org user attempted to authenticate: {user_email}")
            st.error(f"Access denied. You must use a @westkingdom.org Google account to access this application.")
            st.warning("Your account is not in the westkingdom.org domain. Please log out and try again with a westkingdom.org account.")
            
            # Add a logout button
            if st.button("Logout"):
                # Clear session state and redirect to login
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
    except Exception as e:
        logger.error(f"Error verifying token: {str(e)}")
        st.error(f"Authentication error: {e}")

# Health check endpoint for Cloud Run
def health_check():
    """Return a 200 status for Cloud Run health checks"""
    return {"status": "ok", "timestamp": datetime.datetime.now().isoformat()}

# This is only called by Cloud Run health checks
if os.environ.get('K_SERVICE') and os.environ.get('HEALTH_CHECK') == 'true':
    health_check()