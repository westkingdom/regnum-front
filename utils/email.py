import base64
import os.path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import streamlit as st # Import streamlit for error display if needed

# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
# Replace with the email address that should receive the primary notification
ADMIN_EMAIL = "webminister@westkingdom.org"
# Email address for the copy
COMMUNICATIONS_EMAIL = "communications@westkingdom.org"

# Define paths for credentials and token
SECRET_CREDS_PATH = '/secrets/credentials.json'
LOCAL_CREDS_PATH = 'credentials.json' # Local fallback
TOKEN_PATH = 'token.json' # Path for the generated token

def get_gmail_service():
    """Initializes the Gmail service using credentials, prioritizing mounted secrets."""
    creds = None
    # Determine the correct credentials path
    creds_path = SECRET_CREDS_PATH if os.path.exists(SECRET_CREDS_PATH) else LOCAL_CREDS_PATH

    # --- IMPORTANT: token.json Handling ---
    # The current flow using token.json and run_local_server WILL NOT WORK in Cloud Run.
    # This section needs to be replaced with a Service Account approach or a proper web OAuth flow
    # where the refresh token is stored securely after initial authorization.
    # For now, this code will likely fail in Cloud Run when trying to get/refresh the token.
    # Consider this placeholder logic that needs refactoring for production.

    if os.path.exists(TOKEN_PATH):
        try:
            # Attempt to load token, still requires SCOPES and client_secret from creds_path later if refresh needed
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        except Exception as e:
            print(f"Error loading {TOKEN_PATH}: {e}. Re-authenticating.")
            creds = None
            if os.path.exists(TOKEN_PATH):
                try:
                    os.remove(TOKEN_PATH)
                except OSError as rm_e:
                    print(f"Error removing corrupted token file: {rm_e}")


    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                 # Refresh requires client_id, client_secret from creds_path and scopes
                 # This might still fail if the original creds_path isn't accessible or valid
                 # Or if the refresh token itself is invalid/revoked.
                creds.refresh(Request()) # This implicitly needs client secrets associated with the token
            except Exception as e:
                print(f"Error refreshing token: {e}. Re-authenticating.")
                # If refresh fails, force re-authentication (problematic in Cloud Run)
                creds = None # Reset creds
                if os.path.exists(TOKEN_PATH): # Clean up potentially invalid token
                     try:
                         os.remove(TOKEN_PATH)
                     except OSError as rm_e:
                         print(f"Error removing token file after refresh failure: {rm_e}")

        # This 'else' block containing run_local_server is the main issue for Cloud Run
        else:
            print("Attempting interactive authentication flow (will fail in Cloud Run)...")
            try:
                if not os.path.exists(creds_path):
                    # Use st.error if running within Streamlit context, otherwise print
                    error_msg = f"Error: Credentials file not found at {creds_path}. Cannot initiate authentication."
                    try:
                        st.error(error_msg)
                    except Exception:
                        print(error_msg)
                    return None # Cannot proceed

                # THIS IS THE PART THAT WON'T WORK ON CLOUD RUN
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                creds = flow.run_local_server(port=0) # Requires user interaction

            except FileNotFoundError:
                 error_msg = f"Error: Credentials file not found at {creds_path} during flow setup."
                 try:
                     st.error(error_msg)
                 except Exception:
                     print(error_msg)
                 return None
            except Exception as e:
                 error_msg = f"Error during authentication flow: {e}"
                 try:
                     st.error(error_msg)
                 except Exception:
                     print(error_msg)
                 return None


        # Save the credentials (token) for the next run (problematic in Cloud Run's stateless env)
        if creds:
            try:
                # Writing token.json might not persist reliably across Cloud Run instances
                with open(TOKEN_PATH, 'w') as token:
                    token.write(creds.to_json())
                print(f"Token saved to {TOKEN_PATH}")
            except Exception as e:
                print(f"Error saving {TOKEN_PATH}: {e}")

    # Build the service if credentials exist
    if creds:
        try:
            service = build('gmail', 'v1', credentials=creds)
            print("Gmail service built successfully.")
            return service
        except HttpError as error:
            print(f'An error occurred building the Gmail service: {error}')
            return None
        except Exception as e:
            print(f'An unexpected error occurred building service: {e}')
            return None
    else:
        print("Failed to obtain valid credentials.")
        return None


# ... rest of create_message, send_message, send_registration_email functions remain the same ...

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
    """Send an email message."""
    try:
        message = (service.users().messages().send(userId=user_id, body=message)
                   .execute())
        print(f'Message Id: {message["id"]}')
        return message
    except HttpError as error:
        print(f'An error occurred sending the email: {error}')
        if error.resp.status == 400:
            print("Error details:", error.content)
        return None
    except Exception as e:
        print(f'An unexpected error occurred during sending: {e}')
        return None

def send_registration_email(form_data: dict, group_name: str):
    """Constructs and sends the registration email using form data to Admin and CCs Communications."""
    print("Attempting to send registration email...")
    service = get_gmail_service() # Call the updated function
    if not service:
        print("Failed to get Gmail service. Email not sent.")
        # Optionally display error in Streamlit if possible
        try:
            st.error("Failed to initialize email service. Notification not sent.")
        except Exception:
            pass # Ignore if not in Streamlit context
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

    message = create_message('me', ADMIN_EMAIL, COMMUNICATIONS_EMAIL, subject, body)

    if message:
        print(f"Sending email to {ADMIN_EMAIL}, CC {COMMUNICATIONS_EMAIL}...")
        sent_message = send_message(service, 'me', message)
        if sent_message:
            print("Email sent successfully.")
            return True
        else:
            print("Failed to send email via Gmail API.")
            # Optionally display error in Streamlit
            try:
                st.error("Failed to send notification email via Gmail API.")
            except Exception:
                pass
            return False
    else:
        print("Failed to create email message.")
        return False
