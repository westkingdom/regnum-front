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
redirect_uri = "https://regnum-front-85382560394.us-west1.run.app"

# Regnum group check configuration
REGNUM_ADMIN_GROUP = "00kgcv8k1r9idky"
