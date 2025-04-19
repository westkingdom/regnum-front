import base64
import os.path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
IMPERSONATED_USER_EMAIL = "webminister@westkingdom.org"  # <<< --- CONFIGURE THIS

# Define paths for the service account key
SECRET_SA_KEY_PATH = '/secrets/service_account.json'
LOCAL_SA_KEY_PATH = 'regnum-service-account-key.json'  # Local fallback (ensure this file exists locally for testing)


def get_gmail_service():
    creds = None
    sa_key_path = SECRET_SA_KEY_PATH if os.path.exists(SECRET_SA_KEY_PATH) else LOCAL_SA_KEY_PATH

    if not os.path.exists(sa_key_path):
        error_msg = f"Service Account key file not found at {sa_key_path}. Cannot authenticate for email."
        print(error_msg)
        try:
            st.error(error_msg)
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
        print(f"Successfully loaded Service Account credentials, impersonating {IMPERSONATED_USER_EMAIL}")

    except Exception as e:
        error_msg = f"Error loading Service Account credentials from {sa_key_path}: {e}"
        print(error_msg)
        try:
            st.error(error_msg)
        except Exception:
            pass
        return None

    # Build the service if credentials exist
    if creds:
        try:
            service = build('gmail', 'v1', credentials=creds)
            print("Gmail service built successfully using Service Account.")
            return service
        except HttpError as error:
            print(f'An error occurred building the Gmail service: {error}')
            return None
        except Exception as e:
            print(f'An unexpected error occurred building service: {e}')
            return None
    else:
        # This case should ideally not be reached if the error handling above works
        print("Failed to obtain valid credentials.")
        return None


def create_message(sender, to, cc, subject, message_text):
    """Create a message for an email, including CC."""
    message = MIMEMultipart()
    message['to'] = to
    message['cc'] = cc
    # Set the 'From' header to the impersonated user
    message['from'] = sender
    message['subject'] = subject
    msg = MIMEText(message_text)
    message.attach(msg)
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw_message}


def send_message(service, user_id, message):
    """Send an email message using the impersonated user ID.

    Args:
      service: Authorized Gmail API service instance.
      user_id: User's email address to send as (should be the impersonated user).
               The special value "me" can also work if the service account itself
               has a G Suite license, but using the impersonated email is safer.
      message: Message to be sent.

    Returns:
      Sent Message object dictionary if successful, None otherwise.
    """
    try:
        # Use the impersonated user's email as the userId
        message = (service.users().messages().send(userId=user_id, body=message)
                   .execute())
        print(f'Message Id: {message["id"]} sent as {user_id}')
        return message
    except HttpError as error:
        print(f'An error occurred sending the email as {user_id}: {error}')
        if error.resp.status == 400:
            print("Error details:", error.content)
        # Check for common delegation errors
        if "Delegation denied" in str(error.content):
            print("Ensure Domain-Wide Delegation is correctly configured in Google Workspace Admin Console for the service account and scope.")
        return None
    except Exception as e:
        print(f'An unexpected error occurred during sending as {user_id}: {e}')
        return None


def send_registration_email(form_data: dict, group_name: str):
    """Constructs and sends the registration email using form data via Service Account."""
    print("Attempting to send registration email via Service Account...")
    service = get_gmail_service()  # Call the updated function
    if not service:
        print("Failed to get Gmail service. Email not sent.")
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

    # Create the message, setting the 'From' header to the impersonated user
    message = create_message(IMPERSONATED_USER_EMAIL, ADMIN_EMAIL, COMMUNICATIONS_EMAIL, subject, body)

    if message:
        print(f"Sending email as {IMPERSONATED_USER_EMAIL} to {ADMIN_EMAIL}, CC {COMMUNICATIONS_EMAIL}...")
        # Send the message using the impersonated user's email as the userId
        sent_message = send_message(service, IMPERSONATED_USER_EMAIL, message)
        if sent_message:
            print("Email sent successfully.")
            return True
        else:
            print("Failed to send email via Gmail API using Service Account.")
            try:
                st.error("Failed to send notification email via Gmail API.")
            except Exception:
                pass
            return False
    else:
        print("Failed to create email message.")
        return False
