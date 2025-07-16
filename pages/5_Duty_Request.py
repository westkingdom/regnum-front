import streamlit as st
import re
from typing import Dict, Any # Import typing
from utils.email import send_duty_request_email as actual_send_duty_request_email
from utils.logger import app_logger as logger
from utils.recaptcha import require_recaptcha
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
    Use this form to request assignment to a new duty or job within the Kingdom structure.
    Your request will be emailed to Communications and the Regnum Site administrators,
    and a copy will be sent to your West Kingdom email address.
    """)
    
    # Require reCAPTCHA verification before showing the form
    require_recaptcha()

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
                for error in errors:
                    st.error(error)
            else:
                # If valid, collect data into a dictionary
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
                # Call the email sending function
                success = send_duty_request_email(form_data, wk_email)

                if success:
                    st.success(f"Request submitted successfully! Email notifications sent to: {wk_email}, {RECIPIENT_COMMUNICATIONS}, and {RECIPIENT_SITE}.")
                    # Form clears automatically due to clear_on_submit=True
                else:
                    st.error("There was an error submitting your request or sending notifications. Please check error messages above or contact the administrator.")

# Call the main function if script is run directly
if __name__ == "__main__":
    main()
