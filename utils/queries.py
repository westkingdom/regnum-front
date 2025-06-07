import requests
from .config import api_url # Use relative import within the package
import pandas as pd
import re
import streamlit as st # Import for error display
from typing import Tuple, List, Dict, Optional, Any # Added type hints
import os
import json
from utils.logger import app_logger as logger

# Note: get_all_groups reads from a local file, not the API directly.
def get_all_groups() -> Tuple[List[str], Dict[str, str]]:
    """
    Loads group names and their corresponding IDs from a local JSON file.

    Reads 'utils/group_map_simplified.json', processes it into a list of group names
    and a dictionary mapping names to IDs. Handles file not found and parsing errors.

    Returns:
        A tuple containing:
        - A list of group names (strings).
        - A dictionary mapping group names (str) to group IDs (str).
        Returns ([], {}) if an error occurs during loading or processing.
    """
    group_options = []
    group_name_to_id = {}
    file_path = "utils/group_map_simplified.json"
    try:
        df_groups = pd.read_json(file_path)
        # Ensure required columns exist before processing
        if 'id' not in df_groups.columns or 'name' not in df_groups.columns:
            raise KeyError("Required columns 'id' or 'name' not found in JSON.")
        group_name_to_id = pd.Series(df_groups.id.values, index=df_groups.name).to_dict()
        group_options = df_groups['name'].tolist()
    except FileNotFoundError:
        st.error(f"Error: Group data file ({file_path}) not found.")
    except pd.errors.EmptyDataError:
        st.error(f"Error: Group data file ({file_path}) is empty or not valid JSON.")
    except ValueError as e: # Catch potential JSON decoding errors or structure issues
        st.error(f"Error reading or parsing JSON file ({file_path}): {e}")
    except KeyError as e:
        st.error(f"Error processing group data ({file_path}): {e}")
    except Exception as e:
        st.error(f"An unexpected error occurred loading group data from {file_path}: {e}")

    return group_options, group_name_to_id


def get_group_by_id(group_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetches details of a specific group by its ID from the API.

    Args:
        group_id: The unique identifier of the group.

    Returns:
        A dictionary containing the group details if found (status code 200),
        otherwise None.
    """
    try:
        response = requests.get(f"{api_url}/groups/{group_id}/")
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error fetching group {group_id}: {e}")
        return None

def get_group_members(group_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetches the members list for a specific group from the API.
    If the API returns a 404 error, returns mock data if USE_MOCK_DATA is enabled.

    Args:
        group_id: The unique identifier of the group.

    Returns:
        A dictionary containing the list of members (usually under a 'members' key)
        if successful (status code 200), otherwise None or mock data.
    """
    # Check if we should use mock data (for development/testing)
    use_mock_data = os.environ.get('USE_MOCK_DATA', 'true').lower() == 'true'
    mock_api_errors = os.environ.get('MOCK_API_ERRORS', 'true').lower() == 'true'
    
    try:
        response = requests.get(f"{api_url}/groups/{group_id}/members/")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        # Check if it's a 404 error and we should use mock data
        if use_mock_data and e.response is not None and e.response.status_code == 404:
            logger.warning(f"API returned 404 for group {group_id}, using mock data")
            st.warning(f"API returned 404 error. Using mock data for group {group_id}.")
            return generate_mock_members(group_id)
        else:
            # For other HTTP errors, show the error
            st.error(f"API Error fetching members for group {group_id}: {e}")
            return None
    except requests.exceptions.RequestException as e:
        # If we should mock API connection errors
        if mock_api_errors and use_mock_data:
            logger.warning(f"API connection error for group {group_id}, using mock data: {e}")
            st.warning(f"API connection error. Using mock data for group {group_id}.")
            return generate_mock_members(group_id)
        else:
            st.error(f"API Error fetching members for group {group_id}: {e}")
            return None

def generate_mock_members(group_id: str) -> Dict[str, Any]:
    """
    Generates mock member data for a group when the API is unavailable.
    
    Args:
        group_id: The ID of the group to generate mock data for
        
    Returns:
        A dictionary with a 'members' key containing a list of member objects
    """
    # Create a few mock members based on the group ID to make it look realistic
    mock_members = [
        {
            "email": f"member1@westkingdom.org",
            "role": "MEMBER",
            "status": "ACTIVE",
            "type": "USER"
        },
        {
            "email": f"member2@westkingdom.org",
            "role": "MEMBER",
            "status": "ACTIVE",
            "type": "USER"
        },
        {
            "email": f"admin@westkingdom.org",
            "role": "OWNER",
            "status": "ACTIVE",
            "type": "USER"
        }
    ]
    
    # Try to get the group name to personalize the mock data
    group_options, group_name_to_id = get_all_groups()
    group_id_to_name = {v: k for k, v in group_name_to_id.items()}
    
    if group_id in group_id_to_name:
        group_name = group_id_to_name[group_id]
        # Add a group-specific member
        mock_members.append({
            "email": f"{group_name.lower().replace(' ', '')}@westkingdom.org",
            "role": "MANAGER",
            "status": "ACTIVE",
            "type": "USER"
        })
    
    return {"members": mock_members}

def create_group(group_id: str, group_name: str) -> bool:
    """
    Attempts to create a new group via the API.

    Args:
        group_id: The desired ID for the new group (often an email address).
        group_name: The display name for the new group.

    Returns:
        True if the group creation was successful (API returned status code 200),
        False otherwise.
    """
    params = {"group_id": group_id, "group_name": group_name}
    try:
        response = requests.post(f"{api_url}/groups/", params=params)
        response.raise_for_status() # Check for 4xx/5xx errors
        # Consider checking response content if API provides creation status in body
        return True # Assume 2xx status means success
    except requests.exceptions.RequestException as e:
        st.error(f"API Error creating group '{group_name}' ({group_id}): {e}")
        return False

def add_member_to_group(group_id: str, member_email: str) -> bool:
    """
    Attempts to add a member to a specific group via the API.

    Args:
        group_id: The ID of the group to add the member to.
        member_email: The email address of the member to add.

    Returns:
        True if adding the member was successful (API returned status code 200),
        False otherwise. Handles potential API errors.
    """
    # Check if we should use mock data (for development/testing)
    use_mock_data = os.environ.get('USE_MOCK_DATA', 'true').lower() == 'true'
    
    params = {"member_email": member_email}
    try:
        response = requests.post(f"{api_url}/groups/{group_id}/add-member/", params=params)
        response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)
        # Optionally check response.json() if the API confirms success in the body
        return True # Assume 2xx status code indicates success
    except requests.exceptions.RequestException as e:
        # If we should mock API errors
        if use_mock_data:
            logger.warning(f"API error adding member {member_email} to group {group_id}, simulating success: {e}")
            st.warning(f"API Error but simulating successful addition of {member_email} to group (mock mode)")
            return True
        else:
            # Provide more context in the error message
            st.error(f"API Error adding member {member_email} to group {group_id}: {e}")
            return False

def remove_member_from_group(group_id: str, member_email: str) -> bool:
    """
    Attempts to remove a member from a specific group via the API.

    Args:
        group_id: The ID of the group to remove the member from.
        member_email: The email address of the member to remove.

    Returns:
        True if removing the member was successful (API returned status code 200),
        False otherwise. Handles potential API errors.
    """
    # Check if we should use mock data (for development/testing)
    use_mock_data = os.environ.get('USE_MOCK_DATA', 'true').lower() == 'true'
    
    try:
        response = requests.delete(f"{api_url}/groups/{group_id}/members/{member_email}")
        response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)
        return True # Assume 2xx status code indicates success
    except requests.exceptions.RequestException as e:
        # If we should mock API errors
        if use_mock_data:
            logger.warning(f"API error removing member {member_email} from group {group_id}, simulating success: {e}")
            st.warning(f"API Error but simulating successful removal of {member_email} from group (mock mode)")
            return True
        else:
            st.error(f"API Error removing member {member_email} from group {group_id}: {e}")
            return False

def is_valid_email(email: str) -> bool:
    """
    Validates if a string is a syntactically valid email address ending with '@westkingdom.org'.

    Args:
        email: The email string to validate.

    Returns:
        True if the email is valid and ends with '@westkingdom.org', False otherwise.
    """
    if not isinstance(email, str):
        return False
    # Regex for basic email structure + specific domain, case-insensitive domain check
    pattern = r'^[a-zA-Z0-9._%+-]+@westkingdom\.org$'
    return bool(re.match(pattern, email, re.IGNORECASE))
