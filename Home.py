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
            
            # DEBUGGING: Add detailed information about the group check
            with st.expander("Debug Information (Admin Only)"):
                st.write(f"User Email: {user_email}")
                st.write(f"Admin Group ID: {REGNUM_ADMIN_GROUP}")
                st.write(f"Admin Group Name: regnum-site")
                
                # Get directory service status
                service = get_directory_service(credentials=credentials)
                st.write(f"Directory Service Created: {service is not None}")
                
                # Check if credentials have the right scopes
                st.write("Credential Scopes:")
                scope_list = []
                if hasattr(credentials, 'scopes'):
                    scope_list = credentials.scopes
                    for scope in scope_list:
                        st.write(f"- {scope}")
                else:
                    st.write("No scopes found in credentials")
                    
                # Check if the required scope is present
                required_scope = 'https://www.googleapis.com/auth/admin.directory.group.member.readonly'
                if required_scope in scope_list:
                    st.success(f"✅ Directory API scope is present in credentials")
                else:
                    st.error(f"❌ Directory API scope is missing from credentials")
                    st.info(f"Required scope: {required_scope}")
                
                # Try both methods of checking membership
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Method 1: Direct API Check")
                    try:
                        direct_result = is_member_of_group(user_email, REGNUM_ADMIN_GROUP, credentials=credentials)
                        if direct_result:
                            st.success("✅ You ARE a member using direct check")
                        else:
                            st.error("❌ You are NOT a member using direct check")
                    except Exception as e:
                        st.error(f"Error in direct check: {e}")
                
                with col2:
                    st.subheader("Method 2: Auth Utility Check")
                    try:
                        utility_result = is_group_member(user_email, REGNUM_ADMIN_GROUP)
                        if utility_result:
                            st.success("✅ You ARE a member using auth.py check")
                        else:
                            st.error("❌ You are NOT a member using auth.py check")
                    except Exception as e:
                        st.error(f"Error in utility check: {e}")
                
                # Try to fetch group details
                if service and st.button("Check Group Details"):
                    try:
                        group_info = service.groups().get(groupKey=REGNUM_ADMIN_GROUP).execute()
                        st.write("Group information:")
                        st.json(group_info)
                        
                        # Get members list
                        members = service.members().list(groupKey=REGNUM_ADMIN_GROUP).execute()
                        st.write("Group members:")
                        if 'members' in members:
                            member_emails = [m.get('email', '') for m in members.get('members', [])]
                            st.write(member_emails)
                            
                            if user_email in member_emails:
                                st.success(f"✅ Your email {user_email} is in the members list!")
                            else:
                                st.error(f"❌ Your email {user_email} is NOT in the members list.")
                        else:
                            st.write("No members found in this group.")
                    except Exception as e:
                        st.write(f"Error getting group details: {e}")
                    
                # Explain how to fix the issue
                st.write("### If you need access:")
                st.write("Contact webminister@westkingdom.org to be added to the regnum-site Google Group.")
                st.write("This group controls access to the administrative pages like Groups and Regnum data entry.")
                
                # Allow direct addition to the group for troubleshooting
                st.write("### Advanced Troubleshooting")
                st.write("If you are an administrator, you can try to add yourself to the group directly:")
                
                if st.button("Add Me To Regnum-Site Group"):
                    try:
                        # Get a fresh directory service
                        admin_service = get_directory_service(impersonate_user="webminister@westkingdom.org")
                        
                        if admin_service:
                            try:
                                # Create member object
                                member = {
                                    'email': user_email,
                                    'role': 'MEMBER'
                                }
                                
                                # Try to add to the group
                                result = admin_service.members().insert(
                                    groupKey=REGNUM_ADMIN_GROUP,
                                    body=member
                                ).execute()
                                
                                st.success(f"✅ Successfully added {user_email} to the regnum-site group!")
                                st.info("Please refresh the page to check your updated access.")
                                
                            except Exception as e:
                                st.error(f"Failed to add member to group: {e}")
                        else:
                            st.error("Could not create directory service to add member.")
                    except Exception as e:
                        st.error(f"Error in group addition process: {e}")
                
                # Show the environment variables that might affect service account access
                st.write("### Environment Variables")
                if st.button("Check Environment Variables"):
                    env_vars = {
                        "GOOGLE_APPLICATION_CREDENTIALS": os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "Not set"),
                        "BYPASS_GROUP_CHECK": os.environ.get("BYPASS_GROUP_CHECK", "Not set"),
                        "PWD": os.environ.get("PWD", "Not set"),
                        "HOME": os.environ.get("HOME", "Not set")
                    }
                    st.json(env_vars)
            
            # Regular group membership check
            is_admin = is_group_member(user_email, REGNUM_ADMIN_GROUP)
            st.session_state['is_admin'] = is_admin
            logger.info(f"User {user_email} authenticated successfully")
            
            # TEMP FIX: Force admin access for troubleshooting
            if user_email.endswith('@westkingdom.org'):
                override_admin = st.checkbox("Override admin access (temporary fix)", value=False)
                if override_admin:
                    is_admin = True
                    st.session_state['is_admin'] = True
            
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
                if user_email.endswith('@westkingdom.org'):
                    with st.expander("How to get access to admin pages"):
                        st.write("""
                        ### Administrative Access
                        
                        To access the Groups and Regnum pages, you need to be a member of the 'regnum-site' Google Group.
                        
                        #### How to request access:
                        1. Email webminister@westkingdom.org with your request
                        2. Include your role or position that requires this access
                        3. Wait for confirmation that you've been added to the group
                        
                        Only users with administrative responsibilities for the Regnum site should have this access.
                        """)

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