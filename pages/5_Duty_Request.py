import streamlit as st
import re
from typing import Dict, Any # Import typing
from utils.email import send_duty_request_email as actual_send_duty_request_email
from utils.logger import app_logger as logger
from utils.recaptcha import require_recaptcha
from utils.data_sanitizer import sanitize_duty_request_form, sanitize_email
import os

def send_duty_request_email(form_data: Dict[str, Any], user_email: str) -> bool:
    """
    Sends the duty request email.

    Args:
        form_data: A dictionary containing all the validated form fields.
        user_email: The email address provided by the user in the form.

    Returns:
        True if the email was sent successfully, False otherwise.
    """
    try:
        return actual_send_duty_request_email(form_data, user_email)
    except ImportError:
        st.error("Error: The actual email sending function could not be imported. Email not sent.")
        return False
    except Exception as e:
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

def main():
    """Main application logic for Duty Request page."""
    logger.info("Accessing Duty Request page - Public Access")
    
    # --- Streamlit Form Page ---
    st.set_page_config(page_title="Duty Request Form")
    st.title("Duty/Job Request Form")
    
    # Show public access notice
    st.info("📋 This form is publicly accessible. No login required.")
    
    st.markdown("""
    Use this form to request assignment to a new duty or job within the Kingdom of the West.
    Your request will be emailed to Communications and the Regnum Site administrators,
    and a copy will be sent to your West Kingdom email address.
    """)
    
    # Require reCAPTCHA verification before showing the form
    require_recaptcha()

    # Use st.form to group inputs and submit together
    with st.form(key="duty_request_form", clear_on_submit=True):
        st.subheader("Your Information")
        sca_name = st.text_input(
            "Society Name*", 
            max_chars=100,
            help="Your name as known in the SCA. Required. Max 100 characters."
        )
        mundane_name = st.text_input(
            "Mundane Name*", 
            max_chars=100,
            help="Your legal name. Required. Max 100 characters."
        )
        wk_email = st.text_input(
            "West Kingdom Google Email Address*",
            max_chars=254,
            help="Your email ending in @westkingdom.org. Notifications will be sent here. Required."
        )
        contact_phone = st.text_input(
            "Contact Phone Number (Optional)",
            max_chars=20,
            help="Optional. Format: (555) 123-4567 or 555-123-4567"
        )
        member_num = st.text_input(
            "SCA Member Number*",
            max_chars=10,
            help="Your SCA membership number. Required for officer positions."
        )

        st.subheader("Address Information")
        address = st.text_input(
            "Mundane Street Address*", 
            max_chars=200,
            help="Required. Max 200 characters."
        )
        city = st.text_input(
            "Mundane City*", 
            max_chars=100,
            help="Required. Max 100 characters."
        )
        state = st.text_input(
            "Mundane State*", 
            max_chars=50,
            help="e.g., CA, NV, California, Nevada. Required."
        )
        zip_code = st.text_input(
            "Mundane Zip Code*", 
            max_chars=10,
            help="Required. Numbers only or with hyphens (e.g., 12345 or 12345-6789)."
        )

        st.subheader("Duty Location")
        principality = st.text_input(
            "Principality where new duties apply*", 
            max_chars=500,
            help="Required. Max 500 characters."
        )
        barony = st.text_input(
            "Barony where new duties apply (if applicable)",
            max_chars=500,
            help="Optional. Max 500 characters."
        )
        group = st.text_input(
            "Group where new duties apply (if applicable)",
            max_chars=500,
            help="Optional. Max 500 characters."
        )

        st.subheader("Requested Duty")
        requested_job = st.text_area(
            "Specific Job/Duty you are requesting*",
            max_chars=2000,
            help="Please describe the specific role or task you are requesting. Required. Max 2000 characters."
        )

        st.markdown("---")
        st.markdown("*\* Indicates required field.*")
        
        # Security notice
        st.info("🔒 All form data is automatically sanitized for security before processing.")

        # Form submission button
        submitted = st.form_submit_button("Submit Request")

        if submitted:
            # --- Basic Validation Logic ---
            errors = []
            
            # Check required fields are not empty
            if not sca_name.strip(): 
                errors.append("Society Name is required.")
            if not mundane_name.strip(): 
                errors.append("Mundane Name is required.")
            if not wk_email.strip():
                errors.append("West Kingdom Google Email Address is required.")
            elif not is_valid_wk_email(wk_email):
                errors.append("Please provide a valid email ending with @westkingdom.org.")
            if not address.strip(): 
                errors.append("Mundane Street Address is required.")
            if not city.strip(): 
                errors.append("Mundane City is required.")
            if not state.strip(): 
                errors.append("Mundane State is required.")
            if not zip_code.strip():
                errors.append("Mundane Zip Code is required.")
            if not principality.strip(): 
                errors.append("Principality is required.")
            if not requested_job.strip(): 
                errors.append("Specific Job/Duty is required.")
            if not member_num.strip():
                errors.append("SCA Member Number is required for officer positions.")

            # --- Process Submission ---
            if errors:
                # Display all validation errors found
                for error in errors:
                    st.error(error)
            else:
                try:
                    # Prepare raw form data for sanitization
                    raw_form_data = {
                        'sca_name': sca_name,
                        'mundane_name': mundane_name,
                        'wk_email': wk_email,
                        'contact_phone': contact_phone,
                        'address': address,
                        'city': city,
                        'state': state,
                        'zip_code': zip_code,
                        'principality': principality,
                        'barony': barony,
                        'group': group,
                        'requested_job': requested_job,
                        'member_num': member_num,
                    }
                    
                    st.info("🔒 Sanitizing and validating form data...")
                    
                    # Sanitize all form data
                    sanitized_form_data = sanitize_duty_request_form(raw_form_data)
                    
                    # Additional email validation using sanitizer
                    sanitized_email = sanitize_email(wk_email)
                    
                    st.info("📧 Submitting request and sending email notifications...")
                    logger.info(f"Processing sanitized duty request for: {sanitized_email}")
                    
                    # Call the email sending function with sanitized data
                    success = send_duty_request_email(sanitized_form_data, sanitized_email)

                    if success:
                        st.success(f"✅ Request submitted successfully!")
                        st.success(f"📧 Email notifications sent to:")
                        st.write(f"- {sanitized_email}")
                        st.write(f"- {RECIPIENT_COMMUNICATIONS}")
                        st.write(f"- {RECIPIENT_SITE}")
                        logger.info(f"Duty request successfully processed for: {sanitized_email}")
                        # Form clears automatically due to clear_on_submit=True
                    else:
                        st.error("❌ There was an error submitting your request or sending notifications.")
                        st.error("Please check error messages above or contact the administrator.")
                        logger.error(f"Failed to process duty request for: {sanitized_email}")
                        
                except ValueError as e:
                    # Data sanitization failed
                    st.error(f"❌ Data validation failed: {str(e)}")
                    st.warning("Please check your input and try again. Ensure all fields contain valid data.")
                    logger.warning(f"Data sanitization failed for duty request: {str(e)}")
                    
                except Exception as e:
                    # Unexpected error
                    st.error("❌ An unexpected error occurred while processing your request.")
                    st.error("Please try again or contact the administrator if the problem persists.")
                    logger.error(f"Unexpected error processing duty request: {str(e)}")

# Call the main function if script is run directly
if __name__ == "__main__":
    main()
