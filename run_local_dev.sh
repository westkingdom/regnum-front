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

# Display configuration message
echo "==================================================="
echo "Running WKRegnum Portal in LOCAL DEVELOPMENT MODE"
echo "==================================================="
echo "Configuration:"
echo "  - Authentication: DISABLED (Public Access)"
echo "  - API URL: $REGNUM_API_URL"
echo "  - Base URL: $BASE_URL"
echo ""
echo "ℹ️  The application is now publicly accessible without authentication."
echo "   All users have full administrative access to all features."
echo "==================================================="

# Run the application
streamlit run Home.py 