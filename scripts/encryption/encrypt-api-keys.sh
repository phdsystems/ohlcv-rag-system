#!/bin/bash

# Script to encrypt API keys using ADE-Crypt
# This script helps manage encrypted API keys for the OHLCV RAG system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENCRYPTED_KEYS_DIR="./config/encrypted"
ENV_FILE=".env"
ENV_ENCRYPTED_FILE=".env.encrypted"

# Create encrypted keys directory if it doesn't exist
mkdir -p "$ENCRYPTED_KEYS_DIR"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to encrypt a single API key
encrypt_key() {
    local key_name=$1
    local key_value=$2
    local encrypted_file="$ENCRYPTED_KEYS_DIR/${key_name}.enc"
    
    if [ -z "$key_value" ] || [ "$key_value" == "your_"*"_here" ]; then
        print_warning "Skipping $key_name - no valid key found"
        return 1
    fi
    
    print_status "Encrypting $key_name..."
    echo "$key_value" | ade-crypt-lib encrypt-file - "$encrypted_file"
    
    if [ $? -eq 0 ]; then
        print_status "$key_name encrypted successfully to $encrypted_file"
        return 0
    else
        print_error "Failed to encrypt $key_name"
        return 1
    fi
}

# Function to decrypt a single API key
decrypt_key() {
    local key_name=$1
    local encrypted_file="$ENCRYPTED_KEYS_DIR/${key_name}.enc"
    
    if [ ! -f "$encrypted_file" ]; then
        print_error "Encrypted file not found: $encrypted_file"
        return 1
    fi
    
    ade-crypt-lib decrypt-file "$encrypted_file" -
}

# Function to setup encryption for all API keys
setup_encryption() {
    print_status "Setting up API key encryption..."
    
    # Check if .env file exists
    if [ ! -f "$ENV_FILE" ]; then
        print_error "$ENV_FILE not found. Please create it from .env.example"
        exit 1
    fi
    
    # Source the environment file
    set -a
    source "$ENV_FILE"
    set +a
    
    # List of API keys to encrypt
    declare -A api_keys=(
        ["CLAUDE_API_KEY"]="$CLAUDE_API_KEY"
        ["OPENAI_API_KEY"]="$OPENAI_API_KEY"
        ["ALPHA_VANTAGE_API_KEY"]="$ALPHA_VANTAGE_API_KEY"
        ["POLYGON_API_KEY"]="$POLYGON_API_KEY"
        ["WEAVIATE_API_KEY"]="$WEAVIATE_API_KEY"
        ["QDRANT_API_KEY"]="$QDRANT_API_KEY"
    )
    
    # Encrypt each API key
    for key_name in "${!api_keys[@]}"; do
        encrypt_key "$key_name" "${api_keys[$key_name]}"
    done
    
    # Create encrypted environment template
    print_status "Creating encrypted environment template..."
    cat > "$ENV_ENCRYPTED_FILE" << EOF
# Encrypted API Keys Configuration
# Use decrypt-api-keys.sh to decrypt these keys at runtime

# Claude API key (encrypted)
CLAUDE_API_KEY_ENCRYPTED=$ENCRYPTED_KEYS_DIR/CLAUDE_API_KEY.enc

# OpenAI API key (encrypted)
OPENAI_API_KEY_ENCRYPTED=$ENCRYPTED_KEYS_DIR/OPENAI_API_KEY.enc

# Alpha Vantage API key (encrypted)
ALPHA_VANTAGE_API_KEY_ENCRYPTED=$ENCRYPTED_KEYS_DIR/ALPHA_VANTAGE_API_KEY.enc

# Polygon.io API key (encrypted)
POLYGON_API_KEY_ENCRYPTED=$ENCRYPTED_KEYS_DIR/POLYGON_API_KEY.enc

# Weaviate API key (encrypted)
WEAVIATE_API_KEY_ENCRYPTED=$ENCRYPTED_KEYS_DIR/WEAVIATE_API_KEY.enc

# Qdrant API key (encrypted)
QDRANT_API_KEY_ENCRYPTED=$ENCRYPTED_KEYS_DIR/QDRANT_API_KEY.enc

# Copy other non-sensitive settings from .env
EOF
    
    # Copy non-sensitive settings
    grep -v "API_KEY" "$ENV_FILE" | grep -v "^#" | grep -v "^$" >> "$ENV_ENCRYPTED_FILE"
    
    print_status "Encryption setup complete!"
    print_warning "Remember to:"
    print_warning "  1. Remove plain text API keys from $ENV_FILE"
    print_warning "  2. Add $ENCRYPTED_KEYS_DIR to .gitignore"
    print_warning "  3. Store the encryption key securely"
}

# Function to verify encrypted keys
verify_encryption() {
    print_status "Verifying encrypted API keys..."
    
    for enc_file in "$ENCRYPTED_KEYS_DIR"/*.enc; do
        if [ -f "$enc_file" ]; then
            key_name=$(basename "$enc_file" .enc)
            print_status "Checking $key_name..."
            
            decrypted=$(decrypt_key "$key_name" 2>/dev/null)
            if [ $? -eq 0 ] && [ -n "$decrypted" ]; then
                print_status "$key_name: ✓ (decryption successful)"
            else
                print_error "$key_name: ✗ (decryption failed)"
            fi
        fi
    done
}

# Main command handling
case "${1:-}" in
    setup)
        setup_encryption
        ;;
    verify)
        verify_encryption
        ;;
    encrypt)
        if [ -z "$2" ] || [ -z "$3" ]; then
            print_error "Usage: $0 encrypt <key_name> <key_value>"
            exit 1
        fi
        encrypt_key "$2" "$3"
        ;;
    decrypt)
        if [ -z "$2" ]; then
            print_error "Usage: $0 decrypt <key_name>"
            exit 1
        fi
        decrypt_key "$2"
        ;;
    *)
        echo "Usage: $0 {setup|verify|encrypt|decrypt}"
        echo ""
        echo "Commands:"
        echo "  setup    - Encrypt all API keys from .env file"
        echo "  verify   - Verify all encrypted keys can be decrypted"
        echo "  encrypt  - Encrypt a single API key"
        echo "  decrypt  - Decrypt a single API key"
        exit 1
        ;;
esac