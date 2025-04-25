import streamlit as st
import pandas as pd
import json
from datetime import date
# Make sure add_member_to_group is imported
from utils.queries import get_group_members, is_valid_email, add_member_to_group
from utils.email import send_registration_email

# --- Data Loading Function ---
def load_group_data(file_path: str = "utils/group_map_simplified.json") -> tuple[list, dict]:
    """Loads group data from a JSON file and returns options and name-to-ID map."""
    try:
        df_groups = pd.read_json(file_path)
        group_name_to_id = pd.Series(df_groups.id.values, index=df_groups.name).to_dict()
        group_options = df_groups['name'].tolist()
        return group_options, group_name_to_id
    except FileNotFoundError:
        st.error(f"Error: {file_path} not found. Please ensure the file exists.")
    except ValueError as e:
        st.error(f"Error reading or parsing JSON file ({file_path}): {e}")
    except KeyError:
        st.error(f"Error: Column 'name' or 'id' not found in {file_path}. Check JSON structure.")
    except Exception as e:
        st.error(f"An unexpected error occurred while loading data from {file_path}: {e}")
    return [], {} # Return empty structures on error

# --- Member Display Function ---
def display_group_members(selected_group_id: str, selected_group_name: str) -> bool:
    """Fetches and displays members for the selected group. Returns True if successful, False on API error."""
    try:
        members = get_group_members(selected_group_id)
        if members is not None:
            if members:
                st.subheader("Group Members:")
                member_df = pd.DataFrame(members)
                columns_to_display = [col for col in ['name', 'email'] if col in member_df.columns]
                if columns_to_display:
                    st.table(member_df[columns_to_display])
                else:
                    st.dataframe(member_df) # Fallback if columns missing
            else:
                st.info("This group has no members.")
            return True # Success (members fetched or group is empty)
        else:
            st.error(f"Failed to fetch members for group '{selected_group_name}'. The API might be down or the group ID is invalid.")
            return False # API error
    except Exception as e:
        st.error(f"An error occurred while fetching members: {e}")
        return False # Other error

# --- Form Display and Data Collection Function ---
def display_add_member_form(selected_group_name: str) -> tuple[bool, dict | None]:
    """Displays the 'Add New Member' form and returns submit status and data."""
    with st.form(key='new_member_form'):
        st.subheader(f"Add New Member to {selected_group_name}")

        sca_name = st.text_input("SCA Name", placeholder="Stephan of Pembroke")
        mundane_name = st.text_input("Mundane Name", placeholder="Jim Bob MacGillicuty")
        sca_membership_number = st.number_input("SCA Membership Number", value=None, min_value=0, step=1, placeholder="1123581")

        st.write("#### Address Information")
        street_address = st.text_input("Street Address", placeholder="1 Infinite Loop")
        city = st.text_input("City", placeholder="Cupertino")
        state = st.text_input("State", placeholder="CA")
        zip_code = st.text_input("Zip Code", placeholder="95014")
        country = st.text_input("Country", placeholder="USA")

        westkingdom_email = st.text_input("Westkingdom Email Address", placeholder="man.bear.pig@westkingdom.org")
        contact_phone_number = st.text_input("Contact Phone Number (e.g., 123-456-7890)", placeholder="510-867-5309")

        effective_date = st.date_input("Effective Date", value=None, format="YYYY-MM-DD")
        end_date = st.date_input("End Date", value=None, format="YYYY-MM-DD")

        submit_button = st.form_submit_button(label='Add Member')

        form_data = None
        is_valid = True # Flag for validation status

        if submit_button:
            # Perform validation within the form context
            if not westkingdom_email:
                 st.error("Westkingdom email address is required.")
                 is_valid = False
            elif not is_valid_email(westkingdom_email):
                 st.error("Please provide a valid Westkingdom email address ending with @westkingdom.org.")
                 is_valid = False

            if not sca_name:
                 st.error("SCA Name is required.")
                 is_valid = False

            if is_valid:
                # Collect data only if validation passes
                form_data = {
                    'sca_name': sca_name,
                    'mundane_name': mundane_name,
                    'sca_membership_number': sca_membership_number if sca_membership_number is not None else 'N/A',
                    'street_address': street_address,
                    'city': city,
                    'state': state,
                    'zip_code': zip_code,
                    'country': country,
                    'westkingdom_email': westkingdom_email,
                    'contact_phone_number': contact_phone_number,
                    'effective_date': str(effective_date) if effective_date else 'N/A',
                    'end_date': str(end_date) if end_date else 'N/A'
                }
                return True, form_data # Return submitted status and data
            else:
                return True, None # Return submitted status but no data due to validation failure

        return False, None # Return not submitted

# --- Form Submission Handling Function ---
# Updated to accept selected_group_id
def handle_form_submission(form_data: dict, selected_group_name: str, selected_group_id: str):
    """Handles the submission logic: sends email and adds member to the group."""
    st.info("Submitting registration...")
    email_sent = send_registration_email(form_data, selected_group_name)

    if email_sent:
        st.success(f"Registration notification sent for {form_data['sca_name']}.")

        # --- Add member to group ---
        st.info(f"Adding {form_data['westkingdom_email']} to group '{selected_group_name}'...")
        member_added = add_member_to_group(selected_group_id, form_data['westkingdom_email'])

        if member_added:
            st.success(f"Successfully added {form_data['westkingdom_email']} to the group.")
            # Rerun to refresh the member list displayed above the form
            st.rerun()
        else:
            st.error(f"Failed to add {form_data['westkingdom_email']} to the group '{selected_group_name}'. Please add them manually via the Group Management page or contact support.")
            # Don't rerun here, as the user might want to see the error.

    else:
        st.error("Failed to send registration notification email. Member was NOT added to the group. Please contact the administrator.")

# --- Main Streamlit App Logic ---
st.set_page_config(page_title="Regnum")
st.title("Regnum")

# Load data
group_options, group_name_to_id = load_group_data()

# Display selection only if data loaded successfully
if group_options:
    selected_group_name = st.selectbox(
        "Group Selection",
        options=group_options,
        index=None,
        placeholder="Select a group..."
    )

    if selected_group_name:
        st.write(f"You selected: {selected_group_name}")
        selected_group_id = group_name_to_id.get(selected_group_name)

        if selected_group_id:
            # Display members and check if successful before showing form
            members_displayed_successfully = display_group_members(selected_group_id, selected_group_name)

            if members_displayed_successfully:
                st.divider()
                # Display the form and get submission status/data
                submitted, form_data = display_add_member_form(selected_group_name)

                # Handle submission if the form was submitted and data is valid
                if submitted and form_data:
                    # Pass selected_group_id to the handler
                    handle_form_submission(form_data, selected_group_name, selected_group_id)
                # Note: Validation errors are displayed within display_add_member_form

        else:
            # This case should ideally not happen if the selectbox options are derived correctly
            st.error("Could not find the ID for the selected group.")
# else:
    # Error messages handled within load_group_data()

