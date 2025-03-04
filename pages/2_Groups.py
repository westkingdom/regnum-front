import streamlit as st
import requests
from utils.config import api_url
import pandas as pd
import re

def get_all_groups():
    """Fetch all groups from the API"""
    response = requests.get(f"{api_url}/groups/")
    if response.status_code == 200:
        return response.json()
    return None

def get_group_by_id(group_id: str):
    """Fetch a group by its ID"""
    response = requests.get(f"{api_url}/groups/{group_id}/")
    if response.status_code == 200:
        return response.json()
    return None

def get_group_members(group_id: str):
    """Fetch the members of a group"""
    response = requests.get(f"{api_url}/groups/{group_id}/members/")
    if response.status_code == 200:
        return response.json()
    return None

def create_group(group_id: str, group_name: str):
    """Create a new group"""
    params = {"group_id": group_id, "group_name": group_name}
    response = requests.post(f"{api_url}/groups/", params=params)
    return response.status_code == 200

def add_member_to_group(group_id: str, member_email: str):
    """Add a member to a group"""
    params = {"member_email": member_email}
    response = requests.post(f"{api_url}/groups/{group_id}/add-member/", params=params)
    return response.status_code == 200

def remove_member_from_group(group_id: str, member_email: str):
    """Remove a member from a group"""
    response = requests.delete(f"{api_url}/groups/{group_id}/members/{member_email}")
    return response.status_code == 200

def is_valid_email(email: str) -> bool:
    """Validate email format and domain"""
    pattern = r'^[a-zA-Z0-9._%+-]+@westkingdom\.org$'
    return bool(re.match(pattern, email))

# Streamlit UI
st.title("Group Management")

# Create tabs for different group operations
tab1, tab2, tab3 = st.tabs(["View Groups", "Create Group", "Manage Members"])

with st.sidebar:
    st.header("Actions")
    if st.button("Create New Group"):
        st.experimental_rerun()

# Tab for viewing groups and members
with tab1:
    st.header("View Groups")

    # Get all groups
    groups = get_all_groups()

    if not groups or 'groups' not in groups:
        st.warning("No groups found. Please create a new group to begin.")
    else:
        group_names = [group['name'] for group in groups['groups']]
        # Add search functionality using st.text_input
        search_term = st.text_input("Search Groups", "")
        
        # Filter group names based on search term
        filtered_group_names = [name for name in group_names if search_term.lower() in name.lower()]

        # Selectbox for selecting a group by name instead of ID
        selected_group_name = st.selectbox(
            "Select a Group",
            options=filtered_group_names,
            key="select_view_group"
        )

        # Get the selected group's data
        selected_group = next(group for group in groups['groups'] if group['name'] == selected_group_name)
        selected_id = selected_group['id']
        members = get_group_members(selected_id)
        
        st.write(f"### Group: {selected_group['name']}")
        
        # Fixed: Correctly access the members dictionary and create DataFrame
        if members and 'members' in members:
            members_df = pd.DataFrame(members['members'])  # Remove the parentheses
            if not members_df.empty:
                st.dataframe(members_df)
            else:
                st.info("No members in this group")
        else:
            st.warning("Unable to fetch member data")

# Tab 2: Create New Group
with tab2:
    st.header("Create New Group")

    # Add input fields for creating a new group
    with st.form(key="create_group_form"):
        st.text_input("Group Name", key="new_group_name")
        if st.form_submit_button("Create Group"):
            pass  # Replace with your actual implementation

# Tab 3: Manage Members
with tab3:
    st.header("Manage Members")

    groups = get_all_groups()
    if not groups or 'groups' not in groups:
        st.warning("No groups found. Please create a new group to begin.")
    else:
        group_names = [group['name'] for group in groups['groups']]
        # Add search functionality using st.text_input
        search_term = st.text_input("Search Groups", key="manage_search")
        
        # Filter group names based on search term
        filtered_group_names = [name for name in group_names if search_term.lower() in name.lower()]

        selected_group_name = st.selectbox(
            "Select a Group",
            options=filtered_group_names,
            key="select_manage_group"
        )

        # Get the selected group's data
        selected_group = next(group for group in groups['groups'] if group['name'] == selected_group_name)
        selected_id = selected_group['id']

        # Display current members
        st.subheader("Current Members")
        members = get_group_members(selected_id)
        if members and 'members' in members:
            members_df = pd.DataFrame(members['members'])
            if not members_df.empty:
                st.dataframe(members_df)
            else:
                st.info("No members in this group")
        
        # Add member form
        st.subheader("Add New Member")
        with st.form(key="add_member_form"):
            member_email = st.text_input(
                "Member Email",
                placeholder="user@westkingdom.org",
                help="Email must be from westkingdom.org domain"
            )
            
            submit_button = st.form_submit_button("Add Member")
            
            if submit_button:
                if not member_email:
                    st.error("Please enter an email address")
                elif not is_valid_email(member_email):
                    st.error("Invalid email format. Email must be from westkingdom.org domain")
                else:
                    # Attempt to add member
                    if add_member_to_group(selected_id, member_email):
                        st.success(f"Successfully added {member_email} to {selected_group_name}")
                        st.experimental_rerun()  # Refresh to show updated member list
                    else:
                        st.error("Failed to add member. Please try again.")

        # Remove member section
        st.subheader("Remove Member")
        if members and 'members' in members and members['members']:
            member_to_remove = st.selectbox(
                "Select member to remove",
                options=[member['email'] for member in members['members']],
                key="remove_member_select"
            )
            
            if st.button("Remove Selected Member"):
                if st.warning("Are you sure you want to remove this member?"):
                    if remove_member_from_group(selected_id, member_to_remove):
                        st.success(f"Successfully removed {member_to_remove}")
                        st.experimental_rerun()
                    else:
                        st.error("Failed to remove member. Please try again.")
        else:
            st.info("No members available to remove")
