#!/usr/bin/env python3
"""
A utility script to test authentication and group membership functionality.
This script helps diagnose issues with Google Group membership detection.
"""

import os
import sys
import argparse
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from utils.config import REGNUM_ADMIN_GROUP
from utils.auth import get_directory_service, is_group_member

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("auth-test")

def test_service_account():
    """Test if the service account is working and has the correct permissions"""
    logger.info("Testing service account authentication...")
    
    # Path to service account key file
    SERVICE_ACCOUNT_FILE = '/secrets/sa/service_account.json'  # Cloud Run path
    LOCAL_SERVICE_ACCOUNT_FILE = 'regnum-service-account-key.json'  # Local development path
    
    # Check file existence
    sa_file = SERVICE_ACCOUNT_FILE if os.path.exists(SERVICE_ACCOUNT_FILE) else LOCAL_SERVICE_ACCOUNT_FILE
    if not os.path.exists(sa_file):
        logger.error(f"Service account file not found at {sa_file}")
        logger.error("Please make sure the service account key file exists at one of the expected paths.")
        return False
    
    # Test loading service account
    try:
        logger.info(f"Loading service account from: {sa_file}")
        scopes = [
            'https://www.googleapis.com/auth/admin.directory.group.readonly',
            'https://www.googleapis.com/auth/admin.directory.group.member.readonly',
            'https://www.googleapis.com/auth/admin.directory.user.readonly'
        ]
        
        # Set impersonation user
        impersonate_user = os.environ.get("IMPERSONATED_USER_EMAIL", "webminister@westkingdom.org")
        logger.info(f"Impersonating user: {impersonate_user}")
        
        sa_credentials = service_account.Credentials.from_service_account_file(
            sa_file, 
            scopes=scopes,
            subject=impersonate_user
        )
        logger.info("Service account credentials loaded successfully")
        
        # Test building directory service
        service = build('admin', 'directory_v1', credentials=sa_credentials)
        logger.info("Directory service built successfully")
        
        # Test API access
        logger.info("Testing API access...")
        try:
            response = service.groups().list(domain="westkingdom.org", maxResults=5).execute()
            if 'groups' in response:
                logger.info(f"API access successful! Found {len(response['groups'])} groups")
                for group in response['groups']:
                    logger.info(f"  - {group['name']} ({group['email']})")
                return True
            else:
                logger.warning("API returned empty response")
                return False
        except HttpError as e:
            logger.error(f"API access failed: {e}")
            if e.status_code == 403:
                logger.error("Permission denied: The service account doesn't have sufficient permissions")
                logger.error("Make sure the service account has domain-wide delegation enabled and the correct OAuth scopes")
            return False
    except Exception as e:
        logger.error(f"Service account test failed: {e}")
        return False

def test_group_membership(email):
    """Test if a user is a member of the regnum-site group"""
    logger.info(f"Testing group membership for: {email}")
    
    # Get the directory service
    service = get_directory_service()
    if not service:
        logger.error("Failed to get directory service")
        return
    
    # Get the group ID
    group_id = REGNUM_ADMIN_GROUP
    logger.info(f"Testing membership in group ID: {group_id}")
    
    # Check direct membership first
    try:
        logger.info("Checking direct membership...")
        try:
            member = service.members().get(groupKey=group_id, memberKey=email).execute()
            logger.info(f"SUCCESS: {email} is a direct member of the group")
            return True
        except HttpError as e:
            if e.status_code == 404:
                logger.info(f"{email} is not a direct member of the group")
            else:
                logger.error(f"Error checking direct membership: {e}")
        
        # Check full membership (including nested groups)
        logger.info("Checking nested group membership...")
        try:
            request = service.members().list(groupKey=group_id, includeDerivedMembership=True)
            response = request.execute()
            members = response.get('members', [])
            
            # Log all members for debugging
            logger.info(f"Group has {len(members)} members total (including nested groups)")
            for i, member in enumerate(members):
                logger.info(f"  {i+1}. {member.get('email', 'N/A')} - {member.get('role', 'N/A')} - {member.get('type', 'N/A')}")
            
            # Check if user is in the list
            found = False
            for member in members:
                if member.get('email', '').lower() == email.lower():
                    logger.info(f"SUCCESS: {email} found in the group members list")
                    found = True
                    break
            
            if not found:
                logger.warning(f"{email} is NOT a member of the group (not found in members list)")
            
            return found
        except HttpError as e:
            logger.error(f"Error checking group membership: {e}")
            return False
    except Exception as e:
        logger.error(f"Unexpected error in membership test: {e}")
        return False

def test_bypass_mode(email):
    """Test the BYPASS_GROUP_CHECK functionality"""
    logger.info("Testing BYPASS_GROUP_CHECK functionality...")
    
    # First test with bypass disabled
    os.environ['BYPASS_GROUP_CHECK'] = 'false'
    logger.info("BYPASS_GROUP_CHECK=false")
    result1 = is_group_member(email, REGNUM_ADMIN_GROUP)
    logger.info(f"Group membership check with bypass disabled: {result1}")
    
    # Then test with bypass enabled
    os.environ['BYPASS_GROUP_CHECK'] = 'true'
    logger.info("BYPASS_GROUP_CHECK=true")
    result2 = is_group_member(email, REGNUM_ADMIN_GROUP)
    logger.info(f"Group membership check with bypass enabled: {result2}")
    
    return result1, result2

def main():
    parser = argparse.ArgumentParser(description="Test Google Groups authentication and membership")
    parser.add_argument("email", help="Email address to check for group membership")
    parser.add_argument("--bypass", action="store_true", help="Test the BYPASS_GROUP_CHECK functionality")
    parser.add_argument("--service-account", action="store_true", help="Only test service account access")
    
    args = parser.parse_args()
    
    logger.info("=== Google Groups Authentication Test ===")
    
    # Service account test
    if args.service_account:
        test_service_account()
        return
    
    # Full test sequence
    service_account_ok = test_service_account()
    if not service_account_ok:
        logger.error("Service account test failed. Fix this issue before continuing.")
        return
    
    # Group membership test
    membership_result = test_group_membership(args.email)
    logger.info(f"Group membership test result: {membership_result}")
    
    # Bypass test if requested
    if args.bypass:
        bypass_off, bypass_on = test_bypass_mode(args.email)
        logger.info(f"Bypass test results: Without bypass: {bypass_off}, With bypass: {bypass_on}")
    
    logger.info("=== Test Completed ===")

if __name__ == "__main__":
    main() 