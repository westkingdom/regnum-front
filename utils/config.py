import os

# --- API / URL ---
api_url  = os.environ.get('REGNUM_API_URL', 'https://regnum-api-lb-backend-service')
base_url = os.environ.get('BASE_URL', 'http://localhost:8501')

# --- JWT ---
JWT_SECRET = os.environ.get('JWT_SECRET')
if not JWT_SECRET:
    raise RuntimeError(
        "JWT_SECRET environment variable is required. "
        "Set it to a cryptographically random 64-byte hex string."
    )

# --- Users database (JSON string, sourced from Secret Manager in production) ---
USERS_DB_JSON = os.environ.get('USERS_DB_JSON', '')

# --- reCAPTCHA Enterprise ---
# Site key is passed to the frontend widget.
# Verification uses the Enterprise Assessment API with ADC (no secret key needed).
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
