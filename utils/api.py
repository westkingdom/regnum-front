import requests
from typing import Dict, List, Optional

class RegnumAPI:
    def __init__(self, base_url: str = "https://regnum-api-85382560394.us-west1.run.app"):
        self.base_url = base_url

    def get_all_groups(self) -> Dict:
        """Get all groups"""
        response = requests.get(f"{self.base_url}/groups/")
        response.raise_for_status()
        return response.json()

    def create_group(self, group_id: str, group_name: str) -> Dict:
        """Create a new group"""
        params = {"group_id": group_id, "group_name": group_name}
        response = requests.post(f"{self.base_url}/groups/", params=params)
        response.raise_for_status()
        return response.json()

    def get_principalities(self) -> Dict:
        """Get all principalities"""
        response = requests.get(f"{self.base_url}/principalities/")
        response.raise_for_status()
        return response.json()

    def get_group_types(self) -> Dict:
        """Get all group types (officers)"""
        response = requests.get(f"{self.base_url}/officers/")
        response.raise_for_status()
        return response.json()

    def get_groups_in_principality(self, principality: str) -> Dict:
        """Get groups in a specific principality"""
        response = requests.get(f"{self.base_url}/principalities/{principality}/groups/")
        response.raise_for_status()
        return response.json()

    def add_member_to_group(self, group_id: str, member_email: str) -> Dict:
        """Add a member to a group"""
        params = {"member_email": member_email}
        response = requests.post(f"{self.base_url}/groups/{group_id}/add-member/", params=params)
        response.raise_for_status()
        return response.json()

    def remove_member_from_group(self, group_id: str, member_email: str) -> Dict:
        """Remove a member from a group"""
        response = requests.delete(f"{self.base_url}/groups/{group_id}/members/{member_email}")
        response.raise_for_status()
        return response.json()

    def get_user(self, user_email: str) -> Dict:
        """Get user information"""
        params = {"user_email": user_email}
        response = requests.get(f"{self.base_url}/users/", params=params)
        response.raise_for_status()
        return response.json()
