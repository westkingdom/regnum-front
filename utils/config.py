import os

# --- API / URL ---
api_url  = os.environ.get('REGNUM_API_URL', 'https://regnum-api-lb-backend-service')
base_url = os.environ.get('BASE_URL', 'http://localhost:8501')

# --- OAuth state signing (reuses JWT_SECRET) ---
JWT_SECRET = os.environ.get('JWT_SECRET')
if not JWT_SECRET:
    raise RuntimeError(
        "JWT_SECRET environment variable is required. "
        "Set it to a cryptographically random 64-byte hex string: "
        "python3 -c \"import secrets; print(secrets.token_hex(64))\""
    )

# --- Google OAuth 2.0 ---
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
if not GOOGLE_CLIENT_ID:
    raise RuntimeError(
        "GOOGLE_CLIENT_ID environment variable is required. "
        "Create an OAuth 2.0 Web Application credential in GCP Console."
    )

GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
if not GOOGLE_CLIENT_SECRET:
    raise RuntimeError(
        "GOOGLE_CLIENT_SECRET environment variable is required. "
        "Copy it from your OAuth 2.0 credential in GCP Console."
    )

OAUTH_REDIRECT_URI = os.environ.get('OAUTH_REDIRECT_URI', f'{base_url}/login')
REQUIRED_GOOGLE_GROUP = os.environ.get('REQUIRED_GOOGLE_GROUP', 'regnum-site@westkingdom.org')

# --- reCAPTCHA Enterprise ---
RECAPTCHA_SITE_KEY = os.environ.get('RECAPTCHA_SITE_KEY', '')

# --- Email addresses ---
ADMIN_EMAIL              = os.environ.get('ADMIN_EMAIL', 'webminister@westkingdom.org')
COMMUNICATIONS_EMAIL     = os.environ.get('COMMUNICATIONS_EMAIL', 'communications@westkingdom.org')
IMPERSONATED_USER_EMAIL  = os.environ.get('IMPERSONATED_USER_EMAIL', 'westkingdom@westkingdom.org')
RECIPIENT_COMMUNICATIONS = os.environ.get('RECIPIENT_COMMUNICATIONS', 'communications@westkingdom.org')
RECIPIENT_SITE           = os.environ.get('RECIPIENT_SITE', 'regnum-site@westkingdom.org')

# --- Service account key paths ---
SECRET_SA_KEY_PATH = '/secrets/sa/service_account.json'
LOCAL_SA_KEY_PATH  = os.environ.get('LOCAL_SA_KEY_PATH', '')

# --- Group / legacy config ---
REGNUM_ADMIN_GROUP = os.environ.get('REGNUM_ADMIN_GROUP', '00kgcv8k1r9idky')
_bypass_raw        = os.environ.get('BYPASS_GROUP_CHECK', 'false').lower()
BYPASS_GROUP_CHECK = _bypass_raw == 'true'
