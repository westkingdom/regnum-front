# Password Hashing Utility for WKRegnum

This document describes how to use the password hashing utility for managing user passwords in the WKRegnum JWT authentication system.

## Overview

The WKRegnum application uses bcrypt for secure password hashing. This utility provides command-line tools to:

- Hash new passwords for user accounts
- Verify passwords against existing hashes
- Interactive mode for secure password entry

## Security Features

- **bcrypt hashing**: Industry-standard password hashing with salt
- **Secure input**: Interactive mode hides passwords from shell history
- **Backward compatibility**: Supports both bcrypt hashes and demo passwords
- **Salt generation**: Automatic random salt generation for each password

## Usage Methods

### 1. Interactive Mode (Recommended)

The safest way to hash passwords without exposing them in shell history:

```bash
./hash_password.sh
```

Or directly:

```bash
python3 utils/password_hasher.py interactive
```

**Features:**
- Secure password input (hidden from terminal)
- Password confirmation
- Hash verification testing
- No passwords stored in shell history

### 2. Command Line Mode

For scripting or quick hashing:

```bash
# Hash a password
./hash_password.sh hash mypassword123
python3 utils/password_hasher.py hash mypassword123

# Verify a password
./hash_password.sh verify mypassword123 '$2b$12$...'
python3 utils/password_hasher.py verify mypassword123 '$2b$12$...'
```

**⚠️ Security Warning**: Command line mode stores passwords in shell history. Use interactive mode for production passwords.

### 3. Help and Documentation

```bash
./hash_password.sh help
python3 utils/password_hasher.py --help
```

## Examples

### Hashing a New Password

```bash
$ ./hash_password.sh hash admin123
==================================================
🔐 WKRegnum Password Hashing Utility
==================================================

ℹ️  Hashing password...

Password hashed successfully!
Hash: $2b$12$dQ57HkG5ilZF622JV.OO4.dXAIQ36lGZpVqSswgHnzO3dbc1O5D3q

Add this to your USERS_DB:
'password_hash': '$2b$12$dQ57HkG5ilZF622JV.OO4.dXAIQ36lGZpVqSswgHnzO3dbc1O5D3q'
```

### Interactive Mode Session

```bash
$ ./hash_password.sh
==================================================
🔐 WKRegnum Password Hashing Utility
==================================================

=== WKRegnum Password Hasher - Interactive Mode ===

Options:
1. Hash a new password
2. Verify a password against a hash
3. Exit

Select an option (1-3): 1

--- Hash Password ---
Enter password to hash: [hidden input]
Confirm password: [hidden input]
✅ Password hashed successfully!
Hash: $2b$12$example...

You can use this hash in your USERS_DB configuration:
'password_hash': '$2b$12$example...'
```

## Integration with WKRegnum

### Adding New Users

1. **Hash the password**:
   ```bash
   ./hash_password.sh
   # Select option 1, enter password securely
   ```

2. **Update USERS_DB** in `utils/jwt_auth.py`:
   ```python
   USERS_DB = {
       'newuser@westkingdom.org': {
           'password_hash': '$2b$12$your_generated_hash_here',
           'name': 'New User',
           'role': 'user'
       }
   }
   ```

3. **Deploy the changes**:
   ```bash
   git add utils/jwt_auth.py
   git commit -m "Add new user account"
   git push origin main
   gcloud builds submit --config cloudbuild.yaml
   ```

### Password Security Best Practices

1. **Use Interactive Mode**: Avoid passwords in shell history
2. **Strong Passwords**: Use complex passwords with mixed characters
3. **Unique Salts**: Each password gets a unique salt automatically
4. **Regular Updates**: Change passwords periodically
5. **Secure Storage**: Store hashes securely, never plain text passwords

## Technical Details

### bcrypt Configuration

- **Algorithm**: bcrypt with automatic salt generation
- **Cost Factor**: 12 (default, provides good security/performance balance)
- **Salt**: Random salt generated for each password
- **Output Format**: Standard bcrypt hash format (`$2b$12$...`)

### Hash Format

bcrypt hashes follow this format:
```
$2b$12$saltsaltsaltsaltsaltsalthashhashhashhashhashhashhash
│  │  │                        │
│  │  └─ 22-character salt     └─ 31-character hash
│  └─ Cost factor (12)
└─ bcrypt version (2b)
```

### Backward Compatibility

The authentication system supports both:
- **bcrypt hashes**: For production security (starts with `$2b$`)
- **Plain text**: For demo credentials (simple string comparison)

This allows existing demo credentials to work while supporting secure hashes for production users.

## Files

- `utils/password_hasher.py`: Core Python utility
- `hash_password.sh`: Shell script wrapper
- `utils/jwt_auth.py`: Authentication system with bcrypt support
- `requirements.txt`: Includes bcrypt dependency

## Dependencies

- **bcrypt**: Secure password hashing library
- **Python 3.7+**: Required for bcrypt and typing support
- **getpass**: Secure password input (built-in)

## Troubleshooting

### Common Issues

1. **"ModuleNotFoundError: No module named 'bcrypt'"**
   ```bash
   pip install bcrypt==4.1.2
   ```

2. **"This script must be run from the project root directory"**
   ```bash
   cd /path/to/regnum-front
   ./hash_password.sh
   ```

3. **Permission denied**
   ```bash
   chmod +x hash_password.sh
   chmod +x utils/password_hasher.py
   ```

### Verification Testing

Test that your hashed password works:

```bash
# Hash a password
./hash_password.sh hash testpass123

# Verify it works
./hash_password.sh verify testpass123 '$2b$12$your_hash_here'
```

## Production Deployment

### Environment Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Generate Production Passwords**:
   ```bash
   ./hash_password.sh  # Use interactive mode
   ```

3. **Update User Database**:
   - Replace demo credentials in `utils/jwt_auth.py`
   - Use bcrypt hashes for all production accounts
   - Remove or disable demo accounts

4. **Deploy**:
   ```bash
   git add .
   git commit -m "Update production user accounts"
   git push origin main
   gcloud builds submit --config cloudbuild.yaml
   ```

### Security Checklist

- [ ] All production passwords use bcrypt hashes
- [ ] Demo credentials removed or disabled
- [ ] Strong passwords enforced
- [ ] JWT_SECRET updated for production
- [ ] Password hashing utility access restricted
- [ ] Regular password rotation policy established

## Future Enhancements

Potential improvements:
- Database integration for user management
- Password strength validation
- Bulk user import/export
- Password expiration policies
- Integration with external authentication systems