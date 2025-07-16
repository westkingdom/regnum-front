# Gmail API Email System for WKRegnum

This document describes the Gmail API-based email system implemented for the WKRegnum application, replacing the previous SMTP configuration.

## Overview

The WKRegnum application now uses **Google Gmail API exclusively** for all email functionality:

- **Duty Request Form**: Sends notifications via Gmail API
- **Registration Emails**: Sends notifications via Gmail API  
- **Service Account Authentication**: Uses impersonation for sending emails
- **No SMTP Required**: Eliminates need for SMTP credentials

## Architecture

### Gmail API Integration

```
WKRegnum Application
    ↓
Gmail API Service (with Service Account)
    ↓
Google Workspace Email (westkingdom@westkingdom.org)
    ↓
Recipients (users, communications, site admin)
```

### Key Components

1. **Service Account**: Authenticates with Google APIs
2. **Domain-wide Delegation**: Allows impersonation of workspace users
3. **Gmail API**: Sends emails on behalf of impersonated user
4. **Scopes**: `https://www.googleapis.com/auth/gmail.send`

## Configuration

### Service Account Setup

The application uses a service account with domain-wide delegation to send emails:

**Service Account Key Locations**:

- **Production**: `/secrets/sa/service_account.json` (mounted as secret)
- **Development**: `regnum-service-account-key.json` (local file)

**Impersonated User**:

- **Email**: `westkingdom@westkingdom.org`
- **Purpose**: All emails are sent "from" this address
- **Requirement**: Must exist in Google Workspace

### Required Scopes

```python
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
```

### Environment Variables

**No SMTP variables needed** - the following have been removed:

- ~~`SMTP_SERVER`~~
- ~~`SMTP_PORT`~~
- ~~`SMTP_USERNAME`~~
- ~~`SMTP_PASSWORD`~~
- ~~`SENDER_EMAIL`~~

**Current environment variables**:

- `STREAMLIT_ENV`: Controls development vs production behavior
- `JWT_SECRET`: For authentication
- `RECAPTCHA_SITE_KEY`: For form protection
- `RECAPTCHA_SECRET_KEY`: For form protection

## Email Functions

### 1. Duty Request Emails

**Function**: `send_duty_request_email(form_data, user_email)`

**Recipients**:

- User who submitted the form
- `communications@westkingdom.org`
- `regnum-site@westkingdom.org`

**Behavior**:

- **Development Mode**: Shows simulation message, no actual emails sent
- **Production Mode**: Sends emails via Gmail API to all recipients

**Email Format**:

```
Subject: [Regnum Submission] New Duty/Job Request Submitted
From: westkingdom@westkingdom.org
To: [individual recipient]

A new duty/job request has been submitted via the WKRegnum portal:

--- Request Details ---
Society Name: [name]
Mundane Name: [name]
West Kingdom Google Email: [email]
[... other form fields ...]

--- Notification Recipients ---
User: [user_email]
Communications: communications@westkingdom.org
Site Admin: regnum-site@westkingdom.org

This is an automated notification from the WKRegnum system.
```

### 2. Registration Emails

**Function**: `send_registration_email(form_data, group_name)`

**Recipients**:

- `webminister@westkingdom.org` (primary)
- `communications@westkingdom.org` (CC)

**Email Format**:

```
Subject: [Regnum Submission] New Member Registration for [group]: [sca_name]
From: westkingdom@westkingdom.org
To: webminister@westkingdom.org
CC: communications@westkingdom.org

A new member registration has been submitted for the group: [group_name]

--- Member Details ---
SCA Name: [name]
Mundane Name: [name]
[... other registration details ...]
```

## Development vs Production

### Development Mode

**Behavior**:

- No actual emails sent
- Shows simulation messages in Streamlit UI
- Displays intended recipients
- Returns success for testing

**Activation**:

```bash
export STREAMLIT_ENV="development"
```

**UI Messages**:

```
⚠️ Development Mode: Email sending simulation enabled.
📧 In production, this would send emails via Gmail API to:
- User: [email]
- Communications: communications@westkingdom.org
- Site Admin: regnum-site@westkingdom.org
✅ Form submission completed successfully (development mode)
```

### Production Mode

**Behavior**:

- Sends actual emails via Gmail API
- Uses service account authentication
- Logs all email operations
- Returns actual success/failure status

**Requirements**:

- Valid service account key file
- Proper domain-wide delegation setup
- Gmail API enabled in Google Cloud Project

## Error Handling

### Service Account Issues

**Missing Key File**:

```
Service Account key file not found at expected path: [path]
```

**Authentication Errors**:

```
Error loading Service Account credentials: [error]
```

**API Errors**:

```
Failed to initialize Gmail service. Please contact the administrator.
```

### Email Sending Issues

**Individual Recipient Failures**:

- Logs specific recipient failures
- Continues sending to other recipients
- Returns success if at least one email sent

**Complete Failure**:

```
Failed to send any duty request emails
Failed to send notification emails. Please contact the administrator.
```

## Logging

### Email Operations

**Successful Sends**:

```
Duty request email sent successfully to: [recipient]
All duty request emails sent successfully
```

**Partial Success**:

```
Partial success: [count]/[total] emails sent
```

**Failures**:

```
Failed to send duty request email to: [recipient]
Error sending duty request email to [recipient]: [error]
Failed to send any duty request emails
```

## Security Features

### Service Account Security

- **Least Privilege**: Only `gmail.send` scope granted
- **Domain Restriction**: Can only impersonate workspace users
- **Key Protection**: Service account key stored as Kubernetes secret
- **Audit Trail**: All API calls logged by Google Cloud

### Email Security

- **Authenticated Sending**: All emails authenticated via service account
- **Domain Validation**: Emails sent from verified workspace domain
- **Recipient Validation**: Built-in email format validation
- **Error Isolation**: Individual recipient failures don't affect others

## Troubleshooting

### Common Issues

1. **"Service Account key file not found"**
   - Check file exists at expected path
   - Verify file permissions
   - Ensure proper mounting in Cloud Run

2. **"Error loading Service Account credentials"**
   - Validate JSON format of key file
   - Check service account has proper permissions
   - Verify domain-wide delegation is configured

3. **"Failed to initialize Gmail service"**
   - Ensure Gmail API is enabled in Google Cloud Project
   - Check service account has necessary IAM roles
   - Verify network connectivity to Gmail API

4. **Emails not being received**
   - Check spam/junk folders
   - Verify recipient email addresses
   - Check Google Workspace email routing
   - Review Gmail API quotas and limits

### Debugging Steps

1. **Check Service Account Setup**:

   ```bash
   # Verify key file exists and is readable
   ls -la regnum-service-account-key.json
   
   # Validate JSON format
   python -m json.tool regnum-service-account-key.json
   ```

2. **Test Gmail API Access**:

   ```python
   from utils.email import get_gmail_service
   service = get_gmail_service()
   print("Gmail service:", service)
   ```

3. **Check Logs**:

   ```bash
   # Local development
   tail -f logs/application.log
   
   # Cloud Run
   gcloud logs read --service=regnum-front --limit=50
   ```

## Migration from SMTP

### Changes Made

**Removed Components**:

- SMTP server configuration
- SMTP authentication credentials
- `smtplib` usage in duty request emails
- SMTP environment variables

**Added Components**:

- Gmail API service initialization
- Service account authentication
- Individual recipient email sending
- Enhanced error handling and logging

**Maintained Components**:

- Email message formatting
- Recipient lists
- Development mode simulation
- Error reporting to users

### Benefits of Gmail API

1. **Better Reliability**: Direct API integration vs SMTP relay
2. **Enhanced Security**: Service account authentication vs password
3. **Improved Monitoring**: Detailed API logging and metrics
4. **Consistent Authentication**: Single auth method for all emails
5. **Better Error Handling**: Granular error reporting per recipient
6. **No Password Management**: Eliminates SMTP password rotation

## Production Deployment

### Prerequisites

1. **Google Cloud Project**: With Gmail API enabled
2. **Service Account**: With domain-wide delegation
3. **Google Workspace**: With target domain configured
4. **IAM Permissions**: Proper roles assigned to service account

### Deployment Steps

1. **Update Code**: Deploy Gmail API refactored code
2. **Remove SMTP Variables**: Clean up environment configuration
3. **Verify Service Account**: Ensure key file is properly mounted
4. **Test Email Functionality**: Submit test duty request
5. **Monitor Logs**: Check for successful email delivery

### Verification

```bash
# Deploy the updated application
gcloud builds submit --config cloudbuild.yaml

# Check service status
gcloud run services describe regnum-front --region=us-west1

# Test email functionality
# (Submit a test duty request form)

# Check logs for email operations
gcloud logs read --service=regnum-front --filter="textPayload:email" --limit=20
```

## Future Enhancements

### Potential Improvements

1. **Email Templates**: HTML email formatting
2. **Attachment Support**: File attachments for forms
3. **Email Tracking**: Delivery confirmation and read receipts
4. **Batch Operations**: Bulk email sending capabilities
5. **Email Queuing**: Asynchronous email processing
6. **Advanced Logging**: Structured logging with correlation IDs

### Integration Opportunities

1. **Calendar Integration**: Meeting scheduling for duty assignments
2. **Drive Integration**: Document sharing for forms
3. **Sheets Integration**: Automatic data logging
4. **Admin SDK**: User and group management automation

## Support

### Documentation References

- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [Service Account Authentication](https://cloud.google.com/docs/authentication/production)
- [Domain-wide Delegation](https://developers.google.com/admin-sdk/directory/v1/guides/delegation)

### Contact Information

For technical issues with the Gmail API integration:

- **Technical Issues**: <webminister@westkingdom.org>
- **API Issues**: Check Google Cloud Console logs
- **Authentication Issues**: Verify service account configuration
