import streamlit as st
import google.auth
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
import google.auth.transport.requests
import os
import json

# Load client secrets
with open('utils/google_credentials.json') as f:
    client_secrets = json.load(f)

# Configure the OAuth 2.0 flow
flow = Flow.from_client_secrets_file(
    'utils/google_credentials.json',
    scopes=['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile'],
    redirect_uri='http://localhost:8501'
)

# Function to verify the user's organization
def verify_organization(idinfo):
    email = idinfo.get('email')
    hd = idinfo.get('hd')
    if hd == 'westkingdom.com':
        return True
    return False

# Streamlit app
st.title("Google Workspace Authentication")

# Check if the user is authenticated
if 'credentials' not in st.session_state:
    auth_url, _ = flow.authorization_url(prompt='consent')
    st.write(f"[Login with Google]({auth_url})")
else:
    credentials = st.session_state['credentials']
    request = google.auth.transport.requests.Request()
    idinfo = id_token.verify_oauth2_token(credentials.id_token, request, client_secrets['web']['client_id'])

    if verify_organization(idinfo):
        st.write(f"Welcome, {idinfo['name']} from {idinfo['hd']}")
    else:
        st.write("You are not authorized to access this application.")

# Handle the OAuth 2.0 callback
query_params = st.experimental_get_query_params()
if 'code' in query_params:
    flow.fetch_token(authorization_response=query_params['code'][0])
    credentials = flow.credentials
    st.session_state['credentials'] = credentials
    st.experimental_rerun()