#!/bin/bash
# Smart installation script for OHLCV RAG System
# Automatically detects GPU and installs appropriate PyTorch version

set -e

echo "🚀 Starting smart installation..."

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

# Detect GPU and install appropriate PyTorch
echo "🔍 Detecting hardware capabilities..."

# Check for NVIDIA GPU
if command -v nvidia-smi &>/dev/null && nvidia-smi &>/dev/null; then
    echo "🚀 NVIDIA GPU detected - installing CUDA-enabled PyTorch for optimal performance"
    TORCH_INDEX="https://download.pytorch.org/whl/cu121"
    INSTALL_TYPE="GPU-accelerated"
else
    echo "💻 No GPU detected - installing CPU-only PyTorch (faster download, smaller size)"
    TORCH_INDEX="https://download.pytorch.org/whl/cpu"
    INSTALL_TYPE="CPU-only"
fi

echo "⚡ Installing dependencies with $INSTALL_TYPE PyTorch..."

# First, install the package without dependencies
uv sync --no-install-project --python 3.11

# Then install PyTorch with detected capabilities
uv pip install torch torchvision --index-url $TORCH_INDEX --python 3.11

# Finally, sync the rest
uv sync --python 3.11

echo "✅ Installation completed successfully!"
echo ""
echo "📝 Usage tips:"
echo "  - Run tests: uv run pytest tests/"
echo "  - Quick tests: ./scripts/test-quick.sh"
echo "  - Start app: uv run python main.py"