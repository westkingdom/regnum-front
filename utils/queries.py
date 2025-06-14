import requests
from .config import api_url
import pandas as pd
import re
import streamlit as st
from typing import Tuple, List, Dict, Optional, Any
from utils.logger import app_logger as logger

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
        if 'id' not in df_groups.columns or 'name' not in df_groups.columns:
            raise KeyError("Required columns 'id' or 'name' not found in JSON.")
        group_name_to_id = pd.Series(df_groups.id.values, index=df_groups.name).to_dict()
        group_options = df_groups['name'].tolist()
    except FileNotFoundError:
        st.error(f"Error: Group data file ({file_path}) not found.")
    except pd.errors.EmptyDataError:
        st.error(f"Error: Group data file ({file_path}) is empty or not valid JSON.")
    except ValueError as e:
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
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error fetching group {group_id}: {e}")
        return None

def get_group_members(group_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetches the members list for a specific group from the API.

    Args:
        group_id: The unique identifier of the group.

    Returns:
        A dictionary containing the list of members (usually under a 'members' key)
        if successful (status code 200), otherwise None.
    """
    try:
        response = requests.get(f"{api_url}/groups/{group_id}/members/")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error fetching members for group {group_id}: {e}")
        return None

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
        response.raise_for_status()
        return True
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
    params = {"member_email": member_email}
    try:
        response = requests.post(f"{api_url}/groups/{group_id}/add-member/", params=params)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
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
    try:
        response = requests.delete(f"{api_url}/groups/{group_id}/members/{member_email}")
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
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
    pattern = r'^[a-zA-Z0-9._%+-]+@westkingdom\.org$'
    return bool(re.match(pattern, email, re.IGNORECASE))
