#!/bin/bash
# Run the Streamlit application with required environment variables for local development
# This is for local development only

# Set the environment variables for authentication
export GOOGLE_CLIENT_ID="85382560394-7aqkmopbm521utmmhrtr5rijj1tl306r.apps.googleusercontent.com"
export GOOGLE_CLIENT_SECRET="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"
export REDIRECT_URL="http://localhost:8501"
export BASE_URL="http://localhost:8501"

# Set the environment variable to bypass group membership checks (for development)
export BYPASS_GROUP_CHECK=true

# Display a message explaining what's happening
echo "==================================================="
echo "Running Regnum Front in LOCAL DEVELOPMENT MODE"
echo "OAuth credentials and bypass settings enabled for local testing"
echo "Group membership checks are BYPASSED for @westkingdom.org emails"
echo "This is for LOCAL TESTING ONLY and should not be used in production"
echo "==================================================="

# Run the Streamlit application
streamlit run Home.py 