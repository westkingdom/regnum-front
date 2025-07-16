#!/bin/bash
# Run the WKRegnum application for local development
# This is for local development only - no authentication required

# Set API URL - uncomment the local API line if you have a local API server
export REGNUM_API_URL="https://regnum-api-njxuammdla-uw.a.run.app"
# export REGNUM_API_URL="http://localhost:8000"  # Use this for local API server

# Set the base URL for local development
export BASE_URL="http://localhost:8501"

# Set environment for development
export STREAMLIT_ENV="development"

# Email configuration for local development
# Configure these with your email service credentials
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_SENDER_EMAIL="your-email@gmail.com"
export SMTP_SENDER_PASSWORD="your-app-password"

# JWT Authentication configuration
export JWT_SECRET="dev-jwt-secret-key-change-in-production"

# reCAPTCHA configuration (for Duty Request form)
export RECAPTCHA_SITE_KEY="your-recaptcha-site-key"
export RECAPTCHA_SECRET_KEY="your-recaptcha-secret-key"

# Display configuration message
echo "==================================================="
echo "Running WKRegnum Portal in LOCAL DEVELOPMENT MODE"
echo "==================================================="
echo "Configuration:"
echo "  - Authentication: JWT ENABLED"
echo "  - API URL: $REGNUM_API_URL"
echo "  - Base URL: $BASE_URL"
echo "  - reCAPTCHA: Development Mode (Disabled)"
echo ""
echo "🔐 Authentication is now REQUIRED for most pages."
echo "📋 Duty Request form remains publicly accessible."
echo ""
echo "Demo Login Credentials:"
echo "  Admin: admin@westkingdom.org / admin123"
echo "  User:  user@westkingdom.org / user123"
echo "==================================================="

# Run the application
streamlit run Home.py 