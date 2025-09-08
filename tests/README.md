# OHLCV RAG System - Test Suite

## Overview

This directory contains the comprehensive test suite for the OHLCV RAG System. The tests cover all major components including data ingestion, vector storage, retrieval, and the RAG pipeline.

## Test Structure

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py             # Shared fixtures and test configuration
├── run_tests.py            # Test runner script
├── test_data_ingestion.py  # Tests for data ingestion module
├── test_data_adapters.py   # Tests for data source adapters
├── test_vector_store.py    # Tests for vector store operations
├── test_retriever.py       # Tests for retrieval functionality
├── test_rag_pipeline.py    # Tests for RAG pipeline
├── test_application.py     # Tests for main application
└── test_main.py           # Tests for main entry points
```

## Running Tests

### Run All Tests
```bash
# From project root
python -m pytest tests/

# Or use the test runner script
python tests/run_tests.py
```

### Run Specific Test File
```bash
python -m pytest tests/test_data_ingestion.py
```

### Run with Coverage
```bash
python -m pytest tests/ --cov=src --cov-report=term-missing
```

### Run with Verbose Output
```bash
python -m pytest tests/ -v
```

### Run Specific Test
```bash
python -m pytest tests/test_data_ingestion.py::TestOHLCVDataIngestion::test_fetch_ohlcv_data
```

## Test Coverage

The test suite aims for comprehensive coverage of:

- **Data Ingestion** (test_data_ingestion.py)
  - Data fetching from various sources
  - Technical indicator calculation
  - Document preparation for vector store
  - Error handling and edge cases

- **Data Adapters** (test_data_adapters.py)
  - Yahoo Finance adapter
  - Alpha Vantage adapter
  - Polygon.io adapter
  - CSV file adapter
  - Custom adapter registration

- **Vector Store** (test_vector_store.py)
  - ChromaDB operations
  - FAISS operations
  - Document CRUD operations
  - Search and filtering

- **Retriever** (test_retriever.py)
  - Basic retrieval
  - Filtered retrieval (by ticker, date range)
  - Batch retrieval
  - Score-based filtering

- **RAG Pipeline** (test_rag_pipeline.py)
  - Query processing
  - Prompt templates
  - Different query types (general, pattern, comparison, prediction)
  - Batch query processing

- **Application** (test_application.py)
  - Component initialization
  - Data ingestion flow
  - Query processing
  - State management
  - Error handling

## Fixtures

Common fixtures are defined in `conftest.py`:

- `sample_ohlcv_data`: Generated OHLCV DataFrame
- `sample_tickers`: List of test ticker symbols
- `mock_api_response`: Mocked API response data
- `temp_csv_file`: Temporary CSV file for testing
- `mock_vector_store`: Mocked vector store instance
- `mock_llm`: Mocked language model
- `sample_documents`: Sample documents for testing
- `env_setup`: Environment variable setup

## Mocking Strategy

Tests use `unittest.mock` extensively to:
- Mock external API calls
- Mock database operations
- Mock file I/O operations
- Isolate components for unit testing

## Test Requirements

Install test dependencies:
```bash
pip install pytest pytest-cov pytest-mock
```

Or if using uv:
```bash
uv pip install pytest pytest-cov pytest-mock
```

## Writing New Tests

When adding new functionality, follow these guidelines:

1. **Create test file**: Name it `test_<module_name>.py`
2. **Use fixtures**: Leverage existing fixtures from `conftest.py`
3. **Mock external dependencies**: Don't make real API calls or database connections
4. **Test edge cases**: Include tests for error conditions and boundary cases
5. **Use descriptive names**: Test method names should clearly describe what is being tested

Example test structure:
```python
class TestNewComponent:
    def test_initialization(self):
        """Test component initialization"""
        pass
    
    def test_normal_operation(self):
        """Test normal operation flow"""
        pass
    
    def test_error_handling(self):
        """Test error handling"""
        pass
    
    def test_edge_cases(self):
        """Test edge cases and boundaries"""
        pass
```

## Continuous Integration

The test suite is designed to run in CI/CD pipelines. Use the following command for CI:

```bash
python -m pytest tests/ --cov=src --cov-report=xml --cov-report=term
```

## Coverage Goals

- Minimum coverage target: 80%
- Critical components (data ingestion, RAG pipeline): 90%+
- Utility functions: 70%+

## Troubleshooting

### Import Errors
If you encounter import errors, ensure you're running tests from the project root:
```bash
cd /path/to/ohlcv-rag-system
python -m pytest tests/
```

### Missing Dependencies
Install all test dependencies:
```bash
pip install -r requirements-test.txt  # If available
# Or
pip install pytest pytest-cov pytest-mock
```

### Mock Issues
If mocks aren't working correctly, check:
- Import paths in patch decorators
- Mock return values match expected types
- Mock side effects are properly configured

## Contributing

When contributing tests:
1. Ensure all new code has corresponding tests
2. Run the full test suite before submitting
3. Maintain or improve code coverage
4. Follow existing test patterns and conventions
5. Update this README if adding new test categories