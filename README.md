# WKRegnum - West Kingdom Regnum Portal

A Streamlit-based web application for managing the West Kingdom's officer roster (regnum) and Google Groups. **This application is now publicly accessible without authentication requirements.**

## Features

- **Public Access**: No login required - all features available to everyone
- **Officer Management**: View and manage the current officer roster
- **Group Management**: Manage Google Groups and memberships
- **Email Integration**: Send duty request emails and notifications
- **Responsive Design**: Works on desktop and mobile devices

## Architecture

- **Frontend**: Streamlit web application
- **API**: RESTful backend for data management
- **Deployment**: Google Cloud Run with Docker containers
- **Public Access**: No authentication barriers

## Quick Start

### Local Development

1. **Clone Repository**:
   ```bash
   git clone <repository-url>
   cd regnum-front
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Application**:
   ```bash
   ./run_local_dev.sh
   ```

The application will be available at `http://localhost:8501` with full functionality.

### Environment Variables

For local development, you can modify these in `run_local_dev.sh`:

```bash
# API settings  
export REGNUM_API_URL="https://regnum-api-njxuammdla-uw.a.run.app"
export BASE_URL="http://localhost:8501"
```

## Deployment

### Cloud Run Deployment

1. **Build and Deploy**:
   ```bash
   gcloud builds submit --config cloudbuild.yaml
   ```

2. **Environment Variables** (set in cloudbuild.yaml):
   ```yaml
   REGNUM_API_URL=https://regnum-api-njxuammdla-uw.a.run.app
   BASE_URL=https://wkregnum-njxuammdla-uw.a.run.app
   STREAMLIT_ENV=production
   ```

The deployed application will be publicly accessible at the Cloud Run URL.

## Application Features

### Available to All Users

- **Regnum Viewer**: Browse the current officer roster
- **Search**: Find officers by title or branch
- **Reports**: Generate basic and advanced reports
- **Group Management**: Manage Google Groups and memberships
- **Officer Management**: Add/edit officer information
- **Email Templates**: Configure email templates
- **Duty Requests**: Submit duty request forms

## Troubleshooting

### API Issues

1. **"No groups found"**:
   - Check API connectivity to regnum-api service
   - Verify the API service is running

2. **"Failed to fetch members"**:
   - Verify API service is running
   - Check Cloud Run logs for detailed errors
   - Ensure group ID exists and is accessible

### Development Tips

1. **View Logs**:
   ```bash
   gcloud logs read --service=regnum-front --limit=50
   ```

## Security Considerations

- **Public Access**: The application is now publicly accessible to anyone
- **No Authentication**: All users have full administrative access
- **API Security**: Backend API should implement its own security measures
- **Data Sensitivity**: Consider the implications of public access to organizational data

## Contributing

1. Test changes locally first with `./run_local_dev.sh`
2. Update documentation for any configuration changes
3. Test deployment with `gcloud builds submit`

## Support

For technical issues, contact:
- **Technical Issues**: webminister@westkingdom.org
- **Feature Requests**: webminister@westkingdom.org

## Migration Notes

This application has been converted from an authenticated system to a publicly accessible one:

- **Removed**: Google OAuth authentication
- **Removed**: Google Groups membership verification
- **Removed**: Domain restrictions (@westkingdom.org)
- **Removed**: All debugging and mock data functionality
- **Added**: Public access for all users
- **Simplified**: Deployment configuration 