import base64
import os
import os.path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import streamlit as st
from utils.logger import app_logger as logger
from utils.config import (
    ADMIN_EMAIL, COMMUNICATIONS_EMAIL, IMPERSONATED_USER_EMAIL,
    RECIPIENT_COMMUNICATIONS, RECIPIENT_SITE,
    SECRET_SA_KEY_PATH, LOCAL_SA_KEY_PATH,
)

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def get_gmail_service():
    env = os.environ.get('STREAMLIT_ENV', 'production')

    if os.path.exists(SECRET_SA_KEY_PATH):
        sa_key_path = SECRET_SA_KEY_PATH
    elif env == 'development' and LOCAL_SA_KEY_PATH and os.path.exists(LOCAL_SA_KEY_PATH):
        logger.warning(f"Using local SA key file for development: {LOCAL_SA_KEY_PATH}")
        sa_key_path = LOCAL_SA_KEY_PATH
    else:
        logger.error("Service account key not found. In production, mount via Secret Manager.")
        try:
            st.error("Service account key not found. Email notifications are unavailable.")
        except Exception:
            pass
        return None

    try:
        # Create credentials using the service account key file and impersonate the user
        creds = service_account.Credentials.from_service_account_file(
            sa_key_path,
            scopes=SCOPES,
            subject=IMPERSONATED_USER_EMAIL  # The user to impersonate
        )
    except Exception as e:
        try:
            st.error(f"Error loading Service Account credentials: {e}")
        except Exception:
            pass
        return None

    # Build the service if credentials exist
    if creds:
        try:
            service = build('gmail', 'v1', credentials=creds)
            return service
        except HttpError:
            return None
        except Exception:
            return None
    else:
        return None


def create_message(sender, to, cc, subject, message_text):
    """Create a message for an email, including CC."""
    message = MIMEMultipart()
    message['to'] = to
    message['cc'] = cc
    message['from'] = sender
    message['subject'] = subject
    msg = MIMEText(message_text)
    message.attach(msg)
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw_message}


def send_message(service, user_id, message):
    """Send an email message using the impersonated user ID."""
    if not service:
        return None

    try:
        # Use the impersonated user's email as the userId
        sent_message_response = (service.users().messages().send(userId=user_id, body=message)
                                 .execute())
        return sent_message_response
    except HttpError:
        return None
    except Exception:
        return None


def send_registration_email(form_data: dict, group_name: str):
    """Constructs and sends the registration email using form data via Service Account."""
    service = get_gmail_service()  # Call the updated function
    if not service:
        try:
            st.error("Failed to initialize email service. Notification not sent.")
        except Exception:
            pass
        return False

    subject = f"[Regnum Submission] New Member Registration for {group_name}: {form_data.get('sca_name', 'N/A')}"
    body_lines = [
        f"A new member registration has been submitted for the group: {group_name}",
        "--- Member Details ---",
        f"SCA Name: {form_data.get('sca_name', 'N/A')}",
        f"Modern Name: {form_data.get('modern_name', 'N/A')}",
        f"SCA Membership Number: {form_data.get('sca_membership_number', 'N/A')}",
        f"Westkingdom Email: {form_data.get('westkingdom_email', 'N/A')}",
        f"Contact Phone: {form_data.get('contact_phone_number', 'N/A')}",
        "\n--- Address ---",
        f"Street: {form_data.get('street_address', 'N/A')}",
        f"City: {form_data.get('city', 'N/A')}",
        f"State: {form_data.get('state', 'N/A')}",
        f"Zip Code: {form_data.get('zip_code', 'N/A')}",
        f"Country: {form_data.get('country', 'N/A')}",
        "\n--- Dates ---",
        f"Effective Date: {form_data.get('effective_date', 'N/A')}",
        f"End Date: {form_data.get('end_date', 'N/A')}",
    ]
    body = "\n".join(body_lines)

    message = create_message(IMPERSONATED_USER_EMAIL, ADMIN_EMAIL, COMMUNICATIONS_EMAIL, subject, body)

    if message:
        sent_message = send_message(service, IMPERSONATED_USER_EMAIL, message)
        if sent_message:
            return True
        else:
            try:
                # Display a more generic error to the user, details are in logs
                st.error("Failed to send notification email. Please check logs or contact admin.")
            except Exception:
                pass
            return False
    else:
        return False


