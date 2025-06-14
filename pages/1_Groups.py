import streamlit as st
import requests
from utils.config import api_url
from utils.queries import get_all_groups, get_group_members, add_member_to_group, remove_member_from_group, is_valid_email
from utils.logger import app_logger as logger
import pandas as pd
import json
import os
import re
import sys

# Set page configuration
st.set_page_config(page_title="Group Management", page_icon="👥", layout="wide")

# Main function - now publicly accessible
def main():
    logger.info("Accessing Groups management page - public access")
    
    # Initialize session state for public access
    if 'user_email' not in st.session_state:
        st.session_state['user_email'] = 'public@westkingdom.org'
        st.session_state['user_name'] = 'Public User'
        st.session_state['is_admin'] = True
    
    # Display current user info
    st.sidebar.success(f"Public Access Mode")
    st.sidebar.info("🔑 Full Access Granted")
    
    # Streamlit UI
    st.title("Group Management")
    st.markdown("Manage Google Groups and their memberships for the West Kingdom.")

    # --- Fetch group data ONCE ---
    all_groups, group_name_to_id = get_all_groups()

    # Check for errors during initial group load
    if not all_groups:
        logger.warning("No groups found or failed to load groups")
        st.warning("No groups found or failed to load groups. Cannot proceed with group management.")
        st.info("This could be due to API connectivity issues or insufficient permissions.")
        st.stop() # Stop execution if no groups are loaded

    # Create tabs for different group operations
    tab1, tab2, tab3 = st.tabs(["View Groups", "Create Group", "Manage Members"])

    with st.sidebar:
        st.header("Actions")
        st.markdown("### Quick Actions")
        if st.button("🔄 Refresh Groups"):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("### Statistics")
        st.metric("Total Groups", len(all_groups))

    # Tab for viewing groups and members
    with tab1:
        st.header("View Groups")

        # Add search functionality using st.text_input
        search_term_view = st.text_input("Search Groups", "", key="view_search") # Renamed key slightly

        # Filter group names based on search term
        filtered_group_names_view = [name for name in all_groups if search_term_view.lower() in name.lower()]

        # Selectbox for selecting a group by name
        selected_group_name_view = st.selectbox(
            "Select a Group",
            options=filtered_group_names_view,
            index=None, # Default to no selection
            placeholder="Select a group...",
            key="select_view_group"
        )

        # Get the selected group's data
        if selected_group_name_view:
            # --- Use the already fetched map ---
            selected_id = group_name_to_id.get(selected_group_name_view)

            if selected_id:
                try:
                    logger.info(f"Fetching members for group: {selected_group_name_view} (ID: {selected_id})")
                    # API response is expected to be like: {"members": [ {member_data}, ... ]}
                    api_response = get_group_members(selected_id)

                    st.write(f"### Group: {selected_group_name_view}") # Display the selected name
                    st.write(f"**Group ID:** `{selected_id}`")

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
                                    logger.warning(f"Member data found for {selected_group_name_view}, but expected columns are missing")
                                    st.warning("Member data found, but expected columns ('email', 'role', etc.) are missing. Displaying all available data:")
                                    st.dataframe(member_df, hide_index=True)
                                else:
                                    # Should not be hit if members_list was checked, but as a safeguard
                                    logger.info(f"Group {selected_group_name_view} has empty DataFrame for members")
                                    st.info("No member data to display (DataFrame empty).")

                            except Exception as df_error:
                                logger.error(f"Error processing member data into a table: {str(df_error)}")
                                st.error(f"Error processing member data into a table: {df_error}")
                                st.warning("Displaying raw member data instead (from exception handler):")
                                # Display the original API response if DataFrame fails
                                st.json(api_response)

                        else:
                            logger.info(f"Group {selected_group_name_view} has no members")
                            st.info("This group has no members (API returned an empty 'members' list or missing key).")
                    else:
                        logger.warning(f"Failed to fetch members for {selected_group_name_view}")
                        st.warning(f"Could not fetch members for {selected_group_name_view}. The API might be down or the group ID is invalid (API returned None).")

                except Exception as e:
                    logger.error(f"Error fetching members for {selected_group_name_view}: {str(e)}")
                    st.error(f"An error occurred while fetching members for {selected_group_name_view}: {e}")
            else:
                # This should not happen if the selectbox is populated correctly
                logger.error(f"Could not find ID for selected group '{selected_group_name_view}'")
                st.error(f"Could not find ID for selected group '{selected_group_name_view}'. Data inconsistency?")
        else:
            st.info("Please select a group to view its members.")

    # Tab 2: Create New Group
    with tab2:
        st.header("Create New Group")
        st.warning("⚠️ Group creation functionality is not yet implemented.")

        # Add input fields for creating a new group
        with st.form(key="create_group_form"):
            st.text_input("Group Name", key="new_group_name")
            if st.form_submit_button("Create Group"):
                # --- Placeholder for Create Group Logic ---
                logger.info("Create group functionality not yet implemented")
                st.info("Create group functionality not yet implemented.")
                pass

    # Tab 3: Manage Members
    with tab3:
        st.header("Manage Members")

        search_term_manage = st.text_input("Search Groups", key="manage_search") # Use unique key

        # Filter group names based on search term
        filtered_group_names_manage = [name for name in all_groups if search_term_manage.lower() in name.lower()]

        selected_group_name_manage = st.selectbox(
            "Select a Group to Manage", # Slightly clearer label
            options=filtered_group_names_manage,
            index=None, # Add index=None for placeholder
            placeholder="Select a group...", # Add placeholder
            key="select_manage_group"
        )

        # Get the selected group's data
        if selected_group_name_manage:
            # --- Use the already fetched group_name_to_id map ---
            selected_id = group_name_to_id.get(selected_group_name_manage)

            # Check if ID was found (it should be if name is from options)
            if not selected_id:
                logger.error(f"Could not find ID for selected group '{selected_group_name_manage}'")
                st.error(f"Could not find ID for selected group '{selected_group_name_manage}'. Data inconsistency?")
                st.stop() # Stop if ID is missing

            # Display current members
            st.subheader(f"Current Members of {selected_group_name_manage}")
            logger.info(f"Fetching members for group to manage: {selected_group_name_manage} (ID: {selected_id})")
            members_response = get_group_members(selected_id) # Fetch members for the selected group
            current_members = [] # Initialize as empty list

            if members_response and 'members' in members_response:
                # Store the list of member dicts
                current_members = members_response['members']
                members_df = pd.DataFrame(current_members)
                if not members_df.empty:
                    # Define desired columns based on the keys found in the nested objects
                    all_possible_columns = ['email', 'role', 'status', 'type']
                    columns_to_display = [col for col in all_possible_columns if col in members_df.columns]
                    if columns_to_display:
                        st.dataframe(members_df[columns_to_display], hide_index=True)
                    else: # Fallback if expected columns are missing
                        logger.warning(f"Member data found for {selected_group_name_manage}, but expected columns are missing")
                        st.warning("Member data found, but expected columns ('email', 'role', etc.) are missing. Displaying all available data:")
                        st.dataframe(members_df, hide_index=True)
                else:
                    logger.info(f"No members in group {selected_group_name_manage}")
                    st.info("No members currently in this group.")
            else:
                logger.info(f"No members in group {selected_group_name_manage} or failed to fetch")
                st.info("No members currently in this group or failed to fetch.")


            # Add member form
            st.subheader("Add New Member")
            with st.form(key="add_member_form"):
                member_email = st.text_input(
                    "Member Email",
                    placeholder="user@westkingdom.org",
                    help="Email must end with @westkingdom.org" # Updated help text
                )

                submit_button = st.form_submit_button("Add Member")

                if submit_button:
                    if not member_email:
                        logger.warning("Empty email submitted when adding member")
                        st.error("Please enter an email address.")
                    # Use the imported validation function
                    elif not is_valid_email(member_email): # Assuming is_valid_email checks the domain
                        logger.warning(f"Invalid email format submitted: {member_email}")
                        st.error("Invalid email address. Must end with @westkingdom.org.")
                    else:
                        # Attempt to add member
                        logger.info(f"Attempting to add {member_email} to group {selected_group_name_manage}")
                        st.info(f"Attempting to add {member_email}...") # Give feedback
                        if add_member_to_group(selected_id, member_email):
                            logger.info(f"Successfully added {member_email} to {selected_group_name_manage}")
                            st.success(f"Successfully added {member_email} to {selected_group_name_manage}")
                            st.experimental_rerun()  # Refresh to show updated member list
                        else:
                            logger.error(f"Failed to add member {member_email} to group {selected_group_name_manage}")
                            st.error(f"Failed to add member {member_email}. The user may already be in the group, or an API error occurred.")

            # Remove member section
            st.subheader("Remove Member")
            # Use the fetched current_members list
            if current_members:
                member_emails = [member.get('email', 'N/A') for member in current_members if member.get('email')] # Extract emails safely
                if member_emails:
                    member_to_remove = st.selectbox(
                        "Select member to remove",
                        options=member_emails,
                        index=None, # Add index=None
                        placeholder="Select email...", # Add placeholder
                        key="remove_member_select"
                    )

                    # Use a separate button to avoid form conflicts if needed, or ensure key is unique
                    if st.button("Remove Selected Member", key="remove_button"):
                        if member_to_remove: # Check if a member was actually selected
                            # Confirmation dialog (optional but recommended)
                            # st.warning(f"Are you sure you want to remove {member_to_remove}?")
                            # if st.button("Confirm Removal", key="confirm_remove"):
                            logger.info(f"Attempting to remove {member_to_remove} from group {selected_group_name_manage}")
                            st.info(f"Attempting to remove {member_to_remove}...") # Feedback
                            if remove_member_from_group(selected_id, member_to_remove):
                                logger.info(f"Successfully removed {member_to_remove} from group {selected_group_name_manage}")
                                st.success(f"Successfully removed {member_to_remove}")
                                st.experimental_rerun()
                            else:
                                logger.error(f"Failed to remove member {member_to_remove} from group {selected_group_name_manage}")
                                st.error(f"Failed to remove member {member_to_remove}. Please try again or check API logs.")
                        else:
                            logger.warning("No member selected for removal")
                            st.warning("Please select a member email to remove.")
                else:
                    logger.info(f"No members with emails found in group {selected_group_name_manage}")
                    st.info("No members with emails found in this group to remove.")
            else:
                logger.info(f"No members available in group {selected_group_name_manage}")
                st.info("No members available in this group to remove.")

        else: # No group selected in Manage tab
            st.info("Please select a group above to manage its members.")

# Call the main function to execute the page
main()
