import streamlit as st
import pandas as pd
import json
from datetime import date
from typing import Union, Optional, Tuple, List, Dict, Any # Import necessary types
# Make sure add_member_to_group is imported
from utils.queries import get_group_members, is_valid_email, add_member_to_group
from utils.email import send_registration_email
from utils.logger import app_logger as logger
import os
import sys

# --- Data Loading Function ---
# Note: Type hint was tuple[list, dict], updated to standard Tuple[List, Dict]
def load_group_data(file_path: str = "utils/group_map_simplified.json") -> Tuple[List[str], Dict[str, str]]:
    """
    Loads group data (names and IDs) from a specified JSON file.

    Reads the JSON file, processes it using pandas, and extracts group names
    into a list and a name-to-ID mapping into a dictionary. Handles file errors
    and data structure issues, displaying errors using st.error.

    Args:
        file_path: The relative path to the JSON file containing group data.
                   Defaults to "utils/group_map_simplified.json".

    Returns:
        A tuple containing:
        - A list of group name strings.
        - A dictionary mapping group names (str) to group IDs (str).
        Returns ([], {}) if any error occurs during loading or processing.
    """
    group_options = []
    group_name_to_id = {}
    try:
        df_groups = pd.read_json(file_path)
        # Basic validation for expected columns
        if 'id' not in df_groups.columns or 'name' not in df_groups.columns:
             raise KeyError("Required columns 'id' or 'name' not found in JSON data.")
        group_name_to_id = pd.Series(df_groups.id.values, index=df_groups.name).to_dict()
        group_options = df_groups['name'].tolist()
    except FileNotFoundError:
        st.error(f"Error: Group data file ({file_path}) not found. Please ensure the file exists.")
    except pd.errors.EmptyDataError:
        st.error(f"Error: Group data file ({file_path}) is empty or not valid JSON.")
    except ValueError as e: # Catch JSON decoding errors
        st.error(f"Error reading or parsing JSON file ({file_path}): {e}")
    except KeyError as e: # Catch missing 'name' or 'id' columns after loading
        st.error(f"Error processing group data from {file_path}: {e}")
    except Exception as e: # Catch other unexpected errors
        st.error(f"An unexpected error occurred while loading data from {file_path}: {e}")

    return group_options, group_name_to_id


# --- Member Display Function ---
def display_group_members(selected_group_id: str, selected_group_name: str) -> bool:
    """
    Fetches and displays members for a selected group using a Streamlit DataFrame.

    Calls the `get_group_members` API utility function. If successful, formats
    the member list into a pandas DataFrame and displays relevant columns
    (email, role, status, type). Handles API errors, empty member lists,
    and DataFrame processing errors gracefully, displaying informative messages or warnings.

    Args:
        selected_group_id: The ID of the group whose members are to be displayed.
        selected_group_name: The name of the group (used for error messages).

    Returns:
        True if members were successfully fetched and processed (even if the list is empty),
        False if there was an API error preventing fetching members or an unexpected exception.
    """
    try:
        # API response is expected to be like: {"members": [ {member_data}, ... ]}
        st.subheader(f"Members in {selected_group_name}") # Add subheader before fetch
        logger.info(f"Fetching members for group: {selected_group_name} (ID: {selected_group_id})")
        api_response = get_group_members(selected_group_id)

        if api_response is not None:
            # Extract the actual list of members from the response dictionary
            # Use .get() for safety, defaulting to an empty list if 'members' key is missing
            members_list = api_response.get('members', [])

            if members_list: # Check if the extracted list is not empty
                # st.subheader("Group Members:") # Moved above
                try:
                    # Attempt to create DataFrame from the extracted list
                    member_df = pd.DataFrame(members_list)

                    # Define desired columns based on the keys found in the nested objects
                    all_possible_columns = ['email', 'role', 'status', 'type']
                    # Filter to only include columns actually present in the DataFrame
                    columns_to_display = [col for col in all_possible_columns if col in member_df.columns]

                    if columns_to_display:
                        # Display using st.dataframe for better interactivity and formatting
                        # Hide the index column for cleaner presentation
                        st.dataframe(member_df[columns_to_display], hide_index=True, use_container_width=True) # Add container width
                    elif not member_df.empty:
                        # Fallback if NO desired columns are present but DF is not empty
                        logger.warning(f"Member data found for {selected_group_name}, but expected columns are missing")
                        st.warning("Member data found, but expected columns ('email', 'role', etc.) are missing. Displaying all available data:")
                        st.dataframe(member_df, hide_index=True, use_container_width=True)
                    else:
                        # Should not be hit if members_list was checked, but as a safeguard
                        logger.info(f"Group {selected_group_name} has empty DataFrame for members")
                        st.info("No member data to display (DataFrame empty).") # Should be caught by outer 'if members_list'

                except Exception as df_error:
                    logger.error(f"Error processing member data into a table: {str(df_error)}")
                    st.error(f"Error processing member data into a table: {df_error}")
                    st.warning("Displaying raw member data instead (from exception handler):")
                    # Display the original API response if DataFrame fails
                    st.json(api_response) # Display raw data on error

            else: # members_list is empty
                logger.info(f"Group {selected_group_name} has no members")
                st.info(f"The group '{selected_group_name}' currently has no members.")
            return True # Success (members fetched/processed or group is empty)
        else: # api_response is None
            logger.warning(f"Failed to fetch members for {selected_group_name}")
            st.error(f"Failed to fetch members for group '{selected_group_name}'. The API might be down or the group ID is invalid.")
            return False # API error

    except Exception as e: # Catch any other unexpected errors
        logger.error(f"Error fetching members for {selected_group_name}: {str(e)}")
        st.error(f"An unexpected error occurred while fetching or displaying members for '{selected_group_name}': {e}")
        return False # Other error


