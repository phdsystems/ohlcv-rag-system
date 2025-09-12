#!/bin/bash
# CPU-only installation script for OHLCV RAG System

set -e

echo "🚀 Starting CPU-only installation..."

# Export UV optimizations
export UV_CONCURRENT_DOWNLOADS=8
export UV_COMPILE_BYTECODE=1
export UV_PREFER_BINARY=1
export UV_LINK_MODE=hardlink

# Check Python version
echo "🐍 Checking Python version..."
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# Install Python 3.11 if not available
echo "📦 Setting up Python 3.11..."
uv python install 3.11

# Clean previous installation
echo "🧹 Cleaning previous installation..."
rm -rf .venv

# Install with CPU-only PyTorch
echo "⚡ Installing dependencies with CPU-only PyTorch..."
echo "This uses CPU-only versions to avoid 3GB+ of CUDA downloads"

# First, install the package without dependencies
uv sync --no-install-project --python 3.11

# Then install with CPU-only torch
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu --python 3.11

# Finally, sync the rest
uv sync --python 3.11

echo "✅ Installation completed successfully!"
echo ""
echo "📝 Usage tips:"
echo "  - Run tests: uv run pytest tests/"
echo "  - Quick tests: ./scripts/test-quick.sh"
echo "  - Start app: uv run python main.py"