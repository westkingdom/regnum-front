import os

# Set required environment variables before any module is imported during test collection
os.environ.setdefault('JWT_SECRET', 'test-jwt-secret-for-unit-tests-only-not-for-production')
os.environ.setdefault('GOOGLE_CLIENT_ID', 'test-client-id.apps.googleusercontent.com')
os.environ.setdefault('GOOGLE_CLIENT_SECRET', 'test-client-secret')
os.environ.setdefault('STREAMLIT_ENV', 'development')
os.environ.setdefault('REGNUM_API_URL', 'http://localhost:8000')

# Pre-import utils.config so it is cached in sys.modules before any test manipulates env vars.
# Tests that call importlib.reload(cfg) rely on this cached reference being present.
import utils.config  # noqa: E402, F401
