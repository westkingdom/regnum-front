import streamlit as st
import pandas as pd
import json
import re
import os
from utils.pdata import locations_data
from utils.queries import get_group_members, is_valid_email

group_map_file = 'utils/group_map_simplified.json'

@st.cache_data
def load_and_process_data(group_map_file):
    """Loads and processes the simplified JSON file containing group data."""
    try:
        # Load the JSON file
        with open(group_map_file, 'r') as f:
            group_data = json.load(f)
        
        # Convert to DataFrame
        group_map_df = pd.DataFrame(group_data)
        
        # Ensure required columns exist
        required_columns = ['email', 'name', 'type']
        for col in required_columns:
            if col not in group_map_df.columns:
                if col == 'type':
                    # Infer type from email if not present
                    group_map_df['type'] = group_map_df['email'].apply(
                        lambda email: 'officer' if any(keyword in email.lower() for keyword in [
                            "-seneschal", "-marshal", "-archer", "-exchequer", 
                            "-herald", "-chronicler", "-chatelaine", "-webminister",
                            "-artssciences", "-baron", "-constable", "-rapier"
                        ]) else 'group'
                    )
                else:
                    # Add empty column if missing
                    group_map_df[col] = ""
        
        # Normalize text fields (remove extra whitespace, etc.)
        if 'name' in group_map_df.columns:
            group_map_df['name'] = group_map_df['name'].str.strip()
        
        return group_map_df
    
    except FileNotFoundError:
        st.error(f"File not found: {group_map_file}")
        # Return an empty DataFrame with required columns
        return pd.DataFrame(columns=['email', 'name', 'type'])
    
    except json.JSONDecodeError:
        st.error(f"Invalid JSON format in: {group_map_file}")
        # Return an empty DataFrame with required columns
        return pd.DataFrame(columns=['email', 'name', 'type'])
    
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        # Return an empty DataFrame with required columns
        return pd.DataFrame(columns=['email', 'name', 'type'])

group_map_df = load_and_process_data(group_map_file)

# Streamlit UI
st.title("📜 Regnum Management")
st.title("Kingdom/Principality Data Viewer")

# Create a select box with the keys from locations_data
selected_location = st.selectbox(
    "Select a Kingdom or Principality:",
    options=list(locations_data.keys()),
    index=0,
    key="location_selection"
)

# Filter group_map_df based on selected location and type
if selected_location:
    # Filter by location name (fuzzy matching)
    location_groups = group_map_df[group_map_df['name'].str.contains(selected_location, case=False, na=False)]

    # Filter by type (only 'officer')
    officer_groups = location_groups[location_groups['type'] == 'officer']

    # Load the officer names into a select list
    selected_officer = st.selectbox(
        f"Select an officer for {selected_location}:",
        options=officer_groups['name'].tolist(),
        key="officer_selection"
    )

    if selected_officer:
        # Get the officer's email
        selected_officer_row = officer_groups[officer_groups['name'] == selected_officer]
        selected_officer_email = selected_officer_row['email'].values[0]
        st.write(f"You selected officer: {selected_officer} ({selected_officer_email})")

        # Get the group_id from group_map_df
        group_id = selected_officer_email

        # Get the group members
        members_data = get_group_members(group_id)

        # Display the group members in a datatable
        if members_data and 'members' in members_data:
            members_df = pd.DataFrame(members_data['members'])
            st.subheader(f"Members of {selected_officer}:")
            st.dataframe(members_df)
        else:
            st.info(f"No members found for {selected_officer}.")

        # Add New Member Form
        with st.form(key='new_member_form'):
            st.subheader(f"Add New Member to {selected_officer}")

            officer_title = st.text_input("Officer Title", placeholder="Officer Muckity Muck")
            sca_name = st.text_input("SCA Name", placeholder="Stephan of Pembroke")
            mundane_name = st.text_input("Mundane Name", placeholder="Jim Bob MacGillicuty")
            sca_membership_number = st.number_input("SCA Membership Number", min_value=0, step=1, placeholder="1123581")

            st.write("#### Address Information")
            street_address = st.text_input("Street Address", placeholder="1 Infinite Loop")
            city = st.text_input("City", placeholder="Cupertino")
            state = st.text_input("State", placeholder="CA")
            zip_code = st.text_input("Zip Code", placeholder="95014")
            country = st.text_input("Country", placeholder="USA")

            westkingdom_email = st.text_input("Westkingdom Email Address", placeholder="man.bear.pig@westkingdom.org")
            if westkingdom_email:
                if not is_valid_email(westkingdom_email):
                    st.warning("Invalid Westkingdom email address. Must end with @westkingdom.org")

            contact_phone_number = st.text_input("Contact Phone Number (e.g., 123-456-7890)", placeholder="510-867-5309")

            effective_date = st.date_input("Effective Date", format="MM-DD-YYYY")
            end_date = st.date_input("End Date", format="MM-DD-YYYY")

            warranted_position = st.checkbox("Warranted Position", help="Warrants are required for all Major officers.")

            submit_button = st.form_submit_button(label='Add Member')

            if submit_button:
                # Process the form data here
                if is_valid_email(westkingdom_email):
                    st.success(f"New member {sca_name} added to {selected_officer}!")
                    # You would typically send this data to your backend or database
                else:
                    st.error("Please provide a valid Westkingdom email address.")
