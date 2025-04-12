import base64
import os.path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart  # Import MIMEMultipart

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
# Replace with the email address that should receive the primary notification
ADMIN_EMAIL = "your_admin_email@example.com"  # <<< --- IMPORTANT: Configure this email address
# Email address for the copy
COMMUNICATIONS_EMAIL = "communications@westkingdom.org"

def get_gmail_service():
    """Shows basic usage of the Gmail API.
    Initializes the Gmail service using credentials.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    token_path = 'token.json'
    creds_path = 'credentials.json'
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        except Exception as e:
            print(f"Error loading token.json: {e}. Re-authenticating.")
            creds = None  # Force re-authentication
            if os.path.exists(token_path):
                os.remove(token_path)  # Remove potentially corrupted token file

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Error refreshing token: {e}. Re-authenticating.")
                # If refresh fails, force re-authentication
                if not os.path.exists(creds_path):
                    raise FileNotFoundError(f"Error: {creds_path} not found. Please download it from Google Cloud Console and place it in the root directory.")
                flow = InstalledAppFlow.from_client_secrets_file(
                    creds_path, SCOPES)
                creds = flow.run_local_server(port=0)
        else:
            # Make sure 'credentials.json' is in the same directory
            # Download this file from your Google Cloud Console project
            if not os.path.exists(creds_path):
                raise FileNotFoundError(f"Error: {creds_path} not found. Please download it from Google Cloud Console and place it in the root directory.")
            flow = InstalledAppFlow.from_client_secrets_file(
                creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        try:
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        except Exception as e:
            print(f"Error saving token.json: {e}")

    try:
        service = build('gmail', 'v1', credentials=creds)
        return service
    except HttpError as error:
        print(f'An error occurred building the Gmail service: {error}')
        return None
    except Exception as e:
        print(f'An unexpected error occurred: {e}')
        return None


def create_message(sender, to, cc, subject, message_text):
    """Create a message for an email, including CC.

    Args:
      sender: Email address of the sender.
      to: Email address of the primary receiver.
      cc: Email address of the CC receiver.
      subject: The subject of the email message.
      message_text: The text of the email message.

    Returns:
      An object containing a base64url encoded email object.
    """
    # Using MIMEMultipart allows setting To and Cc headers correctly
    message = MIMEMultipart()
    message['to'] = to
    message['cc'] = cc  # Add the Cc header
    message['from'] = sender
    message['subject'] = subject

    # Attach the message text
    msg = MIMEText(message_text)
    message.attach(msg)

    # Encode the message in base64url
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw_message}

def send_message(service, user_id, message):
    """Send an email message.

    Args:
      service: Authorized Gmail API service instance.
      user_id: User's email address. The special value "me"
      can be used to indicate the authenticated user.
      message: Message to be sent.

    Returns:
      Sent Message object dictionary if successful, None otherwise.
    """
    try:
        message = (service.users().messages().send(userId=user_id, body=message)
                   .execute())
        print(f'Message Id: {message["id"]}')
        return message
    except HttpError as error:
        print(f'An error occurred sending the email: {error}')
        # Check for specific errors like invalid recipient
        if error.resp.status == 400:
            print("Error details:", error.content)
        return None
    except Exception as e:
        print(f'An unexpected error occurred during sending: {e}')
        return None

def send_registration_email(form_data: dict, group_name: str):
    """Constructs and sends the registration email using form data to Admin and CCs Communications."""
    service = get_gmail_service()
    if not service:
        print("Failed to get Gmail service. Email not sent.")
        return False

    # Add prefix to the subject line
    subject = f"[Regnum Submission] New Member Registration for {group_name}: {form_data.get('sca_name', 'N/A')}"

    body_lines = [
        f"{group_name} Addition Form Submission",
        "-------------------------------------",
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
        # Add other fields as needed
    ]
    body = "\n".join(body_lines)

    # 'me' refers to the authenticated user (the sender)
    # Pass ADMIN_EMAIL as 'to' and COMMUNICATIONS_EMAIL as 'cc'
    message = create_message('me', ADMIN_EMAIL, COMMUNICATIONS_EMAIL, subject, body)

    if message:
        sent_message = send_message(service, 'me', message)
        return sent_message is not None
    else:
        print("Failed to create email message.")
        return False

# Example Usage (for testing purposes, comment out when importing)
# if __name__ == '__main__':
#     test_data = {
#         'sca_name': 'Test Subject',
#         'mundane_name': 'Test Mundane',
#         'sca_membership_number': 12345,
#         'westkingdom_email': 'test@westkingdom.org',
#         'contact_phone_number': '111-222-3333',
#         'street_address': '1 Test St',
#         'city': 'Testville',
#         'state': 'TS',
#         'zip_code': '12345',
#         'country': 'Testland',
#         'effective_date': '2025-04-11',
#         'end_date': '2026-04-11'
#     }
#     send_registration_email(test_data, "Test Group")
