import requests
from typing import Dict, List, Optional
from google.auth.transport.requests import Request
from google.oauth2 import service_account
import google.auth
import os

class RegnumAPI:
    def __init__(self, base_url: str = "https://regnum-api-njxuammdla-uw.a.run.app/", client_id: str = None):
        self.base_url = base_url
        self.client_id = client_id or os.getenv('IAP_CLIENT_ID')
        self.session = requests.Session()
        self._setup_iap_auth()
    
    def _setup_iap_auth(self):
        """Setup IAP authentication"""
        try:
            if not self.client_id:
                print("Warning: No IAP_CLIENT_ID provided, skipping IAP authentication")
                return
                
            # Get default credentials
            credentials, project = google.auth.default()
            
            # For IAP, we need to create an identity token, not an access token
            from google.auth.transport.requests import Request
            import google.oauth2.id_token
            
            # Create identity token for IAP
            iap_request = Request()
            identity_token = google.oauth2.id_token.fetch_id_token(iap_request, self.client_id)
            
            # Set authorization header with identity token
            self.session.headers.update({
                'Authorization': f'Bearer {identity_token}'
            })
            
            print("IAP authentication configured successfully")
            
        except Exception as e:
            print(f"Warning: Could not setup IAP authentication: {e}")
            print("Continuing without IAP auth - this may work for local development")
            # Continue without IAP auth for local development

    def get_all_groups(self) -> Dict:
        """Get all groups"""
        response = self.session.get(f"{self.base_url}/groups/")
        response.raise_for_status()
        return response.json()

    def create_group(self, group_id: str, group_name: str) -> Dict:
        """Create a new group"""
        params = {"group_id": group_id, "group_name": group_name}
        response = self.session.post(f"{self.base_url}/groups/", params=params)
        response.raise_for_status()
        return response.json()

    def get_principalities(self) -> Dict:
        """Get all principalities"""
        response = self.session.get(f"{self.base_url}/principalities/")
        response.raise_for_status()
        return response.json()

    def get_group_types(self) -> Dict:
        """Get all group types (officers)"""
        response = self.session.get(f"{self.base_url}/officers/")
        response.raise_for_status()
        return response.json()

    def get_groups_in_principality(self, principality: str) -> Dict:
        """Get groups in a specific principality"""
        response = self.session.get(f"{self.base_url}/principalities/{principality}/groups/")
        response.raise_for_status()
        return response.json()

    def add_member_to_group(self, group_id: str, member_email: str) -> Dict:
        """Add a member to a group"""
        params = {"member_email": member_email}
        response = self.session.post(f"{self.base_url}/groups/{group_id}/add-member/", params=params)
        response.raise_for_status()
        return response.json()

    def remove_member_from_group(self, group_id: str, member_email: str) -> Dict:
        """Remove a member from a group"""
        response = self.session.delete(f"{self.base_url}/groups/{group_id}/members/{member_email}")
        response.raise_for_status()
        return response.json()

    def get_user(self, user_email: str) -> Dict:
        """Get user information"""
        params = {"user_email": user_email}
        response = self.session.get(f"{self.base_url}/users/", params=params)
        response.raise_for_status()
        return response.json()