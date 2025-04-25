import base64
import os.path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json  # Import json for pretty printing

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


def get_gmail_service():
    creds = None
    sa_key_path = SECRET_SA_KEY_PATH if os.path.exists(SECRET_SA_KEY_PATH) else LOCAL_SA_KEY_PATH

    if not os.path.exists(sa_key_path):
        error_msg = f"DEBUG: Service Account key file not found at expected path: {sa_key_path}"
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
        print(f"DEBUG: Successfully loaded Service Account credentials from {sa_key_path}, impersonating {IMPERSONATED_USER_EMAIL}")

    except Exception as e:
        error_msg = f"DEBUG: Error loading Service Account credentials from {sa_key_path}: {e}"
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
            print("DEBUG: Gmail service built successfully using Service Account.")
            return service
        except HttpError as error:
            print(f'DEBUG: An HTTP error occurred building the Gmail service: {error}')
            return None
        except Exception as e:
            print(f'DEBUG: An unexpected error occurred building service: {e}')
            return None
    else:
        print("DEBUG: Failed to obtain valid credentials in get_gmail_service.")
        return None


def create_message(sender, to, cc, subject, message_text):
    """Create a message for an email, including CC."""
    print(f"DEBUG: create_message called with sender='{sender}', to='{to}', cc='{cc}', subject='{subject}'")
    message = MIMEMultipart()
    message['to'] = to
    message['cc'] = cc
    message['from'] = sender
    message['subject'] = subject
    msg = MIMEText(message_text)
    message.attach(msg)
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    print("DEBUG: Raw message created for sending.")
    # Optionally print part of the raw message for verification, be careful with large messages
    # print(f"DEBUG: Raw message snippet (first 100 chars): {raw_message[:100]}")
    return {'raw': raw_message}


def send_message(service, user_id, message):
    """Send an email message using the impersonated user ID with added debugging."""
    print(f"DEBUG: send_message called for user_id='{user_id}'.")
    # Optionally print the message structure being sent (can be large)
    # try:
    #     print(f"DEBUG: Sending message body structure: {json.dumps(message, indent=2)}")
    # except Exception as json_e:
    #     print(f"DEBUG: Could not JSON dump message body: {json_e}")

    if not service:
        print("DEBUG: Error in send_message - Gmail service object is None.")
        return None

    try:
        print(f"DEBUG: Attempting service.users().messages().send(userId='{user_id}', ...)")
        # Use the impersonated user's email as the userId
        sent_message_response = (service.users().messages().send(userId=user_id, body=message)
                                 .execute())
        print(f"DEBUG: Gmail API send successful. Response: {sent_message_response}")
        if sent_message_response and 'id' in sent_message_response:
             print(f'DEBUG: Message Id: {sent_message_response["id"]} sent as {user_id}')
        return sent_message_response
    except HttpError as error:
        print(f"DEBUG: HttpError occurred sending the email as {user_id}. Status: {error.resp.status}")
        error_content = "N/A"
        try:
            # Attempt to decode error content for more details
            error_content = error.content.decode('utf-8')
            print(f"DEBUG: HttpError details: {error_content}")
        except Exception as decode_err:
            print(f"DEBUG: Could not decode HttpError content: {decode_err}. Raw content: {error.content}")

        # Check for common delegation errors more explicitly
        if "Delegation denied" in error_content:
            print("DEBUG: Delegation denied error detected. Check Google Workspace Admin Console Domain-Wide Delegation settings.")
            print(f"DEBUG: Ensure Client ID for the service account is authorized for scope: {SCOPES}")
            print(f"DEBUG: Ensure the impersonated user ({user_id}) exists and is active in the Workspace.")
        elif error.resp.status == 400:
            print("DEBUG: Received HTTP 400 Bad Request. Check message format, recipients, and API usage.")
        elif error.resp.status == 403:
             print("DEBUG: Received HTTP 403 Forbidden. Check API permissions, scopes, and potential quota issues.")
        # Add more specific checks if needed

        return None
    except Exception as e:
        # Catch any other unexpected errors during the send process
        print(f'DEBUG: An unexpected non-HTTP error occurred during sending as {user_id}: {type(e).__name__} - {e}')
        import traceback
        print("DEBUG: Traceback:")
        traceback.print_exc()  # Print the full traceback for unexpected errors
        return None


def send_registration_email(form_data: dict, group_name: str):
    """Constructs and sends the registration email using form data via Service Account."""
    print("DEBUG: send_registration_email called.")
    service = get_gmail_service()  # Call the updated function
    if not service:
        print("DEBUG: Failed to get Gmail service in send_registration_email. Email not sent.")
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
        print(f"DEBUG: Sending email via send_message function as {IMPERSONATED_USER_EMAIL} to {ADMIN_EMAIL}, CC {COMMUNICATIONS_EMAIL}...")
        sent_message = send_message(service, IMPERSONATED_USER_EMAIL, message)
        if sent_message:
            print("DEBUG: Email sent successfully confirmed by send_registration_email.")
            return True
        else:
            print("DEBUG: send_message returned failure in send_registration_email.")
            try:
                # Display a more generic error to the user, details are in logs
                st.error("Failed to send notification email. Please check logs or contact admin.")
            except Exception:
                pass
            return False
    else:
        print("DEBUG: Failed to create email message in send_registration_email.")
        return False
