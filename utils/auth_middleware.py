import streamlit as st
from functools import wraps
import time
from google.oauth2 import id_token
import google.auth.transport.requests
from utils.logger import app_logger as logger

def verify_organization(idinfo):
    """
    Checks if the authenticated user belongs to the 'westkingdom.org' domain.
    
    Args:
        idinfo: The dictionary containing the user's ID token information
        
    Returns:
        True if the 'hd' claim in the token matches 'westkingdom.org', False otherwise
    """
    return idinfo.get('hd') == 'westkingdom.org'

def require_auth(flow_provider):
    """
    Authentication middleware decorator that ensures users are logged in.
    
    Args:
        flow_provider: A function that returns the OAuth flow object
    
    Returns:
        A decorator function that checks authentication status
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if 'credentials' not in st.session_state:
                logger.info("User not authenticated, redirecting to login")
                st.error("Please login to access this page")
                try:
                    flow = flow_provider()
                    auth_url, _ = flow.authorization_url(prompt='consent')
                    st.markdown(f'<a href="{auth_url}" target="_self">Login with Google</a>', unsafe_allow_html=True)
                except Exception as e:
                    logger.error(f"Error generating authorization URL: {str(e)}")
                    st.error(f"Error generating authorization URL: {e}")
                st.stop()
            else:
                # Verify the token is still valid
                credentials = st.session_state['credentials']
                request = google.auth.transport.requests.Request()
                
                try:
                    id_info = id_token.verify_oauth2_token(
                        credentials.id_token, request, credentials.client_id
                    )
                    
                    # Check if token is expired
                    if 'exp' in id_info and time.time() > id_info['exp']:
                        logger.warning("Token expired, redirecting to login")
                        del st.session_state['credentials']
                        st.rerun()
                        
                    # Verify organization
                    if not verify_organization(id_info):
                        logger.warning(f"Access denied for non-WK user: {id_info.get('email', 'unknown')}")
                        st.error("Access denied. User does not belong to westkingdom.org")
                        del st.session_state['credentials']
                        st.rerun()
                    
                    # Token is valid, let the function run
                    logger.debug(f"Authenticated access to {func.__name__} by {id_info.get('email', 'unknown')}")
                    
                except ValueError as e:
                    logger.warning(f"Token validation error: {str(e)}")
                    del st.session_state['credentials']
                    st.rerun()
                except Exception as e:
                    logger.error(f"Authentication error: {str(e)}")
                    st.error(f"Authentication error: {e}")
                    st.stop()
                    
            return func(*args, **kwargs)
        return wrapper
    return decorator