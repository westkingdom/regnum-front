# Project Structure

## Root Directory
- **Home.py** - Main application entry point with authentication and welcome page
- **requirements.txt** - Primary Python dependencies (pip format)
- **Pipfile/Pipfile.lock** - Alternative dependency management (Pipenv)
- **Dockerfile** - Container configuration for deployment
- **docker-compose.yaml** - Local container orchestration
- **cloudbuild.yaml** - Google Cloud Build configuration
- **run_local_dev.sh** - Local development startup script

## Application Pages (`pages/`)
Streamlit multi-page application structure:
- **0_Login.py** - Authentication page
- **1_Groups.py** - Google Groups management
- **2_Regnum.py** - Officer roster management
- **5_Duty_Request.py** - Public duty request form
- **health.py** - Health check endpoint

## Utilities (`utils/`)
Core application logic and shared components:
- **auth.py** - Legacy authentication utilities
- **auth_middleware.py** - Authentication middleware
- **jwt_auth.py** - JWT token management and user authentication
- **config.py** - Application configuration and environment variables
- **logger.py** - Structured logging setup (JSON for production, readable for dev)
- **api.py** - API client and HTTP utilities
- **queries.py** - Database/API query functions
- **email.py** - Email sending via Gmail API
- **data_sanitizer.py** - Data cleaning and validation
- **password_hasher.py** - Password hashing utilities
- **recaptcha.py** - reCAPTCHA integration

## Configuration Files (`utils/`)
- **api.json** - API endpoint configurations
- **group_map_simplified.json** - Group mapping data
- **locations_data.json** - Location reference data

## Testing (`tests/`)
- **test_1_groups.py** - Group management tests
- **test_8_regnum.py** - Regnum/roster tests
- **test_data_sanitizer.py** - Data validation tests
- **test_gmail_api.py** - Email functionality tests

## Documentation (`docs/`)
- **AUTHENTICATION.md** - Authentication system documentation
- **DATA_SANITIZATION.md** - Data cleaning processes
- **GMAIL_API_SETUP.md** - Email configuration guide
- **PASSWORD_HASHING.md** - Security implementation details
- **SECURITY_SUMMARY.md** - Overall security overview

## Configuration Directories
- **.streamlit/** - Streamlit-specific configuration
- **.kiro/** - Kiro AI assistant configuration and steering rules
- **.vscode/** - VS Code editor settings

## Coding Conventions

### File Organization
- **Pages**: Follow Streamlit naming convention with numeric prefixes for ordering
- **Utilities**: Group related functionality in focused modules
- **Tests**: Mirror the structure of the code being tested

### Import Patterns
```python
import streamlit as st
from utils.logger import app_logger as logger
from utils.jwt_auth import require_authentication
from utils.config import api_url
```

### Authentication Pattern
All protected pages should start with:
```python
user = require_authentication()
logger.info(f"Accessing [page] - authenticated user: {user['email']}")
```

### Error Handling
- Use structured logging with appropriate log levels
- Provide user-friendly error messages in Streamlit UI
- Log detailed error information for debugging

### Environment Configuration
- Development: Use `run_local_dev.sh` for local environment setup
- Production: Configure via `cloudbuild.yaml` environment variables
- API endpoints configurable via `REGNUM_API_URL` environment variable