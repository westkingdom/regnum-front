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
export JWT_SECRET="ebffa0c3f6e666a54af63c73a4570612f19d9c9ebe5bb91050b93f189690dc0e41dce6bf5cd0fb09183d0affef7c86094bc53b22a224477b38a1f535a5ac7948"

# User database - loaded from env var (do not hardcode credentials in source)
# In production this is sourced from Secret Manager
export USERS_DB_JSON='{"admin@westkingdom.org":{"password_hash":"$2b$12$2wKshX/CrwBD.DqBOUqMVec54r7ddWVLAdYoxAtsJJCQLuvjHk0Z6","name":"Admin (Dev)","role":"admin"},"user@westkingdom.org":{"password_hash":"$2b$12$qdLfsA3ukfaz4EK7W9oSdOfm2LcLa1GNJtGM81kMd4jVDjUc6wJUK","name":"User (Dev)","role":"user"}}'

# Group check bypass (development only - never set in production)
export BYPASS_GROUP_CHECK="true"

# Local service account key path (development only)
export LOCAL_SA_KEY_PATH="regnum-service-account-key.json"

# reCAPTCHA configuration (for Duty Request form)
export RECAPTCHA_SITE_KEY="your-recaptcha-site-key"
export RECAPTCHA_SECRET_KEY="your-recaptcha-secret-key"

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
echo "Dev Login Credentials:"
echo "  Admin: admin@westkingdom.org / admin123"
echo "  User:  user@westkingdom.org  / user123"
echo "  (credentials are set via USERS_DB_JSON in this script)"
echo "==================================================="

# Run the application using uv
uv run streamlit run Home.py 