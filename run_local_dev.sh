#!/bin/bash
# Run the WKRegnum application for local development
# This is for local development only - no authentication required

# Set API URL - Direct Cloud Run service (no IAP)
export REGNUM_API_URL="https://regnum-api-85382560394.us-west1.run.app"
# export REGNUM_API_URL="http://localhost:8000"  # Use this for local API server

# Set the base URL for local development
export BASE_URL="http://localhost:8501"

# Set environment for development
export STREAMLIT_ENV="development"

# Gmail API configuration for local development
# Email sending now uses Gmail API with service account impersonation
# No SMTP credentials needed - uses service account key file

# JWT Authentication configuration
export JWT_SECRET="dev-jwt-secret-key-change-in-production"

# reCAPTCHA configuration (for Duty Request form)
export RECAPTCHA_SITE_KEY="your-recaptcha-site-key"
export RECAPTCHA_SECRET_KEY="your-recaptcha-secret-key"

# No authentication needed - IAP has been disabled for regnum-api

# Display configuration message
echo "==================================================="
echo "Running WKRegnum Portal in LOCAL DEVELOPMENT MODE"
echo "==================================================="
echo "Configuration:"
echo "  - Authentication: JWT ENABLED"
echo "  - Email System: Gmail API (Service Account)"
echo "  - API URL: $REGNUM_API_URL"
echo "  - Base URL: $BASE_URL"
echo "  - reCAPTCHA: Development Mode (Disabled)"
echo ""
echo "🔐 Authentication is now REQUIRED for most pages."
echo "📋 Duty Request form remains publicly accessible."
echo "📧 Email notifications use Gmail API with service account."
echo ""
echo "✅ API ACCESS:"
echo "   Backend API is now accessible without authentication"
echo "   IAP has been disabled for regnum-api service"
echo ""
echo "Demo Login Credentials:"
echo "  Admin: admin@westkingdom.org / admin123"
echo "  User:  user@westkingdom.org / user123"
echo "==================================================="

# Run the application
streamlit run Home.py 