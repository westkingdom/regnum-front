import requests
import streamlit as st
import os
from typing import Optional
from utils.logger import app_logger as logger

# reCAPTCHA Configuration
RECAPTCHA_SITE_KEY = os.environ.get('RECAPTCHA_SITE_KEY', 'your-site-key')
RECAPTCHA_SECRET_KEY = os.environ.get('RECAPTCHA_SECRET_KEY', 'your-secret-key')

def render_recaptcha() -> str:
    """Render Google reCAPTCHA widget and return the HTML"""
    recaptcha_html = f"""
    <div id="recaptcha-container">
        <div class="g-recaptcha" data-sitekey="{RECAPTCHA_SITE_KEY}"></div>
    </div>
    
    <script src="https://www.google.com/recaptcha/api.js" async defer></script>
    
    <script>
    function getRecaptchaResponse() {{
        return grecaptcha.getResponse();
    }}
    </script>
    """
    return recaptcha_html

def verify_recaptcha(recaptcha_response: str) -> bool:
    """Verify reCAPTCHA response with Google"""
    if not recaptcha_response:
        logger.warning("No reCAPTCHA response provided")
        return False
    
    # Skip verification in development mode
    if os.environ.get('STREAMLIT_ENV') == 'development':
        logger.info("Development mode: Skipping reCAPTCHA verification")
        return True
    
    try:
        verify_url = 'https://www.google.com/recaptcha/api/siteverify'
        data = {
            'secret': RECAPTCHA_SECRET_KEY,
            'response': recaptcha_response
        }
        
        response = requests.post(verify_url, data=data)
        result = response.json()
        
        if result.get('success'):
            logger.info("reCAPTCHA verification successful")
            return True
        else:
            logger.warning(f"reCAPTCHA verification failed: {result.get('error-codes', [])}")
            return False
            
    except Exception as e:
        logger.error(f"Error verifying reCAPTCHA: {str(e)}")
        return False

def show_recaptcha_widget():
    """Show reCAPTCHA widget in Streamlit"""
    if os.environ.get('STREAMLIT_ENV') == 'development':
        st.info("🔧 Development Mode: reCAPTCHA verification is disabled")
        st.checkbox("I'm not a robot (Development Mode)", value=True, disabled=True)
        return True
    
    st.markdown("### Security Verification")
    st.markdown("Please complete the reCAPTCHA verification below:")
    
    # In a real implementation, you'd need to handle the reCAPTCHA response
    # For now, we'll use a simple checkbox as a placeholder
    recaptcha_verified = st.checkbox("I'm not a robot")
    
    if recaptcha_verified:
        st.success("✅ reCAPTCHA verified")
        return True
    else:
        st.warning("Please complete the reCAPTCHA verification")
        return False

def require_recaptcha():
    """Require reCAPTCHA verification before proceeding"""
    if 'recaptcha_verified' not in st.session_state:
        st.session_state['recaptcha_verified'] = False
    
    if not st.session_state['recaptcha_verified']:
        if show_recaptcha_widget():
            st.session_state['recaptcha_verified'] = True
            st.rerun()
        else:
            st.stop()
    
    return True