# --- Form Display and Data Collection Function ---
def display_add_member_form(selected_group_name: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Displays the 'Add New Member' Streamlit form and handles its submission.

    Uses `st.form` to collect member details (SCA name, email, address, etc.).
    Upon submission, it validates required fields (SCA name, West Kingdom email).
    If validation passes, it collects form data into a dictionary.

    Args:
        selected_group_name: The name of the group to which the member will be added
                             (used in the form's subheader).

    Returns:
        A tuple containing:
        - bool: True if the form was submitted in this run, False otherwise.
        - Optional[dict]: A dictionary containing the validated form data if submission
                          was successful and valid. None if the form was not submitted or
                          if validation failed.
    """
    with st.form(key='new_member_form'):
        st.subheader(f"Add New Member to {selected_group_name}")

        # Input fields for member details
        sca_name = st.text_input("SCA Name*", placeholder="Stephan of Pembroke", help="Required")
        mundane_name = st.text_input("Mundane Name", placeholder="Jim Bob MacGillicuty")
        sca_membership_number = st.number_input("SCA Membership Number", value=None, min_value=0, step=1, placeholder="1123581")

        st.write("#### Address Information")
        street_address = st.text_input("Street Address", placeholder="1 Infinite Loop")
        city = st.text_input("City", placeholder="Cupertino")
        state = st.text_input("State", placeholder="CA")
        zip_code = st.text_input("Zip Code", placeholder="95014")
        country = st.text_input("Country", placeholder="USA")

        westkingdom_email = st.text_input("Westkingdom Email Address*", placeholder="user@westkingdom.org", help="Required, must end in @westkingdom.org")
        contact_phone_number = st.text_input("Contact Phone Number (e.g., 123-456-7890)", placeholder="510-867-5309")

        effective_date = st.date_input("Effective Date", value=None, format="YYYY-MM-DD") # Consider default to today? value=date.today()
        end_date = st.date_input("End Date (Optional)", value=None, format="YYYY-MM-DD") # Optional end date

        # Submit button for the form
        submit_button = st.form_submit_button(label='Add Member')

        form_data = None
        was_submitted = False # Flag if form was submitted in this run

        if submit_button:
            was_submitted = True # Mark as submitted regardless of validation
            is_valid = True # Assume valid initially
            # Perform validation within the form context
            if not sca_name:
                 logger.warning("Empty SCA name submitted")
                 st.error("SCA Name is required.")
                 is_valid = False
            if not westkingdom_email:
                 logger.warning("Empty email submitted")
                 st.error("Westkingdom email address is required.")
                 is_valid = False
            elif not is_valid_email(westkingdom_email): # Use utility function
                 logger.warning(f"Invalid email format submitted: {westkingdom_email}")
                 st.error("Please provide a valid email address ending with @westkingdom.org.")
                 is_valid = False

            # Add more validation as needed (e.g., zip code format)

            if is_valid:
                # Collect data only if validation passes
                form_data = {
                    'sca_name': sca_name,
                    'mundane_name': mundane_name if mundane_name else 'N/A',
                    'sca_membership_number': sca_membership_number if sca_membership_number is not None else 'N/A',
                    'street_address': street_address if street_address else 'N/A',
                    'city': city if city else 'N/A',
                    'state': state if state else 'N/A',
                    'zip_code': zip_code if zip_code else 'N/A',
                    'country': country if country else 'N/A',
                    'westkingdom_email': westkingdom_email, # Required, so always present
                    'contact_phone_number': contact_phone_number if contact_phone_number else 'N/A',
                    'effective_date': str(effective_date) if effective_date else 'N/A',
                    'end_date': str(end_date) if end_date else 'N/A'
                }
                logger.info(f"Form data collected for {westkingdom_email}")
                # Don't return here yet, let the main logic handle it based on 'was_submitted' and 'form_data'
            # else: Validation errors are displayed above

        # Return submission status and the data (None if invalid or not submitted)
        return was_submitted, form_data


# --- Form Submission Handling Function ---
def handle_form_submission(form_data: Dict[str, Any], selected_group_name: str, selected_group_id: str) -> None:
    """
    Handles the logic after the 'Add Member' form is successfully submitted and validated.

    This function takes the validated form data, sends a registration notification email
    using `send_registration_email`, and then attempts to add the member to the
    specified group using the `add_member_to_group` API utility function.
    It displays success or error messages using Streamlit and triggers `st.rerun()`
    on successful addition to refresh the member list.

    Args:
        form_data: The dictionary containing validated data from the submitted form.
        selected_group_name: The name of the group the member is being added to.
        selected_group_id: The ID of the group the member is being added to.

    Returns:
        None. Displays results and potentially reruns the Streamlit app.
    """
    st.info("Processing registration...") # Use info for processing steps
    logger.info(f"Processing registration for {form_data.get('sca_name', 'N/A')} to group {selected_group_name}")

    # 1. Send notification email
    email_sent = send_registration_email(form_data, selected_group_name)

    if email_sent:
        st.success(f"Registration notification sent for {form_data.get('sca_name', 'N/A')}.") # Use .get for safety
        logger.info(f"Registration email sent for {form_data.get('sca_name', 'N/A')}")

        # 2. Add member to the actual group via API
        st.info(f"Adding {form_data['westkingdom_email']} to group '{selected_group_name}'...") # Use quotes for clarity
        logger.info(f"Attempting to add {form_data['westkingdom_email']} to group {selected_group_name}")
        member_added = add_member_to_group(selected_group_id, form_data['westkingdom_email'])

        if member_added:
            logger.info(f"Successfully added {form_data['westkingdom_email']} to {selected_group_name}")
            st.success(f"Successfully added {form_data['westkingdom_email']} to the group '{selected_group_name}'.")
            # Rerun to refresh the member list displayed above the form
            st.rerun()
        else:
            # Error message already shown by add_member_to_group if API fails
            logger.error(f"Failed to add {form_data['westkingdom_email']} to group {selected_group_name}")
            st.error(f"Failed to add {form_data['westkingdom_email']} to the group '{selected_group_name}'. The user might already be in the group, or an API error occurred. Please check logs or add manually if needed.")
            # Don't rerun here, let the user see the error.

    else:
        # Error message should be shown by send_registration_email
        logger.error(f"Failed to send registration email for {form_data.get('sca_name', 'N/A')}")
        st.error("Failed to send registration notification email. Member was NOT added to the group. Please contact the administrator.")


def main():
    """Main application logic for Regnum Data Entry page."""
    logger.info("Accessing Regnum Data Entry page")
    
    # --- Main Streamlit App Logic ---
    st.set_page_config(page_title="Regnum Data Entry") # More specific title
    st.title("Regnum Data Entry") # Match page title

    # --- Load group data ---
    group_options, group_name_to_id = load_group_data()

    # --- Proceed only if groups loaded successfully ---
    if not group_options:
        logger.warning("Failed to load group information")
        st.warning("Could not load group information. Cannot display member management or entry form.")
        # Error message already displayed by load_group_data
        st.stop() # Stop execution if groups aren't loaded
    else:
        # --- Group Selection ---
        selected_group_name = st.selectbox(
            "Select Group to View/Manage Members", # More descriptive label
            options=group_options,
            index=None,
            placeholder="Select a group..."
        )

        # --- Actions for Selected Group ---
        if selected_group_name:
            # st.write(f"Selected Group: {selected_group_name}") # Display name clearly
            selected_group_id = group_name_to_id.get(selected_group_name)

            if selected_group_id:
                # --- Display Members ---
                # Display members and check if successful before showing the form
                # The function itself handles success/error messages
                members_displayed_successfully = display_group_members(selected_group_id, selected_group_name)

                # --- Display Add Member Form ---
                if members_displayed_successfully:
                    st.divider() # Separate member list from the form
                    # Display the form and get submission status/data
                    # The function displays validation errors internally
                    submitted, form_data = display_add_member_form(selected_group_name)

                    # --- Handle Form Submission ---
                    # Handle submission *only* if the form was submitted in this run *and* data is valid (not None)
                    if submitted and form_data:
                        handle_form_submission(form_data, selected_group_name, selected_group_id)
                    elif submitted and not form_data:
                        # Form was submitted but validation failed (errors shown in display_add_member_form)
                        st.warning("Submission failed validation checks. Please correct the errors above.")
                        logger.warning("Form submission failed validation")

            else:
                # This case should ideally not happen if the selectbox options are derived correctly
                logger.error(f"Could not find ID for selected group '{selected_group_name}'")
                st.error(f"Could not find the ID for the selected group '{selected_group_name}'. Data inconsistency?")
        else:
            st.info("Select a group from the dropdown above to view its members or add a new member.")


# Call the main function if script is run directly
if __name__ == "__main__":
    main()

