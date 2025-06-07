# WKRegnum - West Kingdom Regnum Portal

A Streamlit-based web application for managing the West Kingdom's officer roster (regnum) and Google Groups.

## Features

- **Google OAuth Authentication**: Secure login with @westkingdom.org accounts
- **Group-based Authorization**: Admin features restricted to regnum-site group members
- **Officer Management**: View and manage the current officer roster
- **Group Management**: Manage Google Groups and memberships (admin only)
- **Email Integration**: Send duty request emails and notifications
- **Responsive Design**: Works on desktop and mobile devices

## Architecture

- **Frontend**: Streamlit web application
- **Authentication**: Google OAuth 2.0 with domain restriction
- **Authorization**: Google Groups API for membership verification
- **API**: RESTful backend for data management
- **Deployment**: Google Cloud Run with Docker containers

## Authentication Setup

### Prerequisites

1. **Google Cloud Project** with the following APIs enabled:
   - Google+ API
   - Admin SDK API
   - Identity and Access Management (IAM) API

2. **Google Workspace Domain** (westkingdom.org) with admin access

### OAuth Client Configuration

1. **Create OAuth 2.0 Client ID**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Navigate to APIs & Services > Credentials
   - Create OAuth 2.0 Client ID (Web application)
   - Add authorized redirect URIs:
     - `https://wkregnum-njxuammdla-uw.a.run.app` (production)
     - `http://localhost:8501` (development)

2. **Download Credentials**:
   - Download the JSON file and save as `utils/google_credentials.json`
   - For Cloud Run, upload as a secret named `google-oauth-credentials`

### Service Account Setup

1. **Create Service Account**:
   ```bash
   gcloud iam service-accounts create regnum-service-account \
       --display-name="Regnum Service Account" \
       --description="Service account for WKRegnum application"
   ```

2. **Enable Domain-Wide Delegation**:
   - Go to Google Cloud Console > IAM & Admin > Service Accounts
   - Edit the service account
   - Check "Enable Google Workspace Domain-wide Delegation"
   - Note the Client ID (numeric)

3. **Configure Google Workspace Admin Console**:
   - Go to [Google Admin Console](https://admin.google.com/)
   - Navigate to Security > API Controls > Domain-wide Delegation
   - Add the service account Client ID with these scopes:
     ```
     https://www.googleapis.com/auth/admin.directory.group.member.readonly
     https://www.googleapis.com/auth/admin.directory.group.readonly
     ```

4. **Create and Download Key**:
   ```bash
   gcloud iam service-accounts keys create regnum-service-account-key.json \
       --iam-account=regnum-service-account@PROJECT_ID.iam.gserviceaccount.com
   ```

5. **Upload to Cloud Run**:
   ```bash
   gcloud secrets create regnum-service-account \
       --data-file=regnum-service-account-key.json
   ```

### Group Configuration

1. **Create Admin Group**:
   - Create a Google Group: `regnum-site@westkingdom.org`
   - Add administrators to this group
   - Note the group ID (found in Admin Console)

2. **Update Configuration**:
   - Set `REGNUM_ADMIN_GROUP` environment variable to the group ID
   - Example: `00kgcv8k1r9idky`

## Local Development

### Setup

1. **Clone Repository**:
   ```bash
   git clone <repository-url>
   cd regnum-front
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Credentials**:
   - Place `google_credentials.json` in `utils/` directory
   - Place `regnum-service-account-key.json` in project root

4. **Run Application**:
   ```bash
   ./run_local_dev.sh
   ```

### Environment Variables

For local development, you can modify these in `run_local_dev.sh`:

```bash
# Authentication settings
export BYPASS_AUTH=false              # Set to true to skip OAuth
export BYPASS_GROUP_CHECK=false       # Set to true to skip group checks

# API settings  
export USE_MOCK_DATA=false            # Set to true for mock API responses
export REGNUM_API_URL="https://regnum-api-njxuammdla-uw.a.run.app"

# OAuth settings
export REDIRECT_URL="http://localhost:8501"
export GOOGLE_CLIENT_ID="your-client-id"
export GOOGLE_CLIENT_SECRET="your-client-secret"
```

## Deployment

### Cloud Run Deployment

1. **Build and Deploy**:
   ```bash
   gcloud builds submit --config cloudbuild.yaml
   ```

2. **Environment Variables** (set in cloudbuild.yaml):
   ```yaml
   BYPASS_AUTH=false
   BYPASS_GROUP_CHECK=false
   USE_MOCK_DATA=false
   REGNUM_API_URL=https://regnum-api-njxuammdla-uw.a.run.app
   BASE_URL=https://wkregnum-njxuammdla-uw.a.run.app
   REDIRECT_URL=https://wkregnum-njxuammdla-uw.a.run.app
   REGNUM_ADMIN_GROUP=00kgcv8k1r9idky
   ```

3. **Secrets Configuration**:
   - OAuth credentials: `/oauth/google_credentials.json`
   - Service account key: `/secrets/sa/service_account.json`

### Required Permissions

The service account needs these IAM roles:
- `roles/secretmanager.secretAccessor` (for accessing secrets)
- Domain-wide delegation for Google Workspace APIs

## Troubleshooting

### Authentication Issues

1. **"Access blocked: This app's request is invalid"**:
   - Check OAuth client configuration in Google Cloud Console
   - Verify redirect URIs match exactly
   - Ensure domain verification is complete

2. **"Group membership check failed"**:
   - Verify service account has domain-wide delegation
   - Check Google Workspace Admin Console API scopes
   - Confirm group ID is correct in environment variables

3. **"Credentials file not found"**:
   - For local development: Check `utils/google_credentials.json` exists
   - For Cloud Run: Verify secret mounting in cloudbuild.yaml

### API Issues

1. **"No groups found"**:
   - Check API connectivity to regnum-api service
   - Verify service account permissions
   - Enable mock data for testing: `USE_MOCK_DATA=true`

2. **"Failed to fetch members"**:
   - Verify group ID exists and is accessible
   - Check service account has proper scopes
   - Review Cloud Run logs for detailed errors

### Development Tips

1. **Enable Debug Mode**:
   ```bash
   export STREAMLIT_ENV=development
   ```

2. **View Logs**:
   ```bash
   gcloud logs read --service=regnum-front --limit=50
   ```

3. **Test Authentication Locally**:
   - Use `pages/debug.py` for authentication testing
   - Password: `debug123`

## Security Considerations

- OAuth credentials should never be committed to version control
- Service account keys should be stored as Cloud Secrets
- Group membership is cached for 5 minutes to reduce API calls
- All authentication can be bypassed in development (never in production)

## Contributing

1. Test authentication changes locally first
2. Ensure all bypass flags are set to `false` for production
3. Update documentation for any configuration changes
4. Test group membership verification with actual Google Groups

## Support

For issues with authentication or group access, contact:
- **Technical Issues**: webminister@westkingdom.org
- **Group Access**: webminister@westkingdom.org 