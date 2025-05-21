#!/bin/bash
# Run the Streamlit application with group check bypass enabled
# This is for local development only

# Check if required packages are installed
if ! pip3 show streamlit &>/dev/null; then
  echo "ERROR: streamlit package not found. Please install it using:"
  echo "  pip install streamlit"
  exit 1
fi

# Set the environment variable to bypass group membership checks
export BYPASS_GROUP_CHECK=true

# Display a message explaining what's happening
echo "==================================================="
echo "Running Regnum Front in LOCAL DEVELOPMENT MODE"
echo "Group membership checks are BYPASSED for @westkingdom.org emails"
echo "This is for LOCAL TESTING ONLY and should not be used in production"
echo "==================================================="

# Run the Streamlit application
streamlit run Home.py 