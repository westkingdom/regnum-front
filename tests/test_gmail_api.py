#!/usr/bin/env python3
"""
Gmail API Test Utility for WKRegnum

This utility tests the Gmail API integration to ensure email functionality works correctly.
It can be used to verify service account setup and email sending capabilities.

Usage:
    python test_gmail_api.py test-service
    python test_gmail_api.py test-email recipient@example.com
    python test_gmail_api.py test-duty-request
"""

import sys
import os
import argparse
from datetime import datetime

# Add the project root to the path so we can import utils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.email import get_gmail_service, send_duty_request_email, send_registration_email
from utils.logger import setup_logger

# Set up logging
logger = setup_logger('gmail_test')

def test_service_account():
    """Test service account authentication and Gmail service initialization"""
    print("🔍 Testing Gmail API Service Account Authentication...")
    print()
    
    # Check for service account key file
    secret_path = '/secrets/sa/service_account.json'
    local_path = 'regnum-service-account-key.json'
    
    if os.path.exists(secret_path):
        print(f"✅ Service account key found at: {secret_path}")
    elif os.path.exists(local_path):
        print(f"✅ Service account key found at: {local_path}")
    else:
        print(f"❌ Service account key not found at either:")
        print(f"   - {secret_path}")
        print(f"   - {local_path}")
        return False
    
    # Test Gmail service initialization
    try:
        service = get_gmail_service()
        if service:
            print("✅ Gmail API service initialized successfully")
            
            # Test basic API access
            try:
                # Try to get user profile (basic API test)
                profile = service.users().getProfile(userId='me').execute()
                print(f"✅ Gmail API access verified for: {profile.get('emailAddress', 'Unknown')}")
                return True
            except Exception as e:
                print(f"❌ Gmail API access test failed: {e}")
                return False
        else:
            print("❌ Failed to initialize Gmail API service")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Gmail service: {e}")
        return False

def test_duty_request_email(recipient_email=None):
    """Test duty request email functionality"""
    print("📧 Testing Duty Request Email Functionality...")
    print()
    
    # Use default recipient if none provided
    if not recipient_email:
        recipient_email = "test@westkingdom.org"
    
    # Create test form data
    test_form_data = {
        "Society Name": "Test User",
        "Mundane Name": "John Doe",
        "West Kingdom Google Email": recipient_email,
        "Contact Phone Number": "555-123-4567",
        "Mundane Address": "123 Test Street",
        "Mundane City": "Test City",
        "Mundane State": "CA",
        "Mundane Zip Code": "12345",
        "Principality": "Test Principality",
        "Barony": "Test Barony",
        "Group": "Test Group",
        "Requested Job": "Test duty request for Gmail API verification"
    }
    
    print(f"📤 Sending test duty request email to: {recipient_email}")
    print("📋 Test form data:")
    for key, value in test_form_data.items():
        print(f"   {key}: {value}")
    print()
    
    try:
        success = send_duty_request_email(test_form_data, recipient_email)
        if success:
            print("✅ Duty request email sent successfully!")
            print("📧 Check the following inboxes for the test email:")
            print(f"   - {recipient_email}")
            print("   - communications@westkingdom.org")
            print("   - regnum-site@westkingdom.org")
            return True
        else:
            print("❌ Failed to send duty request email")
            return False
            
    except Exception as e:
        print(f"❌ Error sending duty request email: {e}")
        return False

def test_registration_email():
    """Test registration email functionality"""
    print("📧 Testing Registration Email Functionality...")
    print()
    
    # Create test registration data
    test_form_data = {
        'sca_name': 'Test SCA Name',
        'mundane_name': 'Test Mundane Name',
        'sca_membership_number': '12345',
        'westkingdom_email': 'test@westkingdom.org',
        'contact_phone_number': '555-123-4567',
        'street_address': '123 Test Street',
        'city': 'Test City',
        'state': 'CA',
        'zip_code': '12345',
        'country': 'USA',
        'effective_date': str(datetime.now().date()),
        'end_date': 'N/A'
    }
    
    test_group_name = "Test Group"
    
    print(f"📤 Sending test registration email for group: {test_group_name}")
    print("📋 Test registration data:")
    for key, value in test_form_data.items():
        print(f"   {key}: {value}")
    print()
    
    try:
        success = send_registration_email(test_form_data, test_group_name)
        if success:
            print("✅ Registration email sent successfully!")
            print("📧 Check the following inboxes for the test email:")
            print("   - webminister@westkingdom.org")
            print("   - communications@westkingdom.org")
            return True
        else:
            print("❌ Failed to send registration email")
            return False
            
    except Exception as e:
        print(f"❌ Error sending registration email: {e}")
        return False

def main():
    """Main function for command line interface"""
    parser = argparse.ArgumentParser(
        description="Gmail API test utility for WKRegnum",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_gmail_api.py test-service
  python test_gmail_api.py test-email test@westkingdom.org
  python test_gmail_api.py test-duty-request
  python test_gmail_api.py test-registration
        """
    )
    
    parser.add_argument('command', choices=['test-service', 'test-email', 'test-duty-request', 'test-registration'],
                       help='Test command to run')
    parser.add_argument('recipient', nargs='?', help='Email recipient for test-email command')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🔧 WKRegnum Gmail API Test Utility")
    print("=" * 60)
    print()
    
    success = False
    
    if args.command == 'test-service':
        success = test_service_account()
        
    elif args.command == 'test-email' or args.command == 'test-duty-request':
        # First test service account
        if test_service_account():
            print()
            success = test_duty_request_email(args.recipient)
        else:
            print("❌ Service account test failed, skipping email test")
            
    elif args.command == 'test-registration':
        # First test service account
        if test_service_account():
            print()
            success = test_registration_email()
        else:
            print("❌ Service account test failed, skipping registration test")
    
    print()
    print("=" * 60)
    if success:
        print("✅ Test completed successfully!")
        sys.exit(0)
    else:
        print("❌ Test failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()