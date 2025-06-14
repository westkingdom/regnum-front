import os

# API endpoint URLs
api_url = os.environ.get('REGNUM_API_URL', 'https://regnum-api-njxuammdla-uw.a.run.app')

# Base URL for the application
base_url = os.environ.get('BASE_URL', 'https://wkregnum-njxuammdla-uw.a.run.app')

# Legacy group configuration (kept for compatibility with existing code)
REGNUM_ADMIN_GROUP = os.environ.get('REGNUM_ADMIN_GROUP', '00kgcv8k1r9idky')

# Legacy bypass setting (always True for public access)
BYPASS_GROUP_CHECK = True
