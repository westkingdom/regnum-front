# Data Sanitization System for WKRegnum

This document describes the comprehensive data sanitization system implemented for the WKRegnum Duty Request form and other user input areas.

## Overview

The data sanitization system provides multi-layered protection against various security threats including:

- **XSS (Cross-Site Scripting) attacks**
- **SQL injection attempts**
- **Email header injection**
- **Unicode-based attacks**
- **Spam and abuse prevention**
- **Data corruption protection**

## Security Architecture

### Multi-Layer Defense

```
User Input
    ↓
1. Unicode Normalization
    ↓
2. Dangerous Pattern Detection
    ↓
3. Character Validation
    ↓
4. Length Limits
    ↓
5. HTML Encoding
    ↓
Sanitized Output
```

### Security Features

1. **Pattern Detection**: Identifies dangerous content before processing
2. **Strict Validation**: Rejects input with security threats
3. **HTML Encoding**: Prevents XSS attacks
4. **Length Limits**: Prevents buffer overflow and DoS attacks
5. **Character Restrictions**: Allows only safe characters per field type
6. **Logging**: Comprehensive security event logging

## Implementation

### Core Functions

#### `sanitize_duty_request_form(form_data)`
Main function that sanitizes all fields in the duty request form.

**Input**: Dictionary with raw form data
**Output**: Dictionary with sanitized data
**Raises**: `ValueError` if any field fails validation

#### Field-Specific Sanitizers

- `sanitize_name()`: Names (SCA, mundane)
- `sanitize_email()`: Email addresses
- `sanitize_phone()`: Phone numbers
- `sanitize_address()`: Street addresses
- `sanitize_city()`: City names
- `sanitize_state()`: State names/abbreviations
- `sanitize_zip_code()`: ZIP/postal codes
- `sanitize_text_area()`: Large text fields
- `sanitize_short_text()`: Short text fields

### Security Patterns Detected

#### Dangerous HTML/JavaScript
```
<script>alert('xss')</script>
javascript:alert('xss')
<iframe src='javascript:alert("xss")'></iframe>
<img src=x onerror=alert('xss')>
onload=, onclick=, onerror= (event handlers)
```

#### SQL Injection Patterns
```
'; DROP TABLE users; --
' UNION SELECT * FROM passwords --
admin'; DELETE FROM users WHERE 1=1; --
' OR '1'='1
```

#### Email Header Injection
```
user@example.com\r\nBCC: hacker@evil.com
user@example.com\nCC: spam@evil.com
user@example.com\r\nSubject: Spam
```

#### Unicode Attacks
```
Zero-width characters: \u200b, \u200c, \u200d, \ufeff
Unicode normalization attacks
Encoding obfuscation attempts
```

## Field Validation Rules

### Names (SCA Name, Mundane Name)
- **Max Length**: 100 characters
- **Allowed Characters**: Letters, numbers, spaces, periods, hyphens, apostrophes, quotes
- **Security Checks**: XSS prevention, excessive repetition detection
- **Example Valid**: `"Lord John of Somewhere"`, `"Mary O'Connor"`
- **Example Invalid**: `"<script>alert('xss')</script>"`, `"AAAAAAAAAA"`

### Email Addresses
- **Max Length**: 254 characters (RFC 5321 limit)
- **Format**: Standard email format validation
- **Security Checks**: Email header injection prevention
- **Case**: Normalized to lowercase
- **Example Valid**: `"user@westkingdom.org"`
- **Example Invalid**: `"user@example.com\r\nBCC: hacker@evil.com"`

### Phone Numbers
- **Max Length**: 20 characters
- **Allowed Characters**: Numbers, +, -, (, ), spaces, periods
- **Optional**: Can be empty
- **Example Valid**: `"(555) 123-4567"`, `"+1 555 123 4567"`
- **Example Invalid**: `"555-123-ABCD"`

### Addresses
- **Max Length**: 200 characters
- **Allowed Characters**: Letters, numbers, spaces, periods, hyphens, #, /, commas, quotes
- **Security Checks**: XSS prevention
- **Example Valid**: `"123 Main St, Apt #4"`
- **Example Invalid**: `"123 Main St<script>alert('xss')</script>"`

### Cities
- **Max Length**: 100 characters
- **Allowed Characters**: Letters, spaces, periods, hyphens, apostrophes, quotes
- **No Numbers**: Typically cities don't contain numbers
- **Example Valid**: `"San Francisco"`, `"St. Louis"`, `"O'Fallon"`
- **Example Invalid**: `"City123"`

### States
- **Max Length**: 50 characters
- **Allowed Characters**: Letters and spaces only
- **Case**: Normalized to uppercase
- **Example Valid**: `"CA"`, `"California"` → `"CALIFORNIA"`
- **Example Invalid**: `"CA123"`

### ZIP Codes
- **Max Length**: 10 characters
- **Allowed Characters**: Numbers, hyphens, spaces
- **Example Valid**: `"12345"`, `"12345-6789"`
- **Example Invalid**: `"1234A"`

### Text Areas (Job Descriptions)
- **Max Length**: 2000 characters
- **Security Checks**: XSS prevention, spam detection, URL limits
- **Spam Detection**: Character diversity analysis
- **URL Limits**: Maximum 2 URLs allowed
- **Example Valid**: `"I would like to serve as the Kingdom Seneschal..."`
- **Example Invalid**: Excessive repetition, multiple URLs, dangerous scripts

