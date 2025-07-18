import requests
from typing import Dict, Optional
import os
from google.auth.transport.requests import Request
from google.auth import default
from google.oauth2 import service_account
import google.auth

class RegnumAPI:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv('REGNUM_API_URL') or 'https://regnum-api-85382560394.us-west1.run.app/'
        if not self.base_url.endswith('/'):
            self.base_url += '/'
        self.session = requests.Session()
        self._setup_service_auth()

    def _setup_service_auth(self):
        """Setup service-to-service authentication for Cloud Run"""
        try:
            # In production (Cloud Run), this will use the service account attached to the service
            # In development, this will use Application Default Credentials (ADC)
            credentials, project = default()
            
            # Create an authenticated request object
            auth_request = Request()
            
            # Get the target audience (the regnum-api service URL)
            audience = self.base_url.rstrip('/')
            
            # For service-to-service communication, we need an identity token
            # This is different from access tokens - identity tokens are used for Cloud Run auth
            if hasattr(credentials, 'with_claims'):
                # Service account credentials - create identity token
                identity_token = credentials.with_claims(audience=audience).token
                if not identity_token:
                    credentials.refresh(auth_request)
                    identity_token = credentials.token
            else:
                # For other credential types, try to get an identity token
                try:
                    import google.oauth2.id_token
                    identity_token = google.oauth2.id_token.fetch_id_token(auth_request, audience)
                except Exception as e:
                    print(f"Could not get identity token: {e}")
                    # Fall back to access token (may not work for secured Cloud Run)
                    credentials.refresh(auth_request)
                    identity_token = credentials.token

            if identity_token:
                self.session.headers.update({
                    'Authorization': f'Bearer {identity_token}'
                })
                print(f"✅ Service authentication configured for {audience}")
            else:
                print("⚠️  Warning: Could not obtain authentication token")
                
        except Exception as e:
            print(f"⚠️  Warning: Service authentication setup failed: {e}")
            print("Proceeding without authentication (may fail if service is secured)")

    def get_all_groups(self) -> Dict:
        """Get all groups"""
        response = self.session.get(f"{self.base_url}groups/")
        response.raise_for_status()
        return response.json()

    def create_group(self, group_id: str, group_name: str) -> Dict:
        """Create a new group"""
        params = {"group_id": group_id, "group_name": group_name}
        response = self.session.post(f"{self.base_url}groups/", params=params)
        response.raise_for_status()
        return response.json()

    def get_principalities(self) -> Dict:
        """Get all principalities"""
        response = self.session.get(f"{self.base_url}principalities/")
        response.raise_for_status()
        return response.json()

    def get_group_types(self) -> Dict:
        """Get all group types (officers)"""
        response = self.session.get(f"{self.base_url}officers/")
        response.raise_for_status()
        return response.json()

    def get_groups_in_principality(self, principality: str) -> Dict:
        """Get groups in a specific principality"""
        response = self.session.get(f"{self.base_url}principalities/{principality}/groups/")
        response.raise_for_status()
        return response.json()

    def add_member_to_group(self, group_id: str, member_email: str) -> Dict:
        """Add a member to a group"""
        params = {"member_email": member_email}
        response = self.session.post(f"{self.base_url}groups/{group_id}/add-member/", params=params)
        response.raise_for_status()
        return response.json()

    def remove_member_from_group(self, group_id: str, member_email: str) -> Dict:
        """Remove a member from a group"""
        response = self.session.delete(f"{self.base_url}groups/{group_id}/members/{member_email}")
        response.raise_for_status()
        return response.json()

    def get_group_members(self, group_id: str) -> Dict:
        """Get members of a specific group"""
        response = self.session.get(f"{self.base_url}groups/{group_id}/members/")
        response.raise_for_status()
        return response.json()

    def get_user(self, user_email: str) -> Dict:
        """Get user information"""
        params = {"user_email": user_email}
        response = self.session.get(f"{self.base_url}users/", params=params)
        response.raise_for_status()
        return response.json()