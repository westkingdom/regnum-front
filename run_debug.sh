#!/bin/bash

# Load environment variables from .env file if it exists
if [ -f .env ]; then
  echo "Loading environment variables from .env file..."
  export $(grep -v '^#' .env | xargs)
else
  echo "No .env file found, using default development settings..."
  # Set default environment variables for local development
  export USE_MOCK_DATA="false"
  export MOCK_API_ERRORS="true"
  export BYPASS_GROUP_CHECK="false"
  export REDIRECT_URL="http://localhost:8501"
  export STREAMLIT_SERVER_PORT="8501"
  export STREAMLIT_SERVER_HEADLESS="false"
  export STREAMLIT_BROWSER_GATHER_USAGE_STATS="false"
fi

# Enable more verbose logging for development
export PYTHONPATH=$(pwd)
export PYTHONUNBUFFERED=1
export STREAMLIT_LOG_LEVEL="info"

# Run the Streamlit application
echo "Starting WKRegnum in debug mode..."
echo "Access the application at http://localhost:8501"
streamlit run Home.py 