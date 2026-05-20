"""Google OAuth 2.0 authentication for WKRegnum."""
import os
import secrets
import time
from typing import Optional, Dict, Any

import jwt as pyjwt
import streamlit as st
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from utils.config import (
    JWT_SECRET,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    OAUTH_REDIRECT_URI,
    REQUIRED_GOOGLE_GROUP,
    BYPASS_GROUP_CHECK,
    SECRET_SA_KEY_PATH,
    LOCAL_SA_KEY_PATH,
    IMPERSONATED_USER_EMAIL,
)
from utils.logger import app_logger as logger

_GOOGLE_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]

_DIRECTORY_SCOPES = [
    "https://www.googleapis.com/auth/admin.directory.group.member.readonly",
]


def _get_flow() -> Flow:
    return Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=_GOOGLE_SCOPES,
        redirect_uri=OAUTH_REDIRECT_URI,
    )


def _resolve_sa_key_path() -> str:
    if os.path.exists(SECRET_SA_KEY_PATH):
        return SECRET_SA_KEY_PATH
    if LOCAL_SA_KEY_PATH and os.path.exists(LOCAL_SA_KEY_PATH):
        return LOCAL_SA_KEY_PATH
    return ""


def generate_oauth_state() -> str:
    """Generate a stateless, self-verifying CSRF state token."""
    now = int(time.time())
    payload = {
        "nonce": secrets.token_urlsafe(16),
        "iat": now,
        "exp": now + 300,
    }
    return pyjwt.encode(payload, JWT_SECRET, algorithm="HS256")


def verify_oauth_state(state: str) -> bool:
    """Return True only if the state token has a valid signature and is not expired."""
    try:
        pyjwt.decode(state, JWT_SECRET, algorithms=["HS256"])
        return True
    except pyjwt.ExpiredSignatureError:
        logger.warning("OAuth state token expired")
        return False
    except pyjwt.InvalidTokenError:
        logger.warning("Invalid OAuth state token")
        return False


def get_authorization_url() -> str:
    """Return the Google OAuth authorization URL with a fresh state token."""
    flow = _get_flow()
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="select_account",
        state=generate_oauth_state(),
    )
    return auth_url


def exchange_code_for_user_info(code: str, state: str) -> Optional[Dict[str, Any]]:
    """Exchange an OAuth authorization code for Google user info.

    Returns the user info dict on success, or None if the state is invalid
    or the token exchange fails.
    """
    if not verify_oauth_state(state):
        logger.warning("OAuth state verification failed — possible CSRF attempt")
        return None
    try:
        flow = _get_flow()
        flow.fetch_token(code=code)
        service = build("oauth2", "v2", credentials=flow.credentials)
        return service.userinfo().get().execute()
    except Exception as exc:
        logger.error(f"OAuth code exchange failed: {exc}")
        return None


def check_group_membership(user_email: str) -> bool:
    """Return True if user_email is a member of REQUIRED_GOOGLE_GROUP.

    Bypassed when BYPASS_GROUP_CHECK=true (development only).
    Uses the service account with domain-wide delegation impersonating
    IMPERSONATED_USER_EMAIL (must be a Workspace admin).
    """
    if BYPASS_GROUP_CHECK:
        logger.warning(
            f"BYPASS_GROUP_CHECK enabled — skipping group check for {user_email}"
        )
        return True

    sa_key_path = _resolve_sa_key_path()
    if not sa_key_path:
        logger.error("Service account key not found; cannot verify group membership")
        return False

    try:
        from google.oauth2 import service_account

        credentials = service_account.Credentials.from_service_account_file(
            sa_key_path,
            scopes=_DIRECTORY_SCOPES,
        ).with_subject(IMPERSONATED_USER_EMAIL)

        service = build("admin", "directory_v1", credentials=credentials)
        result = service.members().hasMember(
            groupKey=REQUIRED_GOOGLE_GROUP,
            memberKey=user_email,
        ).execute()
        return result.get("isMember", False)
    except HttpError as exc:
        logger.error(f"Directory API error checking membership for {user_email}: {exc}")
        return False
    except Exception as exc:
        logger.error(f"Unexpected error checking group membership: {exc}")
        return False


def login_user(user_info: Dict[str, Any]) -> None:
    """Store authenticated user in Streamlit session state."""
    st.session_state["is_authenticated"] = True
    st.session_state["user_email"] = user_info["email"]
    st.session_state["user_name"] = user_info.get("name", user_info["email"])
    st.session_state["user_picture"] = user_info.get("picture", "")


def logout_user() -> None:
    """Clear authentication from Streamlit session state."""
    email = st.session_state.get("user_email", "Unknown")
    logger.info(f"User logged out: {email}")
    for key in ("is_authenticated", "user_email", "user_name", "user_picture"):
        st.session_state.pop(key, None)


def is_authenticated() -> bool:
    """Return True if the current session has a completed Google OAuth login."""
    return st.session_state.get("is_authenticated", False)


def get_current_user() -> Optional[Dict[str, Any]]:
    """Return the current user dict, or None if not authenticated."""
    if not is_authenticated():
        return None
    return {
        "email": st.session_state.get("user_email", ""),
        "name": st.session_state.get("user_name", ""),
        "picture": st.session_state.get("user_picture", ""),
    }


def require_authentication() -> Dict[str, Any]:
    """Block unauthenticated access; shows a sign-in button and calls st.stop()."""
    if not is_authenticated():
        st.error("Authentication required.")
        st.info("Sign in with your West Kingdom Google account to continue.")
        st.link_button("Sign in with Google", get_authorization_url())
        st.stop()
    return get_current_user()
