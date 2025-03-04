import streamlit as st
import pandas as pd
import json
import os
from utils.pdata import locations_data  # Import locations_data directly

# Helper function to extract group name from email
def extract_group_name(email):
    """Extract group name from email (part before the '-')"""
    if isinstance(email, str) and '-' in email:
        return email.split('-')[0].lower()
    return ""

# File path for group mapping data
group_map_file = 'utils/group_map.json'

# Initialize group_map_df outside the try-except block
group_map_df = pd.DataFrame(columns=["group", "officer"])

# Check if file exists
if not os.path.exists(group_map_file):
    st.warning(f"File not found: {group_map_file}")
    
    # Option to create sample data
    if st.button("Create Sample Group Map File"):
        # Sample data structure
        sample_data = [
            {"name": "Altavia", "officer": ["Seneschal", "Herald", "Knight Marshal", "Exchequer"]},
            {"name": "Calafia", "officer": ["Seneschal", "Herald", "Knight Marshal", "Exchequer", "Chronicler"]},
            {"name": "Dreiburgen", "officer": ["Seneschal", "Herald", "Exchequer"]}
        ]
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(group_map_file), exist_ok=True)
            
            # Write sample data to file
            with open(group_map_file, 'w') as f:
                json.dump(sample_data, f, indent=2)
                
            st.success(f"Created sample file at {group_map_file}")
            # Reload the page to use the new file
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Failed to create sample file: {str(e)}")
else:
    # Try to load the file
    try:
        with open(group_map_file, 'r') as f:
            file_content = f.read()
            
            # Check if file is empty
            if not file_content.strip():
                st.warning(f"File is empty: {group_map_file}")
            else:
                try:
                    group_map_data = json.loads(file_content)
                    
                    # Convert to DataFrame for easier lookup
                    group_map_rows = []
                    if isinstance(group_map_data, list):
                        # If format is [{"type": "event"}, {"type": "officer"}, ...]
                        for group in group_map_data:
                            if isinstance(group, dict) and "type" in group:
                                group_type = group["type"]
                                group_map_rows.append({"group": group_type, "officer": group_type})  # Use type for both group and officer
                            else:
                                st.warning(f"Expected a dictionary with 'type', got {type(group)}")
                    else:
                        st.error(f"Unexpected format in {group_map_file}: Expected a list, got {type(group_map_data)}")
                    group_map_df = pd.DataFrame(group_map_rows)
                except json.JSONDecodeError as e:
                    st.error(f"Invalid JSON in {group_map_file}: {str(e)}")
    except Exception as e:
        st.warning(f"Error loading group mapping data: {str(e)}")

# Show the group_map DataFrame
if group_map_df.empty:
    st.error("Group mapping data is empty - no officers will be available for selection")
else:
    st.write(f"Loaded {len(group_map_df)} officer mappings for {group_map_df['group'].nunique()} groups")
    #st.dataframe(group_map_df, use_container_width=True)

# Set page title
st.title("📜 Regnum Management")

# Create container for form
form_container = st.container()

with form_container:
    st.subheader("Select Principality")

    # Get top-level keys from locations_data and add Kingdom option
    principalities = ["Kingdom"] + list(locations_data.keys())
    
    # First select box - Principality selection
    selected_principality = st.selectbox(
        "Select Principality",
        options=principalities,
        key="principality_selection"
    )
    
    # Store the selection in session state to persist across reruns
    if selected_principality:
        st.session_state.selected_principality = selected_principality
        
        # If Kingdom is selected, clear any previous group selection
        if selected_principality == "Kingdom":
            if 'selected_group' in st.session_state:
                del st.session_state.selected_group
    
    # Check if a principality is selected
    if 'selected_principality' in st.session_state:
        # Special handling for Kingdom selection
        if st.session_state.selected_principality == "Kingdom":
            # Display Kingdom-wide information
            st.success(f"You selected: {st.session_state.selected_principality}")
            st.info("Kingdom-wide view shows consolidated information across all principalities.")
            
            # Here you would display Kingdom-wide statistics or information
            st.subheader("Kingdom Overview")
            
            # Count total principalities
            num_principalities = len(locations_data.keys())
            st.write(f"Total Principalities: {num_principalities}")
            
            # You could add other Kingdom-level metrics here
        
        # Regular principality handling
        else:
            principality_data = locations_data[st.session_state.selected_principality]
            
            # Handle different data structures
            if isinstance(principality_data, dict):
                # If principality_data is a dictionary, use its keys as group types
                group_types = list(principality_data.keys())
            elif isinstance(principality_data, list):
                # If principality_data is a list, extract group types from items
                if all(isinstance(item, dict) for item in principality_data):
                    # If items are dictionaries, try to get 'office' or 'type' key
                    if principality_data and 'office' in principality_data[0]:
                        group_types = sorted(set(item['office'] for item in principality_data))
                    elif principality_data and 'type' in principality_data[0]:
                        group_types = sorted(set(item['type'] for item in principality_data))
                    else:
                        # Show first item keys for debugging
                        st.write("Available keys in data:", list(principality_data[0].keys()) if principality_data else [])
                        group_types = ["Unknown Group Type"]
                else:
                    # If items are not dictionaries, use the list itself
                    group_types = principality_data
            else:
                st.error(f"Unexpected data type for {selected_principality}: {type(principality_data)}")
                group_types = ["Error loading groups"]
            
            # Second select box - Group types
            selected_group = st.selectbox(
                f"Select Group in {st.session_state.selected_principality}",
                options=group_types,
                key="group_selection"
            )
            
            # Store the group selection in session state
            if selected_group:
                st.session_state.selected_group = selected_group
                
                # Display the selected information
                st.success(f"You selected: {st.session_state.selected_principality} - {selected_group}")
                
                # Look up officers for the selected group in the group_map DataFrame
                if not group_map_df.empty:
                    # Get the lowercase version of the selected group
                    selected_group_lower = selected_group.lower()

                    # Try direct match first
                    direct_match = group_map_df[group_map_df["group"].str.lower() == selected_group_lower]

                    # If no direct match, try matching by email prefix
                    if direct_match.empty:
                        # Extract group names from emails in the dataframe
                        if "group" in group_map_df.columns:
                            group_map_df["extracted_group"] = group_map_df["group"].apply(extract_group_name)
                            # Filter by the extracted group name
                            filtered_officers = group_map_df[group_map_df["extracted_group"] == selected_group_lower]["officer"].tolist()
                        else:
                            st.error("Group column not found in group_map_df")
                            filtered_officers = []
                    else:
                        filtered_officers = direct_match["officer"].tolist()
                    if filtered_officers:
                        # Create a select box for officers
                        selected_officer = st.selectbox(
                            "Select Officer Type",
                            options=filtered_officers,
                            key="officer_selection"
                        )

                        # Store the selected officer in session state
                        if selected_officer:
                            st.session_state.selected_officer = selected_officer
                            st.success(f"You selected officer type: {selected_officer}")
                    else:
                        st.info(f"No officers found for group: {selected_group}")
                        # Debug information
                        st.write("Available groups in mapping:", group_map_df["group"].unique())

                # Display group data based on the data structure
                if isinstance(principality_data, dict) and selected_group in principality_data:
                    # Dictionary structure
                    group_data = principality_data[selected_group]

                    # Check if we have group data
                    if group_data:
                        st.subheader(f"Current {selected_group} Members")

                        # Convert to DataFrame for display
                        if isinstance(group_data, list):
                            # If it's a list of members
                            if all(isinstance(member, dict) for member in group_data):
                                df = pd.DataFrame(group_data)
                                st.dataframe(df, use_container_width=True, hide_index=True)
                            else:
                                # Simple list
                                st.write(", ".join(str(item) for item in group_data))
                        elif isinstance(group_data, dict):
                            # If it's a dictionary of group data
                            df = pd.DataFrame([group_data])
                            st.dataframe(df, use_container_width=True, hide_index=True)
                        else:
                            # Just display as is
                            st.write(group_data)
                    else:
                        st.info(f"No {selected_group} members found for {st.session_state.selected_principality}")
                elif isinstance(principality_data, list):
                    # List structure
                    group_data = []

                    for item in principality_data:
                        if isinstance(item, dict):
                            # If the item is a dictionary, check for matching fields
                            if (('officer' in item and item['officer'] == selected_group) or  # Note: Changed to 'officer'
                                    ('type' in item and item['type'] == selected_group) or
                                    ('group' in item and item['group'] == selected_group)):
                                group_data.append(item)
                        elif isinstance(item, str) and item == selected_group:
                            # If the item is a string and matches the selected group
                            group_data.append({"name": item})

                    if group_data:
                        st.subheader(f"Current {selected_group} Members")
                        df = pd.DataFrame(group_data)
                        st.dataframe(df, use_container_width=True, hide_index=True)
                    else:
                        st.info(f"No {selected_group} members found for {st.session_state.selected_principality}")
                else:
                    st.error(f"Unexpected data structure for {selected_group} in {st.session_state.selected_principality}")

                # Add action button for updating
                if st.button("Update Members"):
                    st.session_state.update_mode = True

# Add form for updating member information
if st.session_state.get('update_mode', False):
    with st.expander("Update Member Information", expanded=True):
        st.subheader(f"Update {st.session_state.get('selected_group')} for {st.session_state.get('selected_principality')}")

        with st.form("member_update_form"):
            st.text_input("Member Name")
            st.text_input("Member Email", placeholder="user@westkingdom.org")
            col1, col2 = st.columns(2)
            with col1:
                st.date_input("Start Date")
            with col2:
                st.date_input("End Date")

            # Use selected officer in form if available
            if 'selected_officer' in st.session_state:
                officer_value = st.session_state.selected_officer
            else:
                officer_value = ""

            st.text_input("Officer Type", value=officer_value)
            st.text_area("Comments")

            if st.form_submit_button("Update Member"):
                st.success("Member information updated!")
                st.session_state.update_mode = False