import streamlit as st
import requests
from utils.config import api_url
# Updated import: get_all_groups now returns (options, name_to_id_map)
from utils.queries import get_all_groups, get_group_members, add_member_to_group, remove_member_from_group, is_valid_email
import pandas as pd
import re


# Streamlit UI
st.title("Group Management")

# Create tabs for different group operations
tab1, tab2, tab3 = st.tabs(["View Groups", "Create Group", "Manage Members"])

with st.sidebar:
    st.header("Actions")
    if st.button("Create New Group"):
        # Navigate to Create Group tab or handle differently if needed
        # For now, just rerun might not be the best UX, consider setting active tab
        st.experimental_rerun()

# Tab for viewing groups and members
with tab1:
    st.header("View Groups")

    # Get all groups using the updated function
    # It now returns (list_of_names, name_to_id_dict)
    group_options, group_name_to_id = get_all_groups()

    if not group_options: # Check if the list of names is empty
        st.warning("No groups found or failed to load groups. Please check the data source or create a new group.")
    else:
        # Add search functionality using st.text_input
        search_term = st.text_input("Search Groups", "", key="view_search") # Added key for uniqueness

        # Filter group names based on search term
        filtered_group_names = [name for name in group_options if search_term.lower() in name.lower()]

        # Selectbox for selecting a group by name
        selected_group_name = st.selectbox(
            "Select a Group",
            options=filtered_group_names,
            index=None, # Default to no selection
            placeholder="Select a group...",
            key="select_view_group"
        )

        # Get the selected group's data
        if selected_group_name:
            # Get the ID from the dictionary
            selected_id = group_name_to_id.get(selected_group_name)

            if selected_id:
                try:
                    # API response is expected to be like: {"members": [ {member_data}, ... ]}
                    api_response = get_group_members(selected_id)

                    st.write(f"### Group: {selected_group_name}") # Display the selected name

                    # Display members - Applying Regnum formatting
                    if api_response is not None:
                        # Extract the actual list of members from the response dictionary
                        members_list = api_response.get('members', [])

                        if members_list: # Check if the extracted list is not empty
                            try:
                                # Attempt to create DataFrame from the extracted list
                                member_df = pd.DataFrame(members_list)

                                # Define desired columns based on the keys found in the nested objects
                                all_possible_columns = ['email', 'role', 'status', 'type']
                                columns_to_display = [col for col in all_possible_columns if col in member_df.columns]

                                if columns_to_display:
                                    # Display using st.dataframe for better interactivity and formatting
                                    # Hide the index column for cleaner presentation
                                    st.dataframe(member_df[columns_to_display], hide_index=True)
                                elif not member_df.empty:
                                    # Fallback if NO desired columns are present but DF is not empty
                                    st.warning("Member data found, but expected columns ('email', 'role', etc.) are missing. Displaying all available data:")
                                    st.dataframe(member_df, hide_index=True)
                                else:
                                    # Should not be hit if members_list was checked, but as a safeguard
                                    st.info("No member data to display (DataFrame empty).")

                            except Exception as df_error:
                                st.error(f"Error processing member data into a table: {df_error}")
                                st.warning("Displaying raw member data instead (from exception handler):")
                                # Display the original API response if DataFrame fails
                                st.json(api_response)

                        else:
                            st.info("This group has no members (API returned an empty 'members' list or missing key).")
                    else:
                        st.warning(f"Could not fetch members for {selected_group_name}. The API might be down or the group ID is invalid (API returned None).")

                except Exception as e:
                    st.error(f"An error occurred while fetching members for {selected_group_name}: {e}")
            else:
                # This should not happen if the selectbox is populated correctly
                st.error(f"Could not find ID for selected group '{selected_group_name}'. Data inconsistency?")
        else:
            st.info("Please select a group to view its members.")

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
        # Check if a group is selected before proceeding
        if selected_group_name:
            try:
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
            except StopIteration:
                st.error("Selected group not found. Please refresh the group list.")
        else:
            st.info("Please select a group to manage its members.")
