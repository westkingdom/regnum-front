#!/usr/bin/env python3
"""
Password Hashing Utility for WKRegnum JWT Authentication

This utility provides secure password hashing using bcrypt for the WKRegnum application.
It can be used to generate password hashes for user accounts in the authentication system.

Usage:
    python utils/password_hasher.py hash <password>
    python utils/password_hasher.py verify <password> <hash>
    python utils/password_hasher.py interactive
"""

import bcrypt
import sys
import getpass
import argparse

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with a random salt.
    
    Args:
        password: The plain text password to hash
        
    Returns:
        The bcrypt hash as a string
    """
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against its bcrypt hash.
    
    Args:
        password: The plain text password to verify
        hashed: The bcrypt hash to verify against
        
    Returns:
        True if the password matches the hash, False otherwise
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception as e:
        print(f"Error verifying password: {e}")
        return False

def interactive_mode():
    """Interactive mode for password hashing"""
    print("=== WKRegnum Password Hasher - Interactive Mode ===")
    print()
    
    while True:
        print("Options:")
        print("1. Hash a new password")
        print("2. Verify a password against a hash")
        print("3. Exit")
        print()
        
        choice = input("Select an option (1-3): ").strip()
        
        if choice == '1':
            print("\n--- Hash Password ---")
            password = getpass.getpass("Enter password to hash: ")
            if not password:
                print("❌ Password cannot be empty")
                continue
                
            confirm_password = getpass.getpass("Confirm password: ")
            if password != confirm_password:
                print("❌ Passwords do not match")
                continue
                
            hashed = hash_password(password)
            print(f"✅ Password hashed successfully!")
            print(f"Hash: {hashed}")
            print()
            print("You can use this hash in your USERS_DB configuration:")
            print(f"'password_hash': '{hashed}'")
            print()
            
        elif choice == '2':
            print("\n--- Verify Password ---")
            password = getpass.getpass("Enter password to verify: ")
            hash_input = input("Enter hash to verify against: ").strip()
            
            if verify_password(password, hash_input):
                print("✅ Password verification successful!")
            else:
                print("❌ Password verification failed!")
            print()
            
        elif choice == '3':
            print("Goodbye!")
            break
            
        else:
            print("❌ Invalid option. Please select 1, 2, or 3.")
            print()

def main():
    """Main function for command line interface"""
    parser = argparse.ArgumentParser(
        description="Password hashing utility for WKRegnum JWT authentication",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python utils/password_hasher.py hash mypassword123
  python utils/password_hasher.py verify mypassword123 '$2b$12$...'
  python utils/password_hasher.py interactive
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Hash command
    hash_parser = subparsers.add_parser('hash', help='Hash a password')
    hash_parser.add_argument('password', help='Password to hash')
    
    # Verify command
    verify_parser = subparsers.add_parser('verify', help='Verify a password against a hash')
    verify_parser.add_argument('password', help='Password to verify')
    verify_parser.add_argument('hash', help='Hash to verify against')
    
    # Interactive command
    interactive_parser = subparsers.add_parser('interactive', help='Interactive mode')
    
    args = parser.parse_args()
    
    if args.command == 'hash':
        hashed = hash_password(args.password)
        print("Password hashed successfully!")
        print(f"Hash: {hashed}")
        print()
        print("Add this to your USERS_DB:")
        print(f"'password_hash': '{hashed}'")
        
    elif args.command == 'verify':
        if verify_password(args.password, args.hash):
            print("✅ Password verification successful!")
            sys.exit(0)
        else:
            print("❌ Password verification failed!")
            sys.exit(1)
            
    elif args.command == 'interactive':
        interactive_mode()
        
    else:
        parser.print_help()

if __name__ == '__main__':
    main()