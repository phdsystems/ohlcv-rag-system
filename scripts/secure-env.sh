#!/bin/bash

# Script to secure .env file after encryption
# This removes sensitive API keys while preserving other settings

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if encryption was done
if [ ! -d "./config/encrypted" ] || [ -z "$(ls -A ./config/encrypted/*.enc 2>/dev/null)" ]; then
    echo -e "${RED}[ERROR]${NC} No encrypted keys found. Run encryption first:"
    echo "  ./scripts/encrypt-api-keys.sh setup"
    exit 1
fi

# Backup original .env
if [ -f ".env" ]; then
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    echo -e "${GREEN}[INFO]${NC} Created backup of .env"
fi

# Create new .env with sensitive keys removed
if [ -f ".env" ]; then
    echo -e "${YELLOW}[INFO]${NC} Removing sensitive keys from .env..."
    
    # Create temp file with non-sensitive settings
    grep -v "_API_KEY" .env | grep -v "^#" | grep -v "^$" > .env.tmp || true
    
    # Add header
    cat > .env.secured << 'EOF'
# Secured Environment File
# API keys have been encrypted and stored in ./config/encrypted/
# To use encrypted keys, the application will automatically decrypt them at runtime

# Non-sensitive settings preserved below:

EOF
    
    # Append non-sensitive settings
    cat .env.tmp >> .env.secured 2>/dev/null || true
    rm -f .env.tmp
    
    # Add reference to encrypted keys
    cat >> .env.secured << 'EOF'

# Encrypted API Keys Location
# Keys are stored encrypted in: ./config/encrypted/
# The application will automatically use these encrypted keys
EOF
    
    echo -e "${GREEN}[SUCCESS]${NC} Created secured environment file: .env.secured"
    echo ""
    echo "Next steps:"
    echo "  1. Review .env.secured to ensure it looks correct"
    echo "  2. Rename it: mv .env.secured .env"
    echo "  3. Remove backup when confident: rm .env.backup.*"
    echo ""
    echo -e "${YELLOW}[IMPORTANT]${NC} Your original .env is backed up with timestamp"
else
    echo -e "${RED}[ERROR]${NC} No .env file found"
    exit 1
fi

# Show what keys are encrypted
echo -e "${GREEN}[INFO]${NC} Encrypted keys available:"
for enc_file in ./config/encrypted/*.enc; do
    if [ -f "$enc_file" ]; then
        key_name=$(basename "$enc_file" .enc)
        echo "  ✓ $key_name"
    fi
done