# Input for the API URL
api_url = "https://api.westkingdom.org"

client_id = "85382560394-7aqkmopbm521utmmhrtr5rijj1tl306r.apps.googleusercontent.com"
# Define the scopes required for your application
SCOPES = [
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
    "https://mail.google.com/",
    "https://www.googleapis.com/auth/admin.directory.group.member.readonly"  # Add Directory API scope
]
redirect_uri = "http://localhost:8501"

# Regnum group check configuration
REGNUM_ADMIN_GROUP = "regnum-site@westkingdom.org"
