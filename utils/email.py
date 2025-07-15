import base64
import os
import os.path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

# Use service account credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import streamlit as st  # Import streamlit for error display if needed

# Scope remains the same
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# --- Configuration ---
# Primary recipient
ADMIN_EMAIL = "webminister@westkingdom.org"
# CC recipient
COMMUNICATIONS_EMAIL = "communications@westkingdom.org"

# !!! IMPORTANT: Set the email address of the Google Workspace user the Service Account will impersonate !!!
# This user must exist in your Workspace. Emails will be sent *from* this address.
# Consider making this an environment variable set during deployment for flexibility.
IMPERSONATED_USER_EMAIL = "westkingdom@westkingdom.org"  # <<< --- CONFIGURE THIS

# Define paths for the service account key
SECRET_SA_KEY_PATH = '/secrets/sa/service_account.json'  # Updated path
LOCAL_SA_KEY_PATH = 'regnum-service-account-key.json'  # Local fallback remains the same

# Assuming you have email credentials stored securely (e.g., environment variables)
SMTP_SERVER = os.environ.get("SMTP_SERVER")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587)) # Default to 587 for TLS
SMTP_USERNAME = os.environ.get("SMTP_SENDER_EMAIL")
SMTP_PASSWORD = os.environ.get("SMTP_SENDER_PASSWORD")
SENDER_EMAIL = os.environ.get("SMTP_SENDER_EMAIL") # Or a specific 'From' address

RECIPIENT_COMMUNICATIONS = "communications@westkingdom.org"
RECIPIENT_SITE = "regnum-site@westkingdom.org"

def get_gmail_service():
    creds = None
    sa_key_path = SECRET_SA_KEY_PATH if os.path.exists(SECRET_SA_KEY_PATH) else LOCAL_SA_KEY_PATH

    if not os.path.exists(sa_key_path):
        try:
            st.error(f"Service Account key file not found at expected path: {sa_key_path}")
        except Exception:
            pass  # Ignore if not in Streamlit context
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
        f"Mundane Name: {form_data.get('mundane_name', 'N/A')}",
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
    Sends the duty request email to the specified recipients.
    Replace this with your actual email sending implementation (e.g., Gmail API).
    """
    # Check if we're in development mode and SMTP is not configured
    if os.environ.get("STREAMLIT_ENV") == "development" and not all([SMTP_SERVER, SMTP_USERNAME, SMTP_PASSWORD]):
        try:
            st.warning("⚠️ Development Mode: Email sending is disabled. SMTP credentials not configured.")
            st.info("📧 In production, this would send emails to:")
            st.write(f"- User: {user_email}")
            st.write(f"- Communications: {RECIPIENT_COMMUNICATIONS}")
            st.write(f"- Site Admin: {RECIPIENT_SITE}")
            st.success("✅ Form submission completed successfully (development mode)")
            return True
        except Exception:
            # Not in Streamlit context, just log and return True for dev mode
            print("Development mode: Email sending skipped")
            return True
    
    if not all([SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SENDER_EMAIL]):
         # In production, this is a real error
         try:
             st.error("Email configuration is incomplete. Please contact the administrator.")
         except Exception:
             pass
         return False

    subject = "New Duty/Job Request Submitted"
    recipients = [user_email, RECIPIENT_COMMUNICATIONS, RECIPIENT_SITE]

    # Format the body
    body_lines = [f"A new duty request has been submitted via the Regnum site:\n"]
    for key, value in form_data.items():
        body_lines.append(f"- {key.replace('_', ' ').title()}: {value}")
    body = "\n".join(body_lines)

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = ", ".join(recipients) # Comma-separated string for header

    try:
        # Example using smtplib with TLS (common setup)
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.ehlo() # Say hello
            server.starttls() # Enable security
            server.ehlo() # Say hello again after TLS
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipients, msg.as_string())
            return True
    except smtplib.SMTPAuthenticationError:
        return False
    except Exception:
        return False
