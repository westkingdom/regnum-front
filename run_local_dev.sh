#!/bin/bash
# Run the WKRegnum application with required environment variables for local development
# This is for local development only

# Set the environment variables for authentication
export GOOGLE_CLIENT_ID="85382560394-7aqkmopbm521utmmhrtr5rijj1tl306r.apps.googleusercontent.com"
export GOOGLE_CLIENT_SECRET="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"
export REDIRECT_URL="http://localhost:8501"
export BASE_URL="http://localhost:8501"

# Set API URL - uncomment the local API line if you have a local API server
export REGNUM_API_URL="https://regnum-api-njxuammdla-uw.a.run.app"
# export REGNUM_API_URL="http://localhost:8000"  # Use this for local API server

# Set the admin group ID
export REGNUM_ADMIN_GROUP="00kgcv8k1r9idky"

# Set environment for development
export STREAMLIT_ENV="development"

# Authentication settings - change these for testing
# Set BYPASS_AUTH=true to skip OAuth (for testing only)
# Set BYPASS_GROUP_CHECK=true to skip group membership checks (for testing only)
export BYPASS_AUTH=false
export BYPASS_GROUP_CHECK=false

# Mock data settings - useful for API testing
export USE_MOCK_DATA=false
export MOCK_API_ERRORS=false

# Display configuration message
echo "==================================================="
echo "Running WKRegnum Portal in LOCAL DEVELOPMENT MODE"
echo "==================================================="
echo "Configuration:"
echo "  - OAuth Authentication: $([ "$BYPASS_AUTH" = "true" ] && echo "BYPASSED" || echo "ENABLED")"
echo "  - Group Membership Checks: $([ "$BYPASS_GROUP_CHECK" = "true" ] && echo "BYPASSED" || echo "ENABLED")"
echo "  - Mock Data: $([ "$USE_MOCK_DATA" = "true" ] && echo "ENABLED" || echo "DISABLED")"
echo "  - API URL: $REGNUM_API_URL"
echo "  - Redirect URL: $REDIRECT_URL"
echo ""
if [ "$BYPASS_AUTH" = "true" ] || [ "$BYPASS_GROUP_CHECK" = "true" ]; then
    echo "⚠️  WARNING: Authentication bypasses are enabled!"
    echo "   This should only be used for local development and testing."
    echo "   Make sure to test with real authentication before deploying."
fi
echo "==================================================="

# Run the application
streamlit run Home.py 