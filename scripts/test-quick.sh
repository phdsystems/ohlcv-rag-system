#!/bin/bash
# Quick test script - runs only simple unit tests with minimal dependencies

echo "🚀 Running quick tests with minimal dependencies..."

# Export UV optimizations
export UV_CONCURRENT_DOWNLOADS=8
export UV_COMPILE_BYTECODE=1
export UV_PREFER_BINARY=1

# Install minimal test dependencies only
echo "📦 Installing minimal test dependencies..."
uv pip install pytest pytest-cov pytest-mock --python 3.11

# Run unit tests
echo "🧪 Running unit tests..."
uv run pytest src/ -m unit -v --tb=short 2>/dev/null || uv run pytest src/ -v --tb=short

echo "✅ Quick tests completed!"