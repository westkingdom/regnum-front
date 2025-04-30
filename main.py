import streamlit as st
import google.auth
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
import google.auth.transport.requests
import os
import json

# Define the path where the secret is mounted
SECRET_CREDENTIALS_PATH = '/oauth/google_credentials.json' # Updated path
# Fallback for local development (optional)
LOCAL_CREDENTIALS_PATH = 'utils/google_credentials.json' # Local fallback remains the same

# Determine the correct path
credentials_path = SECRET_CREDENTIALS_PATH if os.path.exists(SECRET_CREDENTIALS_PATH) else LOCAL_CREDENTIALS_PATH

# Load client secrets
try:
    # Configure the OAuth 2.0 flow using the determined path
    flow = Flow.from_client_secrets_file(
        credentials_path,
        scopes=['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile'],
        # IMPORTANT: Update redirect_uri for Cloud Run deployment
        # You'll need to get the Cloud Run service URL after the first deployment
        # and add it as an authorized redirect URI in your Google Cloud OAuth Client ID settings.
        redirect_uri=os.environ.get('REDIRECT_URI', 'https://regnum-front-85382560394.us-west1.run.app') # Use env var or default
    )
except FileNotFoundError:
    st.error(f"Credentials file not found at {credentials_path}. Ensure the secret is mounted correctly in Cloud Run or the local file exists.")
    st.stop()
except Exception as e:
    st.error(f"Error loading credentials: {e}")
    st.stop()


# Function to verify the user's organization
def verify_organization(idinfo):

    return idinfo.get('hd') == 'westkingdom.org'


# Streamlit app
st.title("West Kingdom Google Authentication")

# Handle OAuth callback
query_params = st.query_params
if 'code' in query_params and 'credentials' not in st.session_state:
    try:
        flow.fetch_token(code=query_params['code'])
        st.session_state['credentials'] = flow.credentials
        # Clear query params after fetching token
        st.query_params.clear()
        st.rerun() # Rerun to update the state
    except Exception as e:
        st.error(f"Error fetching OAuth token: {e}")


# Check if the user is authenticated
if 'credentials' not in st.session_state:
    try:
        auth_url, _ = flow.authorization_url(prompt='consent')
        st.markdown(f'<a href="{auth_url}" target="_self">Login with Google</a>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error generating authorization URL: {e}")

else:
    credentials = st.session_state['credentials']
    request = google.auth.transport.requests.Request()

    try:
        id_info = id_token.verify_oauth2_token(
            credentials.id_token, request, credentials.client_id
        )

        # Optional: Verify organization
        if verify_organization(id_info):
            st.success(f"Welcome {id_info.get('name')} ({id_info.get('email')})")
            st.write("You are authenticated.")
            # Proceed with your application logic here
            # e.g., show the main app content or redirect to pages

            if st.button("Logout"):
                del st.session_state['credentials']
                st.rerun()
        else:
            st.error("Access denied. User does not belong to the required organization.")
            if st.button("Logout"):
                del st.session_state['credentials']
                st.rerun()

    except ValueError as e:
        # Token expired or invalid
        st.warning(f"Session expired or invalid: {e}. Please login again.")
        del st.session_state['credentials']
        # Regenerate auth URL for re-login
        try:
            auth_url, _ = flow.authorization_url(prompt='consent')
            st.markdown(f'<a href="{auth_url}" target="_self">Login with Google</a>', unsafe_allow_html=True)
        except Exception as url_e:
            st.error(f"Error generating re-login URL: {url_e}")
    except Exception as e:
        st.error(f"An error occurred during authentication verification: {e}")
        if st.button("Logout"):
            del st.session_state['credentials']
            st.rerun()

