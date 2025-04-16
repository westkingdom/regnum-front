import requests
from utils.config import api_url
import pandas as pd
import re

def get_all_groups():
    try:
        # Use the simplified JSON file
        df_groups = pd.read_json("utils/group_map_simplified.json")
        # Create a dictionary mapping group names to their IDs for easy lookup
        group_name_to_id = pd.Series(df_groups.id.values, index=df_groups.name).to_dict()
        group_options = df_groups['name'].tolist()
        return group_options, group_name_to_id
    except pd.errors.EmptyDataError:
        st.error("Error: utils/group_map_simplified.json is empty or not formatted correctly.")
        group_options = []
        group_name_to_id = {}
        # Handle the case where the file is empty or not formatted correctly
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
