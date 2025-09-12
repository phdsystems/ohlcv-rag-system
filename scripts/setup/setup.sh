#!/bin/bash

# OHLCV RAG System Setup Script

echo "================================"
echo "OHLCV RAG System Setup with uv"
echo "================================"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "uv is not installed. Installing uv..."
    
    # Detect OS and install accordingly
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            echo "Installing uv with Homebrew..."
            brew install uv
        else
            echo "Installing uv with installer script..."
            curl -LsSf https://astral.sh/uv/install.sh | sh
        fi
    else
        # Linux/WSL
        echo "Installing uv with installer script..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
    fi
    
    # Add to PATH if needed
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Verify uv installation
if command -v uv &> /dev/null; then
    echo "✓ uv is installed (version: $(uv --version))"
else
    echo "✗ Failed to install uv. Please install it manually."
    exit 1
fi

# Install dependencies with uv (handles venv automatically)
echo ""
echo "Installing dependencies..."
uv sync

echo "✓ Virtual environment created at .venv/"
echo "✓ Dependencies installed"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env and add your OpenAI API key"
    echo "    Without it, the LLM features will not work."
else
    echo "✓ .env file already exists"
fi

# Create data directory
mkdir -p data
echo "✓ Created data directory"

echo ""
echo "================================"
echo "Setup Complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your OpenAI API key"
echo "2. Run the system with: python main.py"
echo ""
echo "To activate the virtual environment in future sessions:"
echo "  source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate"
echo ""
echo "Or use uv to run commands directly:"
echo "  uv run python main.py"