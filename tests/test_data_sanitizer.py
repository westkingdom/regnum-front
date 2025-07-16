#!/usr/bin/env python3
"""
Data Sanitization Test Suite for WKRegnum

This test suite verifies that the data sanitization functions properly protect
against various security threats and handle edge cases correctly.

Usage:
    python test_data_sanitizer.py
    python test_data_sanitizer.py --verbose
"""

import sys
import os
import unittest
from unittest.mock import patch
import logging

# Add the project root to the path so we can import utils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.data_sanitizer import (
    sanitize_name, sanitize_email, sanitize_phone, sanitize_address,
    sanitize_city, sanitize_state, sanitize_zip_code, sanitize_text_area,
    sanitize_short_text, sanitize_duty_request_form, normalize_unicode,
    remove_dangerous_patterns, html_encode
)

class TestDataSanitizer(unittest.TestCase):
    """Test cases for data sanitization functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Suppress logging during tests unless verbose
        if '--verbose' not in sys.argv:
            logging.disable(logging.CRITICAL)
    
    def tearDown(self):
        """Clean up after tests"""
        logging.disable(logging.NOTSET)

    # Test basic sanitization functions
    def test_normalize_unicode(self):
        """Test Unicode normalization"""
        # Test normal text
        self.assertEqual(normalize_unicode("Hello World"), "Hello World")
        
        # Test zero-width characters removal
        text_with_zwc = "Hello\u200bWorld\u200c"
        self.assertEqual(normalize_unicode(text_with_zwc), "HelloWorld")
        
        # Test non-string input
        self.assertEqual(normalize_unicode(123), "123")

    def test_html_encode(self):
        """Test HTML encoding"""
        # Test basic HTML encoding
        self.assertEqual(html_encode("<script>alert('xss')</script>"), 
                        "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;")
        
        # Test quotes encoding
        self.assertEqual(html_encode('Hello "World"'), "Hello &quot;World&quot;")
        
        # Test ampersand encoding
        self.assertEqual(html_encode("Tom & Jerry"), "Tom &amp; Jerry")

    def test_remove_dangerous_patterns(self):
        """Test dangerous pattern removal"""
        # Test script tag removal
        dangerous_text = "<script>alert('xss')</script>Hello World"
        safe_text = remove_dangerous_patterns(dangerous_text)
        self.assertNotIn("<script>", safe_text)
        self.assertIn("Hello World", safe_text)
        
        # Test SQL injection patterns
        sql_injection = "'; DROP TABLE users; --"
        safe_sql = remove_dangerous_patterns(sql_injection)
        self.assertNotIn("DROP TABLE", safe_sql.upper())

    # Test name sanitization
    def test_sanitize_name_valid(self):
        """Test valid name sanitization"""
        # Test normal names
        self.assertEqual(sanitize_name("John Doe"), "John Doe")
        self.assertEqual(sanitize_name("Mary O'Connor"), "Mary O&#x27;Connor")
        self.assertEqual(sanitize_name("Jean-Pierre"), "Jean-Pierre")
        
        # Test with numbers (medieval names might have numbers)
        self.assertEqual(sanitize_name("Henry VIII"), "Henry VIII")

    def test_sanitize_name_invalid(self):
        """Test invalid name handling"""
        # Test empty name
        with self.assertRaises(ValueError):
            sanitize_name("")
        
        # Test too long name
        long_name = "A" * 101
        with self.assertRaises(ValueError):
            sanitize_name(long_name)
        
        # Test invalid characters
        with self.assertRaises(ValueError):
            sanitize_name("John<script>alert('xss')</script>")
        
        # Test excessive repetition
        with self.assertRaises(ValueError):
            sanitize_name("AAAAAAAAAA")

    # Test email sanitization
    def test_sanitize_email_valid(self):
        """Test valid email sanitization"""
        # Test normal email
        self.assertEqual(sanitize_email("user@westkingdom.org"), "user@westkingdom.org")
        
        # Test case normalization
        self.assertEqual(sanitize_email("USER@WESTKINGDOM.ORG"), "user@westkingdom.org")
        
        # Test with numbers and special chars
        self.assertEqual(sanitize_email("user.123+test@westkingdom.org"), "user.123+test@westkingdom.org")

    def test_sanitize_email_invalid(self):
        """Test invalid email handling"""
        # Test email injection
        with self.assertRaises(ValueError):
            sanitize_email("user@example.com\r\nBCC: hacker@evil.com")
        
        # Test invalid format
        with self.assertRaises(ValueError):
            sanitize_email("not-an-email")
        
        # Test too long email
        long_email = "a" * 250 + "@example.com"
        with self.assertRaises(ValueError):
            sanitize_email(long_email)

    # Test phone sanitization
    def test_sanitize_phone_valid(self):
        """Test valid phone sanitization"""
        # Test various phone formats
        self.assertEqual(sanitize_phone("(555) 123-4567"), "(555) 123-4567")
        self.assertEqual(sanitize_phone("555-123-4567"), "555-123-4567")
        self.assertEqual(sanitize_phone("+1 555 123 4567"), "+1 555 123 4567")
        
        # Test empty phone (optional field)
        self.assertEqual(sanitize_phone(""), "")

    def test_sanitize_phone_invalid(self):
        """Test invalid phone handling"""
        # Test invalid characters
        with self.assertRaises(ValueError):
            sanitize_phone("555-123-ABCD")
        
        # Test too long phone
        with self.assertRaises(ValueError):
            sanitize_phone("1" * 25)

    # Test address sanitization
    def test_sanitize_address_valid(self):
        """Test valid address sanitization"""
        # Test normal address
        self.assertEqual(sanitize_address("123 Main St"), "123 Main St")
        
        # Test address with apartment
        self.assertEqual(sanitize_address("123 Main St, Apt #4"), "123 Main St, Apt #4")

    def test_sanitize_address_invalid(self):
        """Test invalid address handling"""
        # Test too long address
        long_address = "A" * 201
        with self.assertRaises(ValueError):
            sanitize_address(long_address)
        
        # Test dangerous characters
        with self.assertRaises(ValueError):
            sanitize_address("123 Main St<script>alert('xss')</script>")

    # Test city sanitization
    def test_sanitize_city_valid(self):
        """Test valid city sanitization"""
        # Test normal cities
        self.assertEqual(sanitize_city("San Francisco"), "San Francisco")
        self.assertEqual(sanitize_city("St. Louis"), "St. Louis")
        self.assertEqual(sanitize_city("O'Fallon"), "O&#x27;Fallon")

    def test_sanitize_city_invalid(self):
        """Test invalid city handling"""
        # Test city with numbers (unusual but might be valid)
        with self.assertRaises(ValueError):
            sanitize_city("City123")
        
        # Test too long city
        with self.assertRaises(ValueError):
            sanitize_city("A" * 101)

    # Test state sanitization
    def test_sanitize_state_valid(self):
        """Test valid state sanitization"""
        # Test state abbreviations
        self.assertEqual(sanitize_state("CA"), "CA")
        self.assertEqual(sanitize_state("ca"), "CA")
        
        # Test full state names
        self.assertEqual(sanitize_state("California"), "CALIFORNIA")

    def test_sanitize_state_invalid(self):
        """Test invalid state handling"""
        # Test numbers in state
        with self.assertRaises(ValueError):
            sanitize_state("CA123")
        
        # Test too long state
        with self.assertRaises(ValueError):
            sanitize_state("A" * 51)

    # Test ZIP code sanitization
    def test_sanitize_zip_code_valid(self):
        """Test valid ZIP code sanitization"""
        # Test various ZIP formats
        self.assertEqual(sanitize_zip_code("12345"), "12345")
        self.assertEqual(sanitize_zip_code("12345-6789"), "12345-6789")
        self.assertEqual(sanitize_zip_code("12345 6789"), "12345 6789")

    def test_sanitize_zip_code_invalid(self):
        """Test invalid ZIP code handling"""
        # Test letters in ZIP
        with self.assertRaises(ValueError):
            sanitize_zip_code("1234A")
        
        # Test too long ZIP
        with self.assertRaises(ValueError):
            sanitize_zip_code("1" * 11)

    # Test text area sanitization
    def test_sanitize_text_area_valid(self):
        """Test valid text area sanitization"""
        # Test normal text
        normal_text = "I would like to serve as the Kingdom Seneschal."
        self.assertEqual(sanitize_text_area(normal_text), normal_text)
        
        # Test text with line breaks
        text_with_breaks = "Line 1\nLine 2\nLine 3"
        result = sanitize_text_area(text_with_breaks)
        self.assertIn("Line 1", result)

    def test_sanitize_text_area_invalid(self):
        """Test invalid text area handling"""
        # Test too long text
        long_text = "A" * 2001
        with self.assertRaises(ValueError):
            sanitize_text_area(long_text)
        
        # Test spam-like content (low character diversity)
        spam_text = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        with self.assertRaises(ValueError):
            sanitize_text_area(spam_text)
        
        # Test too many URLs
        url_spam = "Visit http://spam1.com and http://spam2.com and http://spam3.com"
        with self.assertRaises(ValueError):
            sanitize_text_area(url_spam)

    # Test complete form sanitization
    def test_sanitize_duty_request_form_valid(self):
        """Test valid complete form sanitization"""
        valid_form_data = {
            'sca_name': 'Lord John of Somewhere',
            'mundane_name': 'John Smith',
            'wk_email': 'john@westkingdom.org',
            'contact_phone': '(555) 123-4567',
            'address': '123 Main Street',
            'city': 'San Francisco',
            'state': 'CA',
            'zip_code': '94102',
            'principality': 'Principality of the Mists',
            'barony': 'Barony of the Mists',
            'group': 'Shire of Test',
            'requested_job': 'I would like to serve as the local seneschal.',
            'member_num': '12345'
        }
        
        result = sanitize_duty_request_form(valid_form_data)
        
        # Check that all fields are present and sanitized
        self.assertIn('Society Name', result)
        self.assertIn('Mundane Name', result)
        self.assertIn('West Kingdom Google Email', result)
        self.assertEqual(result['West Kingdom Google Email'], 'john@westkingdom.org')
        self.assertEqual(result['Mundane State'], 'CA')

    def test_sanitize_duty_request_form_invalid(self):
        """Test invalid complete form sanitization"""
        # Test with dangerous content
        dangerous_form_data = {
            'sca_name': '<script>alert("xss")</script>',
            'mundane_name': 'John Smith',
            'wk_email': 'john@westkingdom.org',
            'address': '123 Main Street',
            'city': 'San Francisco',
            'state': 'CA',
            'zip_code': '94102',
            'principality': 'Test',
            'requested_job': 'Test job',
            'member_num': '12345'
        }
        
        with self.assertRaises(ValueError):
            sanitize_duty_request_form(dangerous_form_data)

    def test_sanitize_duty_request_form_optional_fields(self):
        """Test form sanitization with optional fields empty"""
        minimal_form_data = {
            'sca_name': 'Lord John',
            'mundane_name': 'John Smith',
            'wk_email': 'john@westkingdom.org',
            'contact_phone': '',  # Optional
            'address': '123 Main Street',
            'city': 'San Francisco',
            'state': 'CA',
            'zip_code': '94102',
            'principality': 'Test Principality',
            'barony': '',  # Optional
            'group': '',   # Optional
            'requested_job': 'Test job description',
            'member_num': '12345'
        }
        
        result = sanitize_duty_request_form(minimal_form_data)
        
        # Check that optional fields are set to "N/A"
        self.assertEqual(result['Contact Phone Number'], 'N/A')
        self.assertEqual(result['Barony'], 'N/A')
        self.assertEqual(result['Group'], 'N/A')

class TestSecurityScenarios(unittest.TestCase):
    """Test specific security attack scenarios"""
    
    def test_xss_attacks(self):
        """Test XSS attack prevention"""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "<iframe src='javascript:alert(\"xss\")'></iframe>",
            "';alert('xss');//",
        ]
        
        for payload in xss_payloads:
            with self.assertRaises(ValueError):
                sanitize_name(payload)

    def test_sql_injection_attacks(self):
        """Test SQL injection prevention"""
        sql_payloads = [
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM passwords --",
            "admin'; DELETE FROM users WHERE 1=1; --",
            "' OR '1'='1",
        ]
        
        for payload in sql_payloads:
            # These should be cleaned by dangerous pattern removal
            cleaned = remove_dangerous_patterns(payload)
            self.assertNotIn("DROP TABLE", cleaned.upper())
            self.assertNotIn("UNION SELECT", cleaned.upper())

    def test_email_injection_attacks(self):
        """Test email header injection prevention"""
        email_injection_payloads = [
            "user@example.com\r\nBCC: hacker@evil.com",
            "user@example.com\nCC: spam@evil.com",
            "user@example.com\r\nSubject: Spam",
            "user@example.com\nTo: victim@target.com",
        ]
        
        for payload in email_injection_payloads:
            with self.assertRaises(ValueError):
                sanitize_email(payload)

    def test_unicode_attacks(self):
        """Test Unicode-based attacks"""
        unicode_payloads = [
            "Hello\u200bWorld",  # Zero-width space
            "Test\ufeffText",    # Zero-width no-break space
            "Normal\u200cText",  # Zero-width non-joiner
        ]
        
        for payload in unicode_payloads:
            normalized = normalize_unicode(payload)
            # Zero-width characters should be removed
            self.assertNotIn('\u200b', normalized)
            self.assertNotIn('\ufeff', normalized)
            self.assertNotIn('\u200c', normalized)

def run_security_tests():
    """Run comprehensive security tests"""
    print("🔒 Running WKRegnum Data Sanitization Security Tests")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestDataSanitizer))
    suite.addTests(loader.loadTestsFromTestCase(TestSecurityScenarios))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2 if '--verbose' in sys.argv else 1)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✅ All security tests passed!")
        print(f"📊 Tests run: {result.testsRun}")
        return True
    else:
        print("❌ Some security tests failed!")
        print(f"📊 Tests run: {result.testsRun}")
        print(f"❌ Failures: {len(result.failures)}")
        print(f"❌ Errors: {len(result.errors)}")
        return False

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="WKRegnum Data Sanitization Test Suite")
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    args = parser.parse_args()
    
    success = run_security_tests()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()