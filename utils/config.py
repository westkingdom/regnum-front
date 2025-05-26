import os

# Group ID for Regnum admins
REGNUM_ADMIN_GROUP = os.environ.get('REGNUM_ADMIN_GROUP', '00kgcv8k1r9idky')

# API URL for Regnum API
REGNUM_API_URL = os.environ.get('REGNUM_API_URL', 'https://regnum-api-njxuammdla-uw.a.run.app')

# Base URL for the application
base_url = os.environ.get('BASE_URL', 'https://wkregnum-njxuammdla-uw.a.run.app')

# Redirect URI for OAuth
redirect_uri = os.environ.get('REDIRECT_URL', 'https://wkregnum-njxuammdla-uw.a.run.app')

# If BYPASS_GROUP_CHECK is set to "true", skip group membership checks
BYPASS_GROUP_CHECK = os.environ.get('BYPASS_GROUP_CHECK', 'false').lower() == 'true'

# Input for the API URL
api_url = "https://regnum-api-njxuammdla-uw.a.run.app"

client_id = "85382560394-7aqkmopbm521utmmhrtr5rijj1tl306r.apps.googleusercontent.com"
# Define the scopes required for your application
SCOPES = [
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
    "https://mail.google.com/",
    "https://www.googleapis.com/auth/admin.directory.group.member.readonly"  # Add Directory API scope
]
