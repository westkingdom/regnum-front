#!/usr/bin/env python3
"""
Data Sanitization Utility for WKRegnum Forms

This module provides comprehensive data sanitization functions to protect against
various security threats including XSS, injection attacks, and data corruption.

Security Features:
- HTML/Script tag removal and encoding
- SQL injection prevention
- Email injection prevention
- Phone number formatting and validation
- Address and name sanitization
- Length limits and character restrictions
- Unicode normalization
"""

import re
import html
import unicodedata
from typing import Optional, Dict, Any, List
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Security patterns for detection and removal
DANGEROUS_PATTERNS = [
    # Script tags and JavaScript
    r'<script[^>]*>.*?</script>',
    r'javascript:',
    r'vbscript:',
    r'onload\s*=',
    r'onerror\s*=',
    r'onclick\s*=',
    r'onmouseover\s*=',
    
    # HTML tags that could be dangerous
    r'<iframe[^>]*>.*?</iframe>',
    r'<object[^>]*>.*?</object>',
    r'<embed[^>]*>.*?</embed>',
    r'<form[^>]*>.*?</form>',
    
    # SQL injection patterns
    r'union\s+select',
    r'drop\s+table',
    r'delete\s+from',
    r'insert\s+into',
    r'update\s+.*\s+set',
    r'exec\s*\(',
    r'sp_\w+',
    
    # Email header injection
    r'bcc\s*:',
    r'cc\s*:',
    r'to\s*:',
    r'from\s*:',
    r'subject\s*:',
    r'content-type\s*:',
    r'\r\n',
    r'\n\r',
]

# Compile patterns for better performance
COMPILED_PATTERNS = [re.compile(pattern, re.IGNORECASE | re.DOTALL) for pattern in DANGEROUS_PATTERNS]

# Character limits for different field types
FIELD_LIMITS = {
    'name': 100,
    'email': 254,  # RFC 5321 limit
    'phone': 20,
    'address': 200,
    'city': 100,
    'state': 50,
    'zip_code': 10,
    'text_area': 2000,
    'short_text': 500,
}

# Allowed characters for different field types
ALLOWED_PATTERNS = {
    'name': r'^[a-zA-Z0-9\s\.\-\'\"]+$',  # Names with common punctuation
    'address': r'^[a-zA-Z0-9\s\.\-\#\/\,\'\"]+$',  # Addresses with common punctuation
    'city': r'^[a-zA-Z\s\.\-\'\"]+$',  # Cities (no numbers typically)
    'state': r'^[a-zA-Z\s]+$',  # States (letters only)
    'zip_code': r'^[0-9\-\s]+$',  # Zip codes (numbers, hyphens, spaces)
    'phone': r'^[0-9\+\-\(\)\s\.]+$',  # Phone numbers
    'alphanumeric': r'^[a-zA-Z0-9\s]+$',  # Basic alphanumeric
}

def normalize_unicode(text: str) -> str:
    """
    Normalize Unicode characters to prevent encoding attacks.
    
    Args:
        text: Input text to normalize
        
    Returns:
        Normalized text string
    """
    if not isinstance(text, str):
        return str(text)
    
    # Normalize Unicode to NFC form
    normalized = unicodedata.normalize('NFC', text)
    
    # Remove or replace problematic Unicode characters
    # Remove zero-width characters that could be used for obfuscation
    zero_width_chars = [
        '\u200b',  # Zero width space
        '\u200c',  # Zero width non-joiner
        '\u200d',  # Zero width joiner
        '\ufeff',  # Zero width no-break space
    ]
    
    for char in zero_width_chars:
        normalized = normalized.replace(char, '')
    
    return normalized

def remove_dangerous_patterns(text: str) -> str:
    """
    Remove potentially dangerous patterns from text.
    
    Args:
        text: Input text to sanitize
        
    Returns:
        Text with dangerous patterns removed
    """
    if not isinstance(text, str):
        return str(text)
    
    sanitized = text
    
    # Remove dangerous patterns
    for pattern in COMPILED_PATTERNS:
        sanitized = pattern.sub('', sanitized)
    
    return sanitized

def html_encode(text: str) -> str:
    """
    HTML encode text to prevent XSS attacks.
    
    Args:
        text: Input text to encode
        
    Returns:
        HTML-encoded text
    """
    if not isinstance(text, str):
        return str(text)
    
    return html.escape(text, quote=True)