### Short Text Fields
- **Max Length**: 500 characters
- **Security Checks**: XSS prevention
- **Used For**: Principality, Barony, Group names

## Integration with Duty Request Form

### Form Processing Flow

1. **User Input**: Form data collected via Streamlit
2. **Basic Validation**: Check required fields are not empty
3. **Data Sanitization**: `sanitize_duty_request_form()` called
4. **Error Handling**: Display validation errors to user
5. **Email Processing**: Send sanitized data via Gmail API
6. **Logging**: Security events logged for monitoring

### Error Handling

**Validation Errors Displayed to User**:
```
❌ Data validation failed: Society Name contains potentially dangerous content
❌ Data validation failed: Email is too long (max 254 characters)
❌ Data validation failed: ZIP code contains invalid characters
```

**Security Events Logged**:
```
WARNING: Dangerous pattern detected in Society Name: '<script>alert("xss")</script>'
WARNING: Email injection attempt detected: 'user@example.com\r\nBCC: hacker@evil.com'
WARNING: Invalid characters in phone number: '555-123-ABCD'
```

## Testing

### Comprehensive Test Suite

**File**: `test_data_sanitizer.py`

**Test Categories**:
- Basic sanitization functions
- Field-specific validation
- Security attack scenarios
- Edge cases and error handling

**Security Scenarios Tested**:
- XSS attacks (script tags, event handlers)
- SQL injection attempts
- Email header injection
- Unicode-based attacks
- Spam and abuse patterns

**Run Tests**:
```bash
python test_data_sanitizer.py
python test_data_sanitizer.py --verbose
```

### Test Results
```
🔒 Running WKRegnum Data Sanitization Security Tests
============================================================
✅ All security tests passed!
📊 Tests run: 26
```

## Security Monitoring

### Logging Events

**Security Threats Detected**:
```python
logger.warning(f"Dangerous pattern detected in {field_name}: {repr(original_value)}")
logger.warning(f"Email injection attempt detected: {repr(email)}")
logger.warning(f"Invalid characters in {field_name}: {repr(value)}")
```

**Sanitization Activities**:
```python
logger.info(f"Data sanitized in field '{field_name}': {len(original)} -> {len(sanitized)} chars")
logger.warning(f"Significant sanitization in field '{field_name}': potential security threat detected")
```

### Monitoring Recommendations

1. **Regular Log Review**: Monitor for security event patterns
2. **Alert Thresholds**: Set up alerts for multiple failed attempts
3. **IP Tracking**: Consider tracking source IPs for repeated violations
4. **Rate Limiting**: Implement form submission rate limits
5. **CAPTCHA Enhancement**: Strengthen reCAPTCHA for suspicious activity

## Performance Considerations

### Optimization Features

1. **Compiled Regex Patterns**: Pre-compiled for better performance
2. **Early Rejection**: Dangerous patterns detected before processing
3. **Efficient Unicode Handling**: Minimal overhead normalization
4. **Selective Validation**: Field-appropriate validation rules
5. **Caching**: Pattern compilation cached at module load

### Performance Metrics

- **Average Processing Time**: < 1ms per form
- **Memory Usage**: Minimal overhead
- **CPU Impact**: Negligible for typical form volumes

## Production Deployment

### Environment Configuration

**No Additional Configuration Required**:
- Data sanitization is built into the form processing
- Automatic activation with form submission
- Logging integrated with existing system

### Monitoring Setup

**Log Monitoring**:
```bash
# Monitor security events
gcloud logs read --service=regnum-front --filter="textPayload:Dangerous pattern" --limit=50

# Monitor sanitization activity
gcloud logs read --service=regnum-front --filter="textPayload:Data sanitized" --limit=50
```

## Best Practices

### Development Guidelines

1. **Always Sanitize**: Never trust user input
2. **Validate Early**: Check data at form submission
3. **Log Security Events**: Monitor for attack patterns
4. **Test Thoroughly**: Include security test cases
5. **Update Patterns**: Keep dangerous pattern list current

### Security Recommendations

1. **Defense in Depth**: Multiple validation layers
2. **Fail Securely**: Reject suspicious input
3. **Log Everything**: Comprehensive security logging
4. **Regular Updates**: Keep sanitization patterns current
5. **User Education**: Clear error messages for legitimate users

## Future Enhancements

### Potential Improvements

1. **Machine Learning**: Pattern detection enhancement
2. **Reputation System**: Track user behavior patterns
3. **Advanced Spam Detection**: Content analysis algorithms
4. **Real-time Threat Intelligence**: Dynamic pattern updates
5. **Integration APIs**: External security service integration

### Scalability Considerations

1. **Caching**: Enhanced pattern caching
2. **Async Processing**: Non-blocking validation
3. **Distributed Validation**: Microservice architecture
4. **Performance Monitoring**: Detailed metrics collection

## Support and Maintenance

### Regular Maintenance Tasks

1. **Pattern Updates**: Review and update dangerous patterns
2. **Log Analysis**: Regular security log review
3. **Test Updates**: Keep test cases current
4. **Performance Monitoring**: Track sanitization performance
5. **Documentation Updates**: Keep security docs current

### Troubleshooting

**Common Issues**:
- False positives in pattern detection
- Performance impact on high-volume forms
- User confusion with validation errors

**Solutions**:
- Pattern refinement and testing
- Performance optimization
- Clear user error messages and help text

## Contact Information

For security-related issues or questions about the data sanitization system:

- **Security Issues**: webminister@westkingdom.org
- **Technical Support**: Development team
- **Documentation Updates**: Technical writing team