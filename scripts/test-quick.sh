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

# Run simple tests
echo "🧪 Running simple unit tests..."
.venv/bin/python -m pytest tests/test_simple.py -v --tb=short

echo "✅ Quick tests completed!"