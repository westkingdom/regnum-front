# WKRegnum Authentication System

This document describes the JWT-based authentication system implemented for the WKRegnum portal.

## Overview

The application now uses JWT (JSON Web Tokens) for authentication with the following security model:

- **Protected Pages**: Most pages require authentication (Home, Groups, Regnum)
- **Public Pages**: Duty Request form is publicly accessible with reCAPTCHA protection
- **Login Page**: Dedicated login interface with demo credentials

## Authentication Flow

1. Users access the login page (`pages/0_Login.py`)
2. Upon successful authentication, a JWT token is created and stored in session state
3. Protected pages verify the JWT token before allowing access
4. Tokens expire after 24 hours and require re-authentication

## User Accounts

### Demo Credentials (Development)

**Administrator Account:**
- Email: `admin@westkingdom.org`
- Password: `admin123`
- Role: `admin`

**Standard User Account:**
- Email: `user@westkingdom.org`
- Password: `user123`
- Role: `user`

### Production Setup

For production deployment, you should:

1. **Replace demo credentials** with real user accounts
2. **Use proper password hashing** (bcrypt is now implemented)
3. **Integrate with a real user database** (replace the in-memory USERS_DB)
4. **Set secure JWT secret** via environment variable

### Password Hashing Utility

Use the included password hashing utility to generate secure bcrypt hashes:

```bash
# Interactive mode (recommended for security)
./hash_password.sh

# Command line mode
./hash_password.sh hash your_password_here
```

See [PASSWORD_HASHING.md](PASSWORD_HASHING.md) for detailed instructions.

## reCAPTCHA Protection

The Duty Request form (`pages/5_Duty_Request.py`) is protected by Google reCAPTCHA:

- **Development Mode**: reCAPTCHA verification is disabled
- **Production Mode**: Requires valid reCAPTCHA response

### reCAPTCHA Setup

1. Get reCAPTCHA keys from [Google reCAPTCHA](https://www.google.com/recaptcha/)
2. Set environment variables:
   - `RECAPTCHA_SITE_KEY`: Your site key
   - `RECAPTCHA_SECRET_KEY`: Your secret key

## Environment Variables

### Required for Authentication

```bash
# JWT Configuration
JWT_SECRET="your-secure-jwt-secret-key"

# reCAPTCHA Configuration
RECAPTCHA_SITE_KEY="your-recaptcha-site-key"
RECAPTCHA_SECRET_KEY="your-recaptcha-secret-key"
```

### Local Development

The `run_local_dev.sh` script includes default values for development.

### Production Deployment

Update `cloudbuild.yaml` with your production values:

```yaml
'--set-env-vars',
'JWT_SECRET=your-production-jwt-secret,RECAPTCHA_SITE_KEY=your-site-key,RECAPTCHA_SECRET_KEY=your-secret-key'
```

## Page Protection Levels

### Protected Pages (Authentication Required)
- `Home.py` - Main dashboard
- `pages/1_Groups.py` - Group management
- `pages/2_Regnum.py` - Regnum data entry

### Public Pages (No Authentication)
- `pages/0_Login.py` - Login interface
- `pages/5_Duty_Request.py` - Duty request form (with reCAPTCHA)
- `pages/health.py` - Health check endpoint

## Security Features

1. **JWT Token Expiration**: Tokens expire after 24 hours
2. **Session Management**: Automatic session cleanup on logout
3. **reCAPTCHA Protection**: Prevents automated form submissions
4. **Role-Based Access**: Support for admin and user roles
5. **Secure Headers**: JWT tokens are validated on each request

## Development vs Production

### Development Mode
- Simplified password verification
- reCAPTCHA verification disabled
- Demo credentials available
- Detailed logging

### Production Mode
- Secure password hashing required
- Full reCAPTCHA verification
- Environment-based configuration
- Production logging levels

## API Integration

The authentication system integrates with the existing API structure:

- JWT tokens can be passed to API calls for user context
- User roles can be used for API authorization
- Session state maintains user information across page loads

## Troubleshooting

### Common Issues

1. **"Authentication Required" on all pages**
   - Check JWT_SECRET environment variable
   - Verify user credentials in USERS_DB
   - Check browser session storage

2. **reCAPTCHA not working**
   - Verify RECAPTCHA_SITE_KEY and RECAPTCHA_SECRET_KEY
   - Check domain configuration in reCAPTCHA console
   - Ensure HTTPS in production

3. **Token expiration issues**
   - Tokens expire after 24 hours
   - Users need to log in again
   - Check system clock synchronization

### Logs

Authentication events are logged with the following patterns:
- `JWT token created for user: {email}`
- `User authenticated successfully: {email}`
- `Authentication failed for user: {email}`
- `User logged out: {email}`

## Future Enhancements

Potential improvements for production use:

1. **Database Integration**: Replace in-memory user storage
2. **OAuth Integration**: Support for Google/Microsoft SSO
3. **Password Reset**: Email-based password recovery
4. **Multi-Factor Authentication**: Additional security layer
5. **Audit Logging**: Comprehensive access logging
6. **Session Management**: Advanced session controls