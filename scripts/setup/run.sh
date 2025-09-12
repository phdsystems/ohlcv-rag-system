#!/bin/bash

# Quick run script for OHLCV RAG System

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Running setup first..."
    ./setup.sh
fi

# Run with uv
echo "Starting OHLCV RAG System..."
uv run python main.py