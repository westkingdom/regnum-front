import streamlit as st
import requests
from utils.config import api_url
import pandas as pd
import re

def get_master_group_list():
    """Fetch the master group list"""
    response = requests.get(f"{api_url}/groups/master/")
    if response.status_code == 200:
        return response.json()
    return None

def get_officer_types():
    """Fetch the officer types"""
    response = requests.get(f"{api_url}/officers/")
    if response.status_code == 200:
        return response.json()
    return None

# Set page title
st.title("📜 Regnum Management")

# Create container for form
form_container = st.container()

with form_container:
    st.subheader("Select Area and Office")
    
    # Create columns for area and office selection
    col1, col2 = st.columns(2)
    
    # Fetch master group list for areas
    with st.spinner("Loading areas..."):
        areas_data = get_master_group_list()
    
    # Initialize the areas list
    areas = []
    
    # Process areas data if available
    if areas_data:
        # Extract areas from master group list
        # The actual structure may vary - adjust according to your API response
        for group in areas_data:
            if "type" in group and group["type"] == "area":
                areas.append(group["name"])
    else:
        st.error("Failed to load areas. Please check API connection.")
    
    # Area selection dropdown
    with col1:
        selected_area = st.selectbox(
            "Select Area",
            options=areas if areas else ["No areas available"],
            disabled=not areas,
            key="area_selection"
        )
    
    # Fetch officer types
    with st.spinner("Loading officer types..."):
        officer_data = get_officer_types()
    
    # Initialize officer types
    officer_types = []
    
    # Process officer data if available
    if officer_data:
        # Extract officer types from API response
        # Adjust according to your API response structure
        officer_types = officer_data.get("types", [])
    else:
        st.error("Failed to load officer types. Please check API connection.")
    
    # Officer type selection dropdown
    with col2:
        selected_officer = st.selectbox(
            "Select Office Type",
            options=officer_types if officer_types else ["No office types available"],
            disabled=not officer_types,
            key="officer_selection"
        )
    
    # Display selections
    if areas and officer_types:
        st.success(f"You selected: {selected_area} - {selected_officer}")
        
        # Add action button
        if st.button("View Officers"):
            st.session_state.area = selected_area
            st.session_state.officer = selected_officer
            st.write(f"Fetching officers for {selected_area} - {selected_officer}...")
            
            # Here you would typically fetch and display officers for the selected area and type
            # This is a placeholder for that functionality
            st.info("Officer data would be displayed here")
            
            # Example display table (replace with actual data)
            sample_data = {
                "Name": ["John Doe", "Jane Smith"],
                "Email": ["john@westkingdom.org", "jane@westkingdom.org"],
                "Start Date": ["2023-01-15", "2022-11-01"],
                "End Date": ["2024-01-14", "2023-10-31"]
            }
            
            st.dataframe(
                pd.DataFrame(sample_data),
                use_container_width=True,
                hide_index=True
            )

# Add form for updating officer information
with st.expander("Update Officer Information"):
    if "area" in st.session_state and "officer" in st.session_state:
        st.subheader(f"Update {st.session_state.officer} for {st.session_state.area}")
        
        with st.form("officer_update_form"):
            st.text_input("Officer Name")
            st.text_input("Officer Email", placeholder="user@westkingdom.org")
            col1, col2 = st.columns(2)
            with col1:
                st.date_input("Start Date")
            with col2:
                st.date_input("End Date")
            
            st.text_area("Comments")
            
            if st.form_submit_button("Update Officer"):
                st.success("Officer information updated!")
    else:
        st.info("Select an area and officer type above to update information")
