import streamlit as st
import pandas as pd
import json # Import the json library
from utils.queries import get_group_members, is_valid_email # Import the functions
from utils.email import send_registration_email # Import the email function

# Set page title
st.set_page_config(page_title="Regnum")

st.title("Regnum")

# Load the data from JSON
try:
    # Use the simplified JSON file
    df_groups = pd.read_json("utils/group_map_simplified.json")
    # Create a dictionary mapping group names to their IDs for easy lookup
    group_name_to_id = pd.Series(df_groups.id.values, index=df_groups.name).to_dict()
    group_options = df_groups['name'].tolist()
except FileNotFoundError:
    st.error("Error: utils/group_map_simplified.json not found. Please ensure the simplified file exists.")
    group_options = []
    group_name_to_id = {}
except ValueError as e: # Catch potential JSON decoding errors or structure issues
    st.error(f"Error reading or parsing JSON file: {e}")
    group_options = []
    group_name_to_id = {}
except KeyError:
    st.error("Error: Column 'name' or 'id' not found in the data loaded from utils/group_map_simplified.json. Please check the JSON structure.")
    group_options = []
    group_name_to_id = {}
except Exception as e:
    st.error(f"An unexpected error occurred while loading the data: {e}")
    group_options = []
    group_name_to_id = {}


# Create a searchable dropdown
selected_group_name = st.selectbox(
    "Group Selection",
    options=group_options,
    index=None, # No default selection
    placeholder="Select a group..."
)

# Display the selection and fetch/display members
if selected_group_name:
    st.write(f"You selected: {selected_group_name}")

    # Get the group ID using the name-to-ID mapping
    selected_group_id = group_name_to_id.get(selected_group_name)

    if selected_group_id:
        # Removed the "Fetching members..." message for cleaner output
        # st.write(f"Fetching members for group ID: {selected_group_id}")
        try:
            members = get_group_members(selected_group_id)
            if members is not None:
                if members: # Check if the list is not empty
                    st.subheader("Group Members:")
                    # Create DataFrame
                    member_df = pd.DataFrame(members)
                    # Select and display only relevant columns ('name', 'email')
                    columns_to_display = []
                    if 'name' in member_df.columns:
                        columns_to_display.append('name')
                    if 'email' in member_df.columns:
                        columns_to_display.append('email')

                    if columns_to_display:
                        # Use st.table for a clean, static table display.
                        # This will display the DataFrame content directly, not as JSON.
                        st.table(member_df[columns_to_display])
                    else:
                        # Fallback if expected columns are missing, still uses st.dataframe
                        st.dataframe(member_df)
                else:
                    st.info("This group has no members.")

                # --- Start of Integrated Form ---
                st.divider() # Add a visual separator

                # Add New Member Form
                with st.form(key='new_member_form'):
                    st.subheader(f"Add New Member to {selected_group_name}") # Use selected_group_name

                    # officer_title = st.text_input("Officer Title", placeholder="Officer Muckity Muck") # Removed as it might not be relevant for all groups
                    sca_name = st.text_input("SCA Name", placeholder="Stephan of Pembroke")
                    mundane_name = st.text_input("Mundane Name", placeholder="Jim Bob MacGillicuty")
                    sca_membership_number = st.number_input("SCA Membership Number", value=None, min_value=0, step=1, placeholder="1123581") # Use value=None

                    st.write("#### Address Information")
                    street_address = st.text_input("Street Address", placeholder="1 Infinite Loop")
                    city = st.text_input("City", placeholder="Cupertino")
                    state = st.text_input("State", placeholder="CA")
                    zip_code = st.text_input("Zip Code", placeholder="95014")
                    country = st.text_input("Country", placeholder="USA")

                    westkingdom_email = st.text_input("Westkingdom Email Address", placeholder="man.bear.pig@westkingdom.org")
                    email_valid = True # Assume valid initially
                    if westkingdom_email: # Only validate if an email is entered
                        if not is_valid_email(westkingdom_email):
                            st.warning("Invalid Westkingdom email address format. Must end with @westkingdom.org")
                            email_valid = False # Mark as invalid
                    # else: # Handle case where email is required but not provided
                        # st.warning("Westkingdom email address is required.")
                        # email_valid = False # Or handle required field validation differently

                    contact_phone_number = st.text_input("Contact Phone Number (e.g., 123-456-7890)", placeholder="510-867-5309")

                    effective_date = st.date_input("Effective Date", value=None, format="YYYY-MM-DD") # Use YYYY-MM-DD format
                    end_date = st.date_input("End Date", value=None, format="YYYY-MM-DD") # Use YYYY-MM-DD format

                    # warranted_position = st.checkbox("Warranted Position", help="Warrants are required for all Major officers.") # Removed as it might not be relevant

                    submit_button = st.form_submit_button(label='Add Member')

                    if submit_button:
                        # Basic validation check
                        if not westkingdom_email:
                             st.error("Westkingdom email address is required.")
                        elif not email_valid:
                             st.error("Please provide a valid Westkingdom email address ending with @westkingdom.org.")
                        elif not sca_name:
                             st.error("SCA Name is required.")
                        else:
                            # All basic checks passed, gather data
                            form_data = {
                                'sca_name': sca_name,
                                'mundane_name': mundane_name,
                                'sca_membership_number': sca_membership_number if sca_membership_number is not None else 'N/A', # Handle None from number_input
                                'street_address': street_address,
                                'city': city,
                                'state': state,
                                'zip_code': zip_code,
                                'country': country,
                                'westkingdom_email': westkingdom_email,
                                'contact_phone_number': contact_phone_number,
                                'effective_date': str(effective_date) if effective_date else 'N/A', # Convert date to string
                                'end_date': str(end_date) if end_date else 'N/A' # Convert date to string
                            }

                            # Attempt to send the email
                            st.info("Submitting registration...") # Give user feedback
                            email_sent = send_registration_email(form_data, selected_group_name)

                            if email_sent:
                                st.success(f"Registration submitted for {sca_name}. Notification sent.")
                                # Optionally: Clear the form (Streamlit forms clear on successful submit by default)
                                # Optionally: Rerun the query to refresh the member list: st.rerun()
                            else:
                                st.error("Failed to send registration notification email. Please contact the administrator.")

                # --- End of Integrated Form ---

            else:
                st.error(f"Failed to fetch members for group '{selected_group_name}'. The API might be down or the group ID is invalid.")
        except Exception as e:
            st.error(f"An error occurred while fetching members: {e}")
    else:
        # This case should ideally not happen if the selectbox options are derived correctly
        st.error("Could not find the ID for the selected group.")

