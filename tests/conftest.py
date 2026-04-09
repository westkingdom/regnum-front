import os

# Set required environment variables before any module is imported during test collection
os.environ.setdefault('JWT_SECRET', 'test-jwt-secret-for-unit-tests-only-not-for-production')
os.environ.setdefault('USERS_DB_JSON', '{}')
os.environ.setdefault('STREAMLIT_ENV', 'development')
os.environ.setdefault('REGNUM_API_URL', 'http://localhost:8000')
