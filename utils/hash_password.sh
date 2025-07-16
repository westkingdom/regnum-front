#!/bin/bash
# WKRegnum Password Hashing Utility Wrapper
# This script provides an easy way to hash passwords for JWT authentication

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "utils/password_hasher.py" ]; then
    print_error "This script must be run from the project root directory."
    print_info "Make sure you're in the regnum-front directory."
    exit 1
fi

# Display header
echo "=================================================="
echo "🔐 WKRegnum Password Hashing Utility"
echo "=================================================="
echo ""

# Check command line arguments
if [ $# -eq 0 ]; then
    print_info "Starting interactive mode..."
    echo ""
    python3 utils/password_hasher.py interactive
elif [ "$1" = "hash" ] && [ $# -eq 2 ]; then
    print_info "Hashing password..."
    echo ""
    python3 utils/password_hasher.py hash "$2"
elif [ "$1" = "verify" ] && [ $# -eq 3 ]; then
    print_info "Verifying password..."
    echo ""
    python3 utils/password_hasher.py verify "$2" "$3"
elif [ "$1" = "help" ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    echo "Usage:"
    echo "  $0                    # Interactive mode"
    echo "  $0 hash <password>    # Hash a password"
    echo "  $0 verify <password> <hash>  # Verify password against hash"
    echo "  $0 help               # Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 hash mypassword123"
    echo "  $0 verify mypassword123 '\$2b\$12\$...'"
    echo "  $0                    # Interactive mode (recommended)"
    echo ""
    print_info "For security, use interactive mode to avoid passwords in shell history."
else
    print_error "Invalid arguments."
    echo ""
    echo "Usage:"
    echo "  $0                    # Interactive mode"
    echo "  $0 hash <password>    # Hash a password"
    echo "  $0 verify <password> <hash>  # Verify password against hash"
    echo "  $0 help               # Show this help"
    echo ""
    print_warning "For security, use interactive mode to avoid passwords in shell history."
    exit 1
fi