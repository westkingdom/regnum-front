import os
import requests
import streamlit as st
import streamlit.components.v1 as components
from utils.logger import app_logger as logger
from utils.config import RECAPTCHA_SITE_KEY

_GCP_PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT', 'westkingdom-primary')

_COMPONENT_DIR = os.path.join(os.path.dirname(__file__), "recaptcha_widget")
_recaptcha_component = components.declare_component(
    "recaptcha_widget",
    path=_COMPONENT_DIR,
)


def show_recaptcha_widget(action: str = "submit") -> str | None:
    """
    Render the reCAPTCHA widget and return the response token once the user
    completes the challenge, or None while pending.

    In development mode (STREAMLIT_ENV=development) the widget is bypassed
    and a sentinel token 'dev-bypass' is returned immediately.

    Returns:
        str  — the reCAPTCHA response token (send this to verify_recaptcha)
        None — widget not yet completed
    """
    env = os.environ.get('STREAMLIT_ENV', 'production')

    if env == 'development':
        st.info("Development mode: reCAPTCHA verification skipped.")
        return 'dev-bypass'

    if not RECAPTCHA_SITE_KEY:
        st.error("reCAPTCHA site key is not configured. Contact the administrator.")
        logger.error("RECAPTCHA_SITE_KEY is not set.")
        return None

    token = _recaptcha_component(site_key=RECAPTCHA_SITE_KEY, action=action, default=None)
    return token


def verify_recaptcha(token: str) -> bool:
    """
    Verify a reCAPTCHA Enterprise response token via the Assessment API.
    Uses Application Default Credentials (service account on Cloud Run).

    Args:
        token: The response token returned by show_recaptcha_widget().

    Returns:
        True if tokenProperties.valid is True, False otherwise.
    """
    if not token:
        logger.warning("reCAPTCHA verification called with empty token.")
        return False

    # Honour dev bypass without hitting the API
    if os.environ.get('STREAMLIT_ENV') == 'development' and token == 'dev-bypass':
        logger.info("Development mode: reCAPTCHA bypassed.")
        return True

    if not RECAPTCHA_SITE_KEY:
        logger.error("RECAPTCHA_SITE_KEY is not configured. Failing closed.")
        return False

    try:
        import google.auth
        import google.auth.transport.requests

        credentials, _ = google.auth.default(
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        auth_request = google.auth.transport.requests.Request()
        credentials.refresh(auth_request)

        url = (
            f"https://recaptchaenterprise.googleapis.com/v1"
            f"/projects/{_GCP_PROJECT_ID}/assessments"
        )
        headers = {
            'Authorization': f'Bearer {credentials.token}',
            'Content-Type': 'application/json',
        }
        payload = {
            'event': {
                'token': token,
                'siteKey': RECAPTCHA_SITE_KEY,
            }
        }

        response = requests.post(url, json=payload, headers=headers, timeout=5)
        result = response.json()

        token_props = result.get('tokenProperties', {})
        if token_props.get('valid'):
            logger.info("reCAPTCHA Enterprise verification successful.")
            return True
        else:
            reason = token_props.get('invalidReason', 'unknown')
            logger.warning(f"reCAPTCHA Enterprise verification failed: {reason}")
            return False

    except Exception as e:
        logger.error(f"reCAPTCHA Enterprise verification error: {e}")
        return False


def require_recaptcha(action: str = "submit") -> bool:
    """
    Gate function: renders the widget, waits for a valid token, then verifies
    it server-side. Calls st.stop() until the user completes the challenge.

    Usage:
        require_recaptcha(action="duty_request")
        # code below only runs after verification passes
    """
    key = f"recaptcha_verified_{action}"

    if st.session_state.get(key):
        return True

    token = show_recaptcha_widget(action=action)

    if not token:
        st.info("Please complete the reCAPTCHA verification above to continue.")
        st.stop()

    if not verify_recaptcha(token):
        st.error("reCAPTCHA verification failed. Please try again.")
        st.stop()

    st.session_state[key] = True
    return True
