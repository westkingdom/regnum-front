import time
import requests
from typing import Dict, Optional

import google.auth.transport.requests
from google.oauth2 import id_token as _google_id_token

from utils.config import api_url as _default_api_url
from utils.logger import app_logger as logger


class _IDTokenAuth(requests.auth.AuthBase):
    """Attach a Cloud Run identity token, refreshing it before it expires.

    The audience must be the receiving service's URL. On Cloud Run the token is
    minted by the metadata server for the attached service account; under ADC
    with a service-account key it is minted from that key. Tokens are cached and
    re-fetched a few minutes before the ~1h expiry so a long-lived client (the
    cached RegnumAPI singleton) keeps working once the API enforces IAM.
    """

    _LIFETIME_SECONDS = 3600
    _REFRESH_MARGIN_SECONDS = 600

    def __init__(self, audience: str):
        self._audience = audience
        self._token: Optional[str] = None
        self._expiry: float = 0.0
        self._request = google.auth.transport.requests.Request()

    def _ensure_token(self) -> None:
        if self._token and time.time() < self._expiry:
            return
        self._token = _google_id_token.fetch_id_token(self._request, self._audience)
        self._expiry = time.time() + self._LIFETIME_SECONDS - self._REFRESH_MARGIN_SECONDS

    def __call__(self, request: requests.PreparedRequest) -> requests.PreparedRequest:
        try:
            self._ensure_token()
            request.headers["Authorization"] = f"Bearer {self._token}"
        except Exception as exc:
            logger.warning(f"Could not obtain identity token for {self._audience}: {exc}")
        return request


class RegnumAPI:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or _default_api_url
        if not self.base_url.endswith('/'):
            self.base_url += '/'
        self.session = requests.Session()
        # Audience is the receiving service's URL (no trailing slash).
        self.session.auth = _IDTokenAuth(self.base_url.rstrip('/'))

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