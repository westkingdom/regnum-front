import streamlit as st
import os
import sys
import json
import pandas as pd
from utils.debug_tools import debug_info, debug_panel
from utils.queries import get_all_groups, get_group_members
from utils.logger import app_logger as logger

# Set page configuration
st.set_page_config(page_title="Debug Mode", page_icon="🐞", layout="wide")

# Password protection for the debug page
def check_password():
    """Return True if the user entered the correct password"""
    if "debug_password_correct" not in st.session_state:
        st.session_state["debug_password_correct"] = False

    if st.session_state["debug_password_correct"]:
        return True

    # Password field
    password = st.text_input("Debug page password", type="password")
    
    # Check if password is correct (simple for development, not for production)
    if password == "debug123":
        st.session_state["debug_password_correct"] = True
        st.success("Authenticated!")
        return True
    elif password:
        st.error("Incorrect password")
        return False
    else:
        return False

# Only show the debug interface if password is correct
if check_password():
    st.title("Debug Mode 🐞")
    st.warning("This page is for development and debugging only. Do not use in production.")

    # Create tabs for different debugging sections
    system_tab, auth_tab, data_tab, api_tab = st.tabs([
        "System Info", "Authentication", "Mock Data", "API Testing"
    ])

    with system_tab:
        st.header("System Information")
        debug_panel()
        
        st.subheader("Python Information")
        st.code(f"""
Python Version: {sys.version}
Platform: {sys.platform}
Executable: {sys.executable}
Path: {sys.path}
        """)
        
        st.subheader("Environment Variables")
        env_dict = {
            "USE_MOCK_DATA": os.environ.get("USE_MOCK_DATA", "Not set"),
            "BYPASS_GROUP_CHECK": os.environ.get("BYPASS_GROUP_CHECK", "Not set"),
            "MOCK_API_ERRORS": os.environ.get("MOCK_API_ERRORS", "Not set"),
            "STREAMLIT_LOG_LEVEL": os.environ.get("STREAMLIT_LOG_LEVEL", "Not set"),
            "API_URL": os.environ.get("API_URL", "Not set"),
            "REDIRECT_URL": os.environ.get("REDIRECT_URL", "Not set"),
        }
        
        env_df = pd.DataFrame({
            "Variable": env_dict.keys(),
            "Value": env_dict.values()
        })
        
        st.dataframe(env_df, use_container_width=True)
        
        if st.button("Toggle Mock Data Mode"):
            current = os.environ.get("USE_MOCK_DATA", "false").lower() == "true"
            os.environ["USE_MOCK_DATA"] = str(not current).lower()
            st.success(f"USE_MOCK_DATA set to {not current}")
            st.rerun()
            
        if st.button("Toggle Auth Bypass"):
            current = os.environ.get("BYPASS_GROUP_CHECK", "false").lower() == "true"
            os.environ["BYPASS_GROUP_CHECK"] = str(not current).lower()
            st.success(f"BYPASS_GROUP_CHECK set to {not current}")
            st.rerun()

    with auth_tab:
        st.header("Authentication Debugging")
        
        st.subheader("Current Authentication State")
        if "authenticated" in st.session_state:
            st.success(f"Authentication status: {st.session_state.authenticated}")
            if "user_email" in st.session_state:
                st.info(f"User email: {st.session_state.user_email}")
                
                # Test group membership
                if st.button("Test Group Membership"):
                    from utils.auth import get_directory_service, is_group_member
                    from utils.config import REGNUM_ADMIN_GROUP
                    
                    user_email = st.session_state.user_email
                    group_id = REGNUM_ADMIN_GROUP
                    
                    st.write(f"Testing if {user_email} is a member of group {group_id}")
                    
                    # Test direct membership
                    try:
                        result = is_group_member(user_email, group_id)
                        st.write(f"Group membership result: {result}")
                    except Exception as e:
                        st.error(f"Error testing group membership: {e}")
        else:
            st.error("Not authenticated")
            
        # Session management
        st.subheader("Session Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Set Test Authentication"):
                st.session_state.authenticated = True
                st.session_state.user_email = "test@westkingdom.org"
                st.success("Set test authentication")
                st.rerun()
                
        with col2:
            if st.button("Clear Authentication"):
                if "authenticated" in st.session_state:
                    del st.session_state.authenticated
                if "user_email" in st.session_state:
                    del st.session_state.user_email
                st.success("Cleared authentication")
                st.rerun()

    with data_tab:
        st.header("Mock Data Testing")
        
        # Show groups and allow selection
        st.subheader("Groups")
        
        group_options, group_name_to_id = get_all_groups()
        
        if group_options:
            selected_group = st.selectbox("Select a group", options=group_options)
            
            if selected_group:
                group_id = group_name_to_id.get(selected_group)
                st.write(f"Group ID: {group_id}")
                
                if st.button("View Group Members"):
                    with st.spinner("Fetching group members..."):
                        members_data = get_group_members(group_id)
                        
                        if members_data and "members" in members_data:
                            members_list = members_data["members"]
                            st.success(f"Found {len(members_list)} members")
                            
                            members_df = pd.DataFrame(members_list)
                            st.dataframe(members_df, use_container_width=True)
                        else:
                            st.warning("No members found or invalid response")
        else:
            st.warning("No groups found")
            
        # Create mock data
        st.subheader("Generate Mock Data")
        
        with st.form("mock_data_form"):
            group_name = st.text_input("Group Name", "Test Group")
            members_count = st.number_input("Number of Members", 1, 10, 3)
            
            submitted = st.form_submit_button("Generate Mock Data")
            
            if submitted:
                from utils.debug_tools import mock_group_member, create_mock_group_data
                
                # Generate mock members
                mock_members = [
                    mock_group_member(f"member{i}@westkingdom.org", 
                                      "OWNER" if i == 0 else "MEMBER")
                    for i in range(members_count)
                ]
                
                # Create mock group data
                mock_group = create_mock_group_data(
                    group_id=group_name.lower().replace(" ", "-"),
                    members=mock_members
                )
                
                st.json(mock_group)
                
                # Copy to clipboard option
                st.code(json.dumps(mock_group, indent=2))
                st.info("You can copy this JSON data for testing.")

    with api_tab:
        st.header("API Testing")
        
        st.subheader("API Configuration")
        api_url = os.environ.get("API_URL", "Not configured")
        st.write(f"Current API URL: {api_url}")
        
        # Simple API test
        if st.button("Test API Connection"):
            import requests
            
            try:
                with st.spinner("Testing API connection..."):
                    response = requests.get(f"{api_url}/health", timeout=5)
                    
                    if response.status_code == 200:
                        st.success(f"API connection successful! Status code: {response.status_code}")
                        try:
                            st.json(response.json())
                        except:
                            st.write(response.text)
                    else:
                        st.error(f"API returned error status: {response.status_code}")
                        st.write(response.text)
            except Exception as e:
                st.error(f"Error connecting to API: {str(e)}")
                
        # Custom API request
        st.subheader("Custom API Request")
        
        with st.form("api_request_form"):
            method = st.selectbox("Method", ["GET", "POST", "PUT", "DELETE"])
            endpoint = st.text_input("Endpoint", "/groups/")
            headers = st.text_area("Headers (JSON)", "{}")
            body = st.text_area("Body (JSON)", "{}")
            
            api_submit = st.form_submit_button("Send Request")
            
            if api_submit:
                import requests
                import json
                
                try:
                    headers_dict = json.loads(headers) if headers.strip() else {}
                    body_dict = json.loads(body) if body.strip() else {}
                    
                    with st.spinner("Sending API request..."):
                        full_url = f"{api_url}{endpoint}"
                        st.write(f"Sending {method} request to: {full_url}")
                        
                        if method == "GET":
                            response = requests.get(full_url, headers=headers_dict, params=body_dict, timeout=10)
                        elif method == "POST":
                            response = requests.post(full_url, headers=headers_dict, json=body_dict, timeout=10)
                        elif method == "PUT":
                            response = requests.put(full_url, headers=headers_dict, json=body_dict, timeout=10)
                        elif method == "DELETE":
                            response = requests.delete(full_url, headers=headers_dict, json=body_dict, timeout=10)
                            
                        st.write(f"Status code: {response.status_code}")
                        
                        try:
                            st.json(response.json())
                        except:
                            st.write(response.text)
                except Exception as e:
                    st.error(f"Error sending request: {str(e)}")

# Hide this page from the sidebar in production mode
if os.environ.get("STREAMLIT_ENV") == "production":
    st.markdown("""
    <style>
    [data-testid="stSidebarNav"] ul li:has(div[aria-label*="debug.py"]) {
        display: none;
    }
    </style>
    """, unsafe_allow_html=True) 