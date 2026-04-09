#!/bin/bash
# Run the WKRegnum application for local development

set -e

ENV_FILE="$(dirname "$0")/.env.local"

if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: .env.local not found."
    echo "Copy .env.local.example to .env.local and fill in your values."
    exit 1
fi

# Load environment variables from .env.local
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

echo "==================================================="
echo "Running WKRegnum Portal in LOCAL DEVELOPMENT MODE"
echo "==================================================="
echo "  API URL:      $REGNUM_API_URL"
echo "  Base URL:     $BASE_URL"
echo "  reCAPTCHA:    Disabled (development mode)"
echo ""
echo "Dev Login Credentials:"
echo "  Admin: admin@westkingdom.org / admin123"
echo "  User:  user@westkingdom.org  / user123"
echo "==================================================="

# Run the application using uv
uv run streamlit run Home.py
