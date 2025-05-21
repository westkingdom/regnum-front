import streamlit as st
import re
from typing import Dict, Any # Import typing
# Assume the email sending logic is encapsulated in this function
# Make sure this import points to the actual function if it exists
from utils.email import send_duty_request_email as actual_send_duty_request_email
from utils.logger import app_logger as logger
from utils.auth_middleware import require_auth
import os

# Get OAuth flow function for authentication middleware
def get_flow():
    from google_auth_oauthlib.flow import Flow
    SECRET_CREDENTIALS_PATH = '/oauth/google_credentials.json'
    LOCAL_CREDENTIALS_PATH = 'utils/google_credentials.json'
    credentials_path = SECRET_CREDENTIALS_PATH if os.path.exists(SECRET_CREDENTIALS_PATH) else LOCAL_CREDENTIALS_PATH
    
    try:
        flow = Flow.from_client_secrets_file(
            credentials_path,
            scopes=['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile'],
            redirect_uri=os.environ.get('REDIRECT_URL', 'https://regnum-front-85382560394.us-west1.run.app')
        )
        return flow
    except Exception as e:
        logger.error(f"Failed to create OAuth flow: {str(e)}")
        st.error(f"Authentication error: {e}")
        st.stop()

# --- Placeholder/Wrapper for the actual email sending function ---
# This allows testing/simulation if the real function isn't ready or if
# you want to avoid sending real emails during development/testing.
# In production, you might remove this wrapper and import directly,
# or have the real function handle simulation via a flag/env var.
USE_SIMULATED_EMAIL = False # Set to False to use the actual email function

def send_duty_request_email(form_data: Dict[str, Any], user_email: str) -> bool:
    """
    Sends or simulates sending the duty request email based on USE_SIMULATED_EMAIL flag.

    If USE_SIMULATED_EMAIL is True, it prints debug info and simulates success.
    If False, it calls the actual email sending function imported from utils.email.

    Args:
        form_data: A dictionary containing all the validated form fields.
        user_email: The email address provided by the user in the form.

    Returns:
        True if the email was sent (or simulated) successfully, False otherwise.
    """
    if USE_SIMULATED_EMAIL:
        logger.info("Simulating email dispatch")
        st.info("Simulating email dispatch...")
        logger.debug("--- Sending Duty Request Email (Simulated) ---")
        recipients = [user_email, RECIPIENT_COMMUNICATIONS, RECIPIENT_SITE]
        logger.debug(f"To: {', '.join(recipients)}")
        logger.debug(f"Subject: New Regnum Duty/Job Request")
        logger.debug(f"From: {form_data['Mundane Name']} ({form_data['West Kingdom Google Email']})")
        logger.debug(f"Requested Job: {form_data['Requested Job']}")
        
        import time
        time.sleep(1) # Simulate network delay
        return True # Simulate success
    else:
        # Call the actual imported function
        logger.info(f"Sending duty request email for {user_email}")
        # Ensure the actual function exists and handles potential errors
        try:
             # You might need to adjust args/kwargs based on the real function's signature
            return actual_send_duty_request_email(form_data, user_email)
        except ImportError:
            logger.error("Email sending function could not be imported")
            st.error("Error: The actual email sending function could not be imported. Email not sent.")
            return False
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            st.error(f"An error occurred while trying to send the email: {e}")
            return False


# --- Email Validation ---
def is_valid_wk_email(email: str) -> bool:
    """
    Validates if a string is a syntactically valid email address ending with '@westkingdom.org'.

    Args:
        email: The email string to validate.

    Returns:
        True if the email format is valid and the domain is '@westkingdom.org' (case-insensitive),
        False otherwise. Returns False if input is not a string.
    """
    if not isinstance(email, str):
        return False
    # Basic regex for email format and specific domain (case-insensitive)
    pattern = r'^[a-zA-Z0-9._%+-]+@westkingdom\.org$'
    return bool(re.match(pattern, email, re.IGNORECASE))


# Define recipient addresses (used in messages, actual recipients handled by email function)
RECIPIENT_COMMUNICATIONS = "communications@westkingdom.org"
RECIPIENT_SITE = "regnum-site@westkingdom.org"

# Apply authentication protection
@require_auth(get_flow)
def main():
    """Main application logic for Duty Request page."""
    logger.info("Accessing Duty Request page")
    
    # --- Streamlit Form Page ---
    st.set_page_config(page_title="Duty Request Form")
    st.title("Duty/Job Request Form")
    
    # Display explicit warning about requiring westkingdom.org account
    st.warning("You must be logged in with a @westkingdom.org Google account to access this application.")
    
    st.markdown("""
    Use this form to request assignment to a new duty or job within the Kingdom structure.
    Your request will be emailed to Communications and the Regnum Site administrators,
    and a copy will be sent to your West Kingdom email address.
    """)

    # Use st.form to group inputs and submit together
    with st.form(key="duty_request_form", clear_on_submit=True):
        st.subheader("Your Information")
        sca_name = st.text_input("Society Name*", help="Your name as known in the SCA. Required.")
        mundane_name = st.text_input("Mundane Name*", help="Your legal name. Required.")
        wk_email = st.text_input(
            "West Kingdom Google Email Address*",
            help="Your email ending in @westkingdom.org. Notifications will be sent here. Required."
        )
        contact_phone = st.text_input("Contact Phone Number (Optional)")

        st.subheader("Address Information")
        address = st.text_input("Mundane Street Address*", help="Required.")
        city = st.text_input("Mundane City*", help="Required.")
        state = st.text_input("Mundane State*", max_chars=2, help="e.g., CA, NV. Required.")
        zip_code = st.text_input("Mundane Zip Code*", help="Required.")

        st.subheader("Duty Location")
        principality = st.text_input("Principality where new duties apply*", help="Required.")
        barony = st.text_input("Barony where new duties apply (if applicable)")
        group = st.text_input("Group where new duties apply (if applicable)")

        st.subheader("Requested Duty")
        requested_job = st.text_area(
            "Specific Job/Duty you are requesting*",
            help="Please describe the specific role or task you are requesting. Required."
        )

        st.markdown("---")
        st.markdown("*\* Indicates required field.*")

        # Form submission button
        submitted = st.form_submit_button("Submit Request")

        if submitted:
            # --- Validation Logic ---
            errors = []
            # Check required fields
            if not sca_name: errors.append("Society Name is required.")
            if not mundane_name: errors.append("Mundane Name is required.")
            if not wk_email:
                errors.append("West Kingdom Google Email Address is required.")
            elif not is_valid_wk_email(wk_email):
                # is_valid_wk_email already checks format and domain
                errors.append("Please provide a valid email ending with @westkingdom.org.")
            if not address: errors.append("Mundane Street Address is required.")
            if not city: errors.append("Mundane City is required.")
            if not state: errors.append("Mundane State is required.")
            # Basic zip code validation (numeric, optional length check)
            if not zip_code:
                errors.append("Mundane Zip Code is required.")
            elif not zip_code.isdigit():
                errors.append("Zip Code should contain only numbers.")
            if not principality: errors.append("Principality is required.")
            if not requested_job: errors.append("Specific Job/Duty is required.")

            # --- Process Submission ---
            if errors:
                # Display all validation errors found
                logger.warning(f"Form validation failed with {len(errors)} errors")
                for error in errors:
                    st.error(error)
            else:
                # If valid, collect data into a dictionary
                logger.info(f"Duty request form valid for {wk_email}, processing")
                form_data = {
                    "Society Name": sca_name,
                    "Mundane Name": mundane_name,
                    "West Kingdom Google Email": wk_email,
                    "Contact Phone Number": contact_phone if contact_phone else "N/A",
                    "Mundane Address": address,
                    "Mundane City": city,
                    "Mundane State": state.upper(), # Standardize state casing
                    "Mundane Zip Code": zip_code,
                    "Principality": principality,
                    "Barony": barony if barony else "N/A",
                    "Group": group if group else "N/A",
                    "Requested Job": requested_job,
                }

                st.info("Submitting request and sending email notifications...")
                # Call the email sending function (wrapper or actual)
                success = send_duty_request_email(form_data, wk_email)

                if success:
                    logger.info(f"Duty request submitted successfully for {wk_email}")
                    st.success(f"Request submitted successfully! Email notifications sent to: {wk_email}, {RECIPIENT_COMMUNICATIONS}, and {RECIPIENT_SITE}.")
                    # Form clears automatically due to clear_on_submit=True
                else:
                    # Specific error should be shown by send_duty_request_email or its wrapper
                    logger.error(f"Failed to submit duty request for {wk_email}")
                    st.error("There was an error submitting your request or sending notifications. Please check error messages above or contact the administrator.")

# Call the main function if script is run directly
if __name__ == "__main__":
    main()
