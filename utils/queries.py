import requests
from utils.config import api_url
import pandas as pd
import re

def get_all_groups():
    """Fetch all groups from the API"""
    response = requests.get(f"{api_url}/groups/")
    if response.status_code == 200:
        return response.json()
    return None

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
