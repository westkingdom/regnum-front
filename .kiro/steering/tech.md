# Technology Stack

## Core Framework
- **Frontend**: Streamlit 1.39.0 - Python web framework for data applications
- **Backend API**: FastAPI with uvicorn server
- **Python Version**: 3.11

## Key Dependencies
- **Authentication**: PyJWT 2.8.0, bcrypt 4.1.2, streamlit-authenticator 0.3.2
- **Google Services**: google-auth, google-auth-oauthlib, google-api-python-client
- **Data Processing**: pandas 2.2.3, numpy 2.1.2
- **HTTP/Networking**: requests 2.32.3, aiohttp 3.10.10
- **Logging**: google-cloud-logging 3.11.3

## Deployment & Infrastructure
- **Containerization**: Docker with Python 3.11-slim base image
- **Cloud Platform**: Google Cloud Run
- **Build System**: Google Cloud Build with cloudbuild.yaml
- **Registry**: Google Artifact Registry (us-west1)
- **Load Balancing**: Kubernetes load balancer configuration

## Development Environment
- **Package Management**: pip with requirements.txt (primary), Pipenv as alternative
- **Environment Variables**: Managed via shell scripts and Cloud Run environment
- **Logging**: Structured JSON logging in production, human-readable in development

## Common Commands

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run local development server
./run_local_dev.sh

# Access application
http://localhost:8501
```

### Docker Operations
```bash
# Build container
docker build -t regnum-image .

# Run with docker-compose
docker-compose up
```

### Cloud Deployment
```bash
# Deploy to Cloud Run
gcloud builds submit --config cloudbuild.yaml

# View logs
gcloud logs read --service=regnum-front --limit=50
```

### Testing
```bash
# Run tests (pytest framework used)
python -m pytest tests/

# Specific test files
python -m pytest tests/test_1_groups.py
python -m pytest tests/test_data_sanitizer.py
```

## Configuration Management
- **Environment Variables**: Set via run_local_dev.sh for development
- **Production Config**: Managed through cloudbuild.yaml substitutions
- **API Endpoints**: Configurable via REGNUM_API_URL environment variable
- **Authentication**: JWT secrets and reCAPTCHA keys via environment variables