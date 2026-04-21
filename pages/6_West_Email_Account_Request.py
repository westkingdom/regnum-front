import streamlit as st
from utils.email import send_wk_email_account_request_email as _send_email
from utils.logger import app_logger as logger
from utils.recaptcha import require_recaptcha
from utils.data_sanitizer import sanitize_wk_email_request_form, sanitize_email

RECIPIENT_COMMUNICATIONS = "communications@westkingdom.org"
RECIPIENT_SITE = "regnum-site@westkingdom.org"


def _send(form_data: dict) -> bool:
    try:
        return _send_email(form_data)
    except ImportError:
        st.error("Error: The email sending function could not be imported. Email not sent.")
        return False
    except Exception as e:
        st.error(f"An error occurred while trying to send the email: {e}")
        return False


def main():
    logger.info("Accessing West Kingdom Email Account Request page - Public Access")

    st.set_page_config(page_title="West Kingdom Email Account Request")
    st.title("West Kingdom Email Account Request")

    st.markdown("""
    Use this form to request a new **@westkingdom.org** email address.
    Your request will be sent to the Kingdom Communications office.
    """)

    require_recaptcha()

    with st.form(key="wk_email_request_form", clear_on_submit=True):
        mundane_name = st.text_input(
            "Modern Name*",
            max_chars=100,
            help="Your legal name. Required. Max 100 characters.",
        )
        society_name = st.text_input(
            "Society Name*",
            max_chars=100,
            help="Your name as known in the SCA. Required. Max 100 characters.",
        )
        current_email = st.text_input(
            "Current Email Address*",
            max_chars=254,
            help="Your current email address. Required.",
        )
        requested_address = st.text_input(
            "Requested @westkingdom.org Address*",
            max_chars=64,
            help="The local part of the address you are requesting (e.g. firstname.lastname). Do not include @westkingdom.org. Required.",
        )

        st.markdown("---")
        st.markdown("*\\* Indicates required field.*")
        st.info("🔒 All form data is automatically sanitized for security before processing.")

        submitted = st.form_submit_button("Submit Request")

        if submitted:
            errors = []

            if not mundane_name.strip():
                errors.append("Modern Name is required.")
            if not society_name.strip():
                errors.append("Society Name is required.")
            if not current_email.strip():
                errors.append("Current Email Address is required.")
            if not requested_address.strip():
                errors.append("Requested @westkingdom.org Address is required.")

            if errors:
                for error in errors:
                    st.error(error)
            else:
                try:
                    raw_form_data = {
                        "mundane_name": mundane_name,
                        "society_name": society_name,
                        "current_email": current_email,
                        "requested_address": requested_address,
                    }

                    st.info("🔒 Sanitizing and validating form data...")
                    sanitized_form_data = sanitize_wk_email_request_form(raw_form_data)

                    st.info("📧 Submitting request and sending email notification...")
                    logger.info(
                        f"Processing WK email account request for: {sanitized_form_data.get('current_email')}"
                    )

                    success = _send(sanitized_form_data)

                    if success:
                        st.success("✅ Request submitted successfully!")
                        st.success("📧 Your request has been sent to:")
                        st.write(f"- {RECIPIENT_COMMUNICATIONS}")
                        st.write(f"- {RECIPIENT_SITE} (copy)")
                        logger.info(
                            f"WK email account request processed for: {sanitized_form_data.get('current_email')}"
                        )
                    else:
                        st.error("❌ There was an error submitting your request or sending the notification.")
                        st.error("Please check error messages above or contact the administrator.")
                        logger.error(
                            f"Failed to process WK email account request for: {sanitized_form_data.get('current_email')}"
                        )

                except ValueError as e:
                    st.error(f"❌ Data validation failed: {str(e)}")
                    st.warning("Please check your input and try again.")
                    logger.warning(f"Data sanitization failed for WK email account request: {str(e)}")

                except Exception as e:
                    st.error("❌ An unexpected error occurred while processing your request.")
                    st.error("Please try again or contact the administrator if the problem persists.")
                    logger.error(f"Unexpected error processing WK email account request: {str(e)}")


if __name__ == "__main__":
    main()