def send_duty_request_email(form_data: dict, user_email: str) -> bool:
    """
    Sends the duty request email using Gmail API to the specified recipients.
    """
    # Check if we're in development mode
    if os.environ.get("STREAMLIT_ENV") == "development":
        try:
            st.warning("⚠️ Development Mode: Email sending simulation enabled.")
            st.info("📧 In production, this would send emails via Gmail API to:")
            st.write(f"- User: {user_email}")
            st.write(f"- Communications: {RECIPIENT_COMMUNICATIONS}")
            st.write(f"- Site Admin: {RECIPIENT_SITE}")
            st.success("✅ Form submission completed successfully (development mode)")
            return True
        except Exception:
            # Not in Streamlit context, just log and return True for dev mode
            print("Development mode: Email sending skipped")
            return True
    
    # Get Gmail service
    service = get_gmail_service()
    if not service:
        try:
            st.error("Failed to initialize Gmail service. Please contact the administrator.")
        except Exception:
            pass
        return False

    subject = "[Regnum Submission] New Duty/Job Request Submitted"
    recipients = [user_email, RECIPIENT_COMMUNICATIONS, RECIPIENT_SITE]

    def field(label, key):
        return f"{label}: {form_data.get(key) or 'N/A'}"

    body_lines = [
        "A new duty/job request has been submitted via the WKRegnum portal.",
        "",
        "--- Your Information ---",
        field("Society Name",           "Society Name"),
        field("Modern Name",            "Modern Name"),
        field("West Kingdom Email",     "West Kingdom Google Email"),
        field("Contact Phone",          "Contact Phone Number"),
        field("SCA Member Number",      "SCA Member Number"),
        "",
        "--- Address ---",
        field("Street Address",         "Mundane Address"),
        field("City",                   "Mundane City"),
        field("State",                  "Mundane State"),
        field("Postal Code",            "Mundane Zip Code"),
        "",
        "--- Duty Location ---",
        field("Principality",           "Principality"),
        field("Barony",                 "Barony"),
        field("Group",                  "Group"),
        "",
        "--- Requested Duty ---",
        field("Job / Duty Requested",   "Requested Job"),
        "",
        "--- Notification Recipients ---",
        f"User: {user_email}",
        f"Communications: {RECIPIENT_COMMUNICATIONS}",
        f"Site Admin: {RECIPIENT_SITE}",
        "",
        "This is an automated notification from the WKRegnum system.",
    ]
    
    body = "\n".join(body_lines)

    # Send email to each recipient individually for better delivery tracking
    success_count = 0
    total_recipients = len(recipients)
    
    for recipient in recipients:
        try:
            # Create message for this recipient
            message = create_message(IMPERSONATED_USER_EMAIL, recipient, "", subject, body)
            
            if message:
                sent_message = send_message(service, IMPERSONATED_USER_EMAIL, message)
                if sent_message:
                    success_count += 1
                    logger.info(f"Duty request email sent successfully to: {recipient}")
                else:
                    logger.error(f"Failed to send duty request email to: {recipient}")
            else:
                logger.error(f"Failed to create message for recipient: {recipient}")
                
        except Exception as e:
            logger.error(f"Error sending duty request email to {recipient}: {str(e)}")
    
    # Return True if at least one email was sent successfully
    if success_count > 0:
        if success_count == total_recipients:
            logger.info("All duty request emails sent successfully")
        else:
            logger.warning(f"Partial success: {success_count}/{total_recipients} emails sent")
        return True
    else:
        logger.error("Failed to send any duty request emails")
        try:
            st.error("Failed to send notification emails. Please contact the administrator.")
        except Exception:
            pass
        return False
