#!/usr/bin/env python
"""
Test runner script for OHLCV RAG System
"""

import sys
import pytest
import os

def run_tests():
    """Run all tests with coverage report"""
    
    # Add parent directory to path so tests can import src modules
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Test configuration
    args = [
        '-v',  # Verbose output
        '--tb=short',  # Short traceback format
        '--cov=src',  # Coverage for src directory
        '--cov-report=term-missing',  # Show missing lines in coverage
        '--cov-report=html:htmlcov',  # Generate HTML coverage report
        '--cov-config=.coveragerc',  # Coverage configuration
    ]
    
    # Add any command line arguments
    args.extend(sys.argv[1:])
    
    # Run pytest
    exit_code = pytest.main(args)
    
    if exit_code == 0:
        print("\n✅ All tests passed successfully!")
    else:
        print(f"\n❌ Tests failed with exit code: {exit_code}")
    
    return exit_code

if __name__ == '__main__':
    sys.exit(run_tests())