def sanitize_name(name: str, field_name: str = "Name") -> str:
    """
    Sanitize name fields (SCA name, mundane name, etc.).
    
    Args:
        name: Input name to sanitize
        field_name: Name of the field for error reporting
        
    Returns:
        Sanitized name
        
    Raises:
        ValueError: If name contains invalid characters or is too long
    """
    if not isinstance(name, str):
        name = str(name)
    
    original_name = name
    
    # Basic cleanup
    name = name.strip()
    name = normalize_unicode(name)
    
    # Check for dangerous patterns BEFORE removing them
    for pattern in COMPILED_PATTERNS:
        if pattern.search(original_name):
            logger.warning(f"Dangerous pattern detected in {field_name}: {repr(original_name)}")
            raise ValueError(f"{field_name} contains potentially dangerous content")
    
    # Remove any remaining dangerous patterns
    name = remove_dangerous_patterns(name)
    
    # Check length
    if len(name) > FIELD_LIMITS['name']:
        raise ValueError(f"{field_name} is too long (max {FIELD_LIMITS['name']} characters)")
    
    # Additional checks for suspicious patterns
    if len(name.strip()) == 0:
        raise ValueError(f"{field_name} cannot be empty")
    
    # Check for allowed characters
    if not re.match(ALLOWED_PATTERNS['name'], name):
        # Log the attempt for security monitoring
        logger.warning(f"Invalid characters in {field_name}: {repr(name)}")
        raise ValueError(f"{field_name} contains invalid characters")
    
    # Check for excessive repetition (potential spam/abuse)
    if len(set(name.replace(' ', ''))) < 2 and len(name) > 5:
        raise ValueError(f"{field_name} appears to contain excessive repetition")
    
    return html_encode(name)

def sanitize_email(email: str) -> str:
    """
    Sanitize and validate email addresses.
    
    Args:
        email: Input email to sanitize
        
    Returns:
        Sanitized email
        
    Raises:
        ValueError: If email is invalid or contains dangerous patterns
    """
    if not isinstance(email, str):
        email = str(email)
    
    # Basic cleanup
    email = email.strip().lower()
    email = normalize_unicode(email)
    
    # Check for email injection patterns
    dangerous_email_patterns = [
        r'\r\n',
        r'\n\r',
        r'bcc\s*:',
        r'cc\s*:',
        r'to\s*:',
        r'from\s*:',
        r'subject\s*:',
    ]
    
    for pattern in dangerous_email_patterns:
        if re.search(pattern, email, re.IGNORECASE):
            logger.warning(f"Email injection attempt detected: {repr(email)}")
            raise ValueError("Email contains invalid characters")
    
    # Check length
    if len(email) > FIELD_LIMITS['email']:
        raise ValueError(f"Email is too long (max {FIELD_LIMITS['email']} characters)")
    
    # Basic email format validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise ValueError("Invalid email format")
    
    return email

def sanitize_phone(phone: str) -> str:
    """
    Sanitize and format phone numbers.
    
    Args:
        phone: Input phone number to sanitize
        
    Returns:
        Sanitized phone number
        
    Raises:
        ValueError: If phone number is invalid
    """
    if not isinstance(phone, str):
        phone = str(phone)
    
    # Basic cleanup
    phone = phone.strip()
    phone = normalize_unicode(phone)
    phone = remove_dangerous_patterns(phone)
    
    # Check length
    if len(phone) > FIELD_LIMITS['phone']:
        raise ValueError(f"Phone number is too long (max {FIELD_LIMITS['phone']} characters)")
    
    # Check for allowed characters
    if phone and not re.match(ALLOWED_PATTERNS['phone'], phone):
        logger.warning(f"Invalid characters in phone number: {repr(phone)}")
        raise ValueError("Phone number contains invalid characters")
    
    return html_encode(phone)

def sanitize_address(address: str, field_name: str = "Address") -> str:
    """
    Sanitize address fields.
    
    Args:
        address: Input address to sanitize
        field_name: Name of the field for error reporting
        
    Returns:
        Sanitized address
        
    Raises:
        ValueError: If address contains invalid characters or is too long
    """
    if not isinstance(address, str):
        address = str(address)
    
    original_address = address
    
    # Basic cleanup
    address = address.strip()
    address = normalize_unicode(address)
    
    # Check for dangerous patterns BEFORE removing them
    for pattern in COMPILED_PATTERNS:
        if pattern.search(original_address):
            logger.warning(f"Dangerous pattern detected in {field_name}: {repr(original_address)}")
            raise ValueError(f"{field_name} contains potentially dangerous content")
    
    # Remove any remaining dangerous patterns
    address = remove_dangerous_patterns(address)
    
    # Check length
    if len(address) > FIELD_LIMITS['address']:
        raise ValueError(f"{field_name} is too long (max {FIELD_LIMITS['address']} characters)")
    
    # Check for allowed characters
    if address and not re.match(ALLOWED_PATTERNS['address'], address):
        logger.warning(f"Invalid characters in {field_name}: {repr(address)}")
        raise ValueError(f"{field_name} contains invalid characters")
    
    return html_encode(address)

def sanitize_city(city: str) -> str:
    """
    Sanitize city names.
    
    Args:
        city: Input city name to sanitize
        
    Returns:
        Sanitized city name
        
    Raises:
        ValueError: If city name is invalid
    """
    if not isinstance(city, str):
        city = str(city)
    
    # Basic cleanup
    city = city.strip()
    city = normalize_unicode(city)
    city = remove_dangerous_patterns(city)
    
    # Check length
    if len(city) > FIELD_LIMITS['city']:
        raise ValueError(f"City name is too long (max {FIELD_LIMITS['city']} characters)")
    
    # Check for allowed characters
    if city and not re.match(ALLOWED_PATTERNS['city'], city):
        logger.warning(f"Invalid characters in city name: {repr(city)}")
        raise ValueError("City name contains invalid characters")
    
    return html_encode(city)

def sanitize_state(state: str) -> str:
    """
    Sanitize state names/abbreviations.
    
    Args:
        state: Input state to sanitize
        
    Returns:
        Sanitized state (uppercase)
        
    Raises:
        ValueError: If state is invalid
    """
    if not isinstance(state, str):
        state = str(state)
    
    # Basic cleanup
    state = state.strip().upper()
    state = normalize_unicode(state)
    state = remove_dangerous_patterns(state)
    
    # Check length
    if len(state) > FIELD_LIMITS['state']:
        raise ValueError(f"State is too long (max {FIELD_LIMITS['state']} characters)")
    
    # Check for allowed characters
    if state and not re.match(ALLOWED_PATTERNS['state'], state):
        logger.warning(f"Invalid characters in state: {repr(state)}")
        raise ValueError("State contains invalid characters")
    
    return html_encode(state)

def sanitize_zip_code(zip_code: str) -> str:
    """
    Sanitize ZIP/postal codes.
    
    Args:
        zip_code: Input ZIP code to sanitize
        
    Returns:
        Sanitized ZIP code
        
    Raises:
        ValueError: If ZIP code is invalid
    """
    if not isinstance(zip_code, str):
        zip_code = str(zip_code)
    
    # Basic cleanup
    zip_code = zip_code.strip()
    zip_code = normalize_unicode(zip_code)
    zip_code = remove_dangerous_patterns(zip_code)
    
    # Check length
    if len(zip_code) > FIELD_LIMITS['zip_code']:
        raise ValueError(f"ZIP code is too long (max {FIELD_LIMITS['zip_code']} characters)")
    
    # Check for allowed characters
    if zip_code and not re.match(ALLOWED_PATTERNS['zip_code'], zip_code):
        logger.warning(f"Invalid characters in ZIP code: {repr(zip_code)}")
        raise ValueError("ZIP code contains invalid characters")
    
    return html_encode(zip_code)

def sanitize_text_area(text: str, field_name: str = "Text") -> str:
    """
    Sanitize large text areas (like job descriptions).
    
    Args:
        text: Input text to sanitize
        field_name: Name of the field for error reporting
        
    Returns:
        Sanitized text
        
    Raises:
        ValueError: If text is too long or contains dangerous content
    """
    if not isinstance(text, str):
        text = str(text)
    
    original_text = text
    
    # Basic cleanup
    text = text.strip()
    text = normalize_unicode(text)
    
    # Check for dangerous patterns BEFORE removing them
    for pattern in COMPILED_PATTERNS:
        if pattern.search(original_text):
            logger.warning(f"Dangerous pattern detected in {field_name}: {repr(original_text[:100])}")
            raise ValueError(f"{field_name} contains potentially dangerous content")
    
    # Remove any remaining dangerous patterns
    text = remove_dangerous_patterns(text)
    
    # Check length
    if len(text) > FIELD_LIMITS['text_area']:
        raise ValueError(f"{field_name} is too long (max {FIELD_LIMITS['text_area']} characters)")
    
    # Check for excessive repetition (potential spam)
    if len(text) > 50:
        # Count unique characters (excluding spaces)
        unique_chars = len(set(text.replace(' ', '').replace('\n', '')))
        if unique_chars < 5:
            logger.warning(f"Potential spam detected in {field_name}: low character diversity")
            raise ValueError(f"{field_name} appears to contain spam or excessive repetition")
    
    # Check for URL patterns (might be spam)
    url_pattern = r'https?://|www\.|\.com|\.org|\.net'
    url_matches = len(re.findall(url_pattern, text, re.IGNORECASE))
    if url_matches > 2:
        logger.warning(f"Multiple URLs detected in {field_name}")
        raise ValueError(f"{field_name} contains too many URLs")
    
    return html_encode(text)

def sanitize_short_text(text: str, field_name: str = "Text") -> str:
    """
    Sanitize shorter text fields.
    
    Args:
        text: Input text to sanitize
        field_name: Name of the field for error reporting
        
    Returns:
        Sanitized text
        
    Raises:
        ValueError: If text is invalid
    """
    if not isinstance(text, str):
        text = str(text)
    
    original_text = text
    
    # Basic cleanup
    text = text.strip()
    text = normalize_unicode(text)
    
    # Check for dangerous patterns BEFORE removing them
    for pattern in COMPILED_PATTERNS:
        if pattern.search(original_text):
            logger.warning(f"Dangerous pattern detected in {field_name}: {repr(original_text)}")
            raise ValueError(f"{field_name} contains potentially dangerous content")
    
    # Remove any remaining dangerous patterns
    text = remove_dangerous_patterns(text)
    
    # Check length
    if len(text) > FIELD_LIMITS['short_text']:
        raise ValueError(f"{field_name} is too long (max {FIELD_LIMITS['short_text']} characters)")
    
    return html_encode(text)

def sanitize_duty_request_form(form_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Sanitize all fields in a duty request form.
    
    Args:
        form_data: Dictionary containing form field values
        
    Returns:
        Dictionary with sanitized values
        
    Raises:
        ValueError: If any field fails validation
    """
    sanitized_data = {}
    errors = []
    
    try:
        # Required fields
        if 'sca_name' in form_data:
            sanitized_data['Society Name'] = sanitize_name(form_data['sca_name'], "Society Name")
        
        if 'mundane_name' in form_data:
            sanitized_data['Mundane Name'] = sanitize_name(form_data['mundane_name'], "Mundane Name")
        
        if 'wk_email' in form_data:
            sanitized_data['West Kingdom Google Email'] = sanitize_email(form_data['wk_email'])
        
        if 'address' in form_data:
            sanitized_data['Mundane Address'] = sanitize_address(form_data['address'], "Street Address")
        
        if 'city' in form_data:
            sanitized_data['Mundane City'] = sanitize_city(form_data['city'])
        
        if 'state' in form_data:
            sanitized_data['Mundane State'] = sanitize_state(form_data['state'])
        
        if 'zip_code' in form_data:
            sanitized_data['Mundane Zip Code'] = sanitize_zip_code(form_data['zip_code'])
        
        if 'principality' in form_data:
            sanitized_data['Principality'] = sanitize_short_text(form_data['principality'], "Principality")
        
        if 'requested_job' in form_data:
            sanitized_data['Requested Job'] = sanitize_text_area(form_data['requested_job'], "Requested Job")
        
        # Optional fields
        if 'contact_phone' in form_data and form_data['contact_phone']:
            sanitized_data['Contact Phone Number'] = sanitize_phone(form_data['contact_phone'])
        else:
            sanitized_data['Contact Phone Number'] = "N/A"
        
        if 'barony' in form_data and form_data['barony']:
            sanitized_data['Barony'] = sanitize_short_text(form_data['barony'], "Barony")
        else:
            sanitized_data['Barony'] = "N/A"
        
        if 'group' in form_data and form_data['group']:
            sanitized_data['Group'] = sanitize_short_text(form_data['group'], "Group")
        else:
            sanitized_data['Group'] = "N/A"
        
        if 'member_num' in form_data and form_data['member_num']:
            # Member number should be numeric
            member_num = str(form_data['member_num']).strip()
            if not member_num.isdigit():
                raise ValueError("SCA Member Number must be numeric")
            sanitized_data['SCA Member Number'] = html_encode(member_num)
        else:
            sanitized_data['SCA Member Number'] = "N/A"
        
    except ValueError as e:
        errors.append(str(e))
    except Exception as e:
        logger.error(f"Unexpected error during sanitization: {e}")
        errors.append("An error occurred while processing your data")
    
    if errors:
        raise ValueError("; ".join(errors))
    
    return sanitized_data

def log_sanitization_attempt(field_name: str, original_value: str, sanitized_value: str):
    """
    Log sanitization attempts for security monitoring.
    
    Args:
        field_name: Name of the field being sanitized
        original_value: Original input value
        sanitized_value: Sanitized output value
    """
    if original_value != sanitized_value:
        logger.info(f"Data sanitized in field '{field_name}': {len(original_value)} -> {len(sanitized_value)} chars")
        
        # Log if significant changes were made (potential security issue)
        if len(original_value) - len(sanitized_value) > 10:
            logger.warning(f"Significant sanitization in field '{field_name}': potential security threat detected")