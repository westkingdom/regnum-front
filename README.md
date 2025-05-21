# WKRegnum - West Kingdom Regnum Portal

A web application for the West Kingdom organization that provides access to officer roster and reporting systems. The application uses Google Workspace authentication to restrict access based on membership in a Google Group.

## Local Development Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the local development script:
   ```bash
   ./run_local_dev.sh
   ```

   This script sets up the required environment variables:
   - `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` for OAuth authentication
   - `REDIRECT_URL` and `BASE_URL` for the OAuth callback
   - `BYPASS_GROUP_CHECK=true` to allow any @westkingdom.org email to access the application

## Authentication System

The application uses Google OAuth for authentication and restricts access based on:

1. **Domain Verification**: Only users with @westkingdom.org email addresses can log in
2. **Group Membership**: Admin features require membership in the regnum-site Google Group

### Testing Authentication

To test group membership verification, use the `test_auth.py` script:

```bash
# Test if a user is a member of the regnum-site group
./test_auth.py user@westkingdom.org

# Test if the BYPASS_GROUP_CHECK functionality works
./test_auth.py user@westkingdom.org --bypass

# Only test service account access and permissions
./test_auth.py --service-account
```

### Troubleshooting Authentication Issues

If users cannot access the application despite being part of the correct Google Group:

1. Check that the service account has domain-wide delegation enabled
2. Verify the service account has the required OAuth scopes:
   - https://www.googleapis.com/auth/admin.directory.group.readonly
   - https://www.googleapis.com/auth/admin.directory.group.member.readonly
   - https://www.googleapis.com/auth/admin.directory.user.readonly
3. Make sure the service account key file is correctly mounted in the Cloud Run service
4. Verify that the `IMPERSONATED_USER_EMAIL` is an admin user in the Google Workspace

## Production Deployment

The application is deployed to Google Cloud Run using Cloud Build with the following considerations:

1. **Environment Variables**: Set in the Cloud Build trigger as substitution variables:
   - `_GOOGLE_CLIENT_ID`: OAuth Client ID
   - `_GOOGLE_CLIENT_SECRET`: OAuth Client Secret
   - `_BASE_URL`: The URL where the application is hosted
   - `_BYPASS_GROUP_CHECK`: Set to "false" for production, or "true" for testing

2. **Service Account**: For the Directory API access, a service account key is mounted as a secret:
   - Secret path: `/secrets/sa/service_account.json`
   - Secret name: `regnum-service-account-key`

## Security Considerations

1. Never commit OAuth credentials or service account keys to the repository
2. The `BYPASS_GROUP_CHECK` should always be set to "false" in production
3. Authentication tokens are stored in session state and expire after the OAuth token lifetime 