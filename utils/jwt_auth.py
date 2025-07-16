import jwt
import streamlit as st
from datetime import datetime, timedelta
import os
from typing import Optional, Dict, Any
import hashlib
import hmac
from utils.logger import app_logger as logger

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

# Simple user database (in production, use a proper database)
USERS_DB = {
    'admin@westkingdom.org': {
        'password_hash': 'admin123',  # In production, use proper password hashing
        'name': 'Administrator',
        'role': 'admin'
    },
    'user@westkingdom.org': {
        'password_hash': 'user123',
        'name': 'User',
        'role': 'user'
    }
}

def hash_password(password: str) -> str:
    """Simple password hashing (use bcrypt in production)"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash"""
    # For demo purposes, using simple comparison
    # In production, use proper password verification
    return password == password_hash

def create_jwt_token(user_email: str, user_data: Dict[str, Any]) -> str:
    """Create JWT token for authenticated user"""
    payload = {
        'email': user_email,
        'name': user_data['name'],
        'role': user_data['role'],
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    logger.info(f"JWT token created for user: {user_email}")
    return token

def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token has expired")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Invalid JWT token")
        return None

def authenticate_user(email: str, password: str) -> Optional[str]:
    """Authenticate user and return JWT token if successful"""
    if email in USERS_DB:
        user_data = USERS_DB[email]
        if verify_password(password, user_data['password_hash']):
            token = create_jwt_token(email, user_data)
            logger.info(f"User authenticated successfully: {email}")
            return token
    
    logger.warning(f"Authentication failed for user: {email}")
    return None

def get_current_user() -> Optional[Dict[str, Any]]:
    """Get current authenticated user from session state"""
    if 'jwt_token' in st.session_state:
        user_data = verify_jwt_token(st.session_state['jwt_token'])
        if user_data:
            return user_data
        else:
            # Token is invalid or expired, clear session
            clear_session()
    return None

def clear_session():
    """Clear authentication session"""
    keys_to_remove = ['jwt_token', 'user_email', 'user_name', 'user_role', 'is_authenticated']
    for key in keys_to_remove:
        if key in st.session_state:
            del st.session_state[key]

def login_user(email: str, password: str) -> bool:
    """Login user and set session state"""
    token = authenticate_user(email, password)
    if token:
        user_data = verify_jwt_token(token)
        if user_data:
            st.session_state['jwt_token'] = token
            st.session_state['user_email'] = user_data['email']
            st.session_state['user_name'] = user_data['name']
            st.session_state['user_role'] = user_data['role']
            st.session_state['is_authenticated'] = True
            return True
    return False

def logout_user():
    """Logout user and clear session"""
    logger.info(f"User logged out: {st.session_state.get('user_email', 'Unknown')}")
    clear_session()

def require_authentication():
    """Decorator/function to require authentication for pages"""
    user = get_current_user()
    if not user:
        st.error("🔒 Authentication Required")
        st.info("Please log in to access this page.")
        
        # Show login form
        with st.form("login_form"):
            st.subheader("Login")
            email = st.text_input("Email", placeholder="user@westkingdom.org")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if login_user(email, password):
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid email or password")
        
        st.stop()
    
    return user

def is_authenticated() -> bool:
    """Check if user is authenticated"""
    return get_current_user() is not None