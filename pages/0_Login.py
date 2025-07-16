import streamlit as st
from utils.jwt_auth import login_user, logout_user, is_authenticated, get_current_user
from utils.logger import app_logger as logger

# Set page configuration
st.set_page_config(page_title="Login - WKRegnum", page_icon="🔐")

def main():
    """Main login page logic"""
    st.title("🔐 WKRegnum Login")
    
    # Check if user is already authenticated
    if is_authenticated():
        user = get_current_user()
        st.success(f"You are already logged in as {user['name']}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Go to Home Page"):
                st.switch_page("Home.py")
        with col2:
            if st.button("Logout"):
                logout_user()
                st.rerun()
        
        st.info("Use the sidebar to navigate to other pages.")
        return
    
    # Show login form
    st.markdown("### Please log in to access the WKRegnum Portal")
    
    # Demo credentials info
    with st.expander("Demo Credentials", expanded=True):
        st.markdown("""
        **Administrator Account:**
        - Email: `admin@westkingdom.org`
        - Password: `admin123`
        
        **User Account:**
        - Email: `user@westkingdom.org`
        - Password: `user123`
        """)
    
    with st.form("login_form"):
        st.subheader("Login")
        email = st.text_input(
            "Email Address", 
            placeholder="user@westkingdom.org",
            help="Enter your West Kingdom email address"
        )
        password = st.text_input(
            "Password", 
            type="password",
            help="Enter your password"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("Login", use_container_width=True)
        with col2:
            if st.form_submit_button("Public Duty Request", use_container_width=True):
                st.switch_page("pages/5_Duty_Request.py")
        
        if submit:
            if not email or not password:
                st.error("Please enter both email and password")
            else:
                with st.spinner("Authenticating..."):
                    if login_user(email, password):
                        st.success("Login successful! Redirecting...")
                        logger.info(f"User logged in successfully: {email}")
                        st.rerun()
                    else:
                        st.error("Invalid email or password. Please try again.")
                        logger.warning(f"Failed login attempt for: {email}")
    
    st.markdown("---")
    st.markdown("### Public Access")
    st.info("The Duty Request form is available without login.")
    if st.button("Access Duty Request Form"):
        st.switch_page("pages/5_Duty_Request.py")

if __name__ == "__main__":
    main()