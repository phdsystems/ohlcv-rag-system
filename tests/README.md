# OHLCV RAG System - Test Suite

## Overview

This directory contains the comprehensive test suite for the OHLCV RAG System. The tests include both unit tests and integration tests using Testcontainers for realistic testing with actual databases.

## Test Structure

```
tests/
├── __init__.py                          # Test package initialization
├── conftest.py                         # Shared fixtures for unit tests
├── conftest_full.py                    # Full fixtures with pandas/numpy
├── run_tests.py                        # Test runner script
├── test_data_ingestion.py              # Unit tests for data ingestion
├── test_data_adapters.py               # Unit tests for data adapters
├── test_vector_store.py                # Unit tests for vector stores
├── test_retriever.py                   # Unit tests for retriever
├── test_rag_pipeline.py                # Unit tests for RAG pipeline
├── test_application.py                 # Unit tests for application
├── test_main.py                       # Unit tests for main entry
├── test_simple.py                      # Simple mock-based tests
└── integration/                        # Integration tests with Testcontainers
    ├── __init__.py
    ├── conftest.py                     # Testcontainers fixtures
    ├── test_chromadb_integration.py    # ChromaDB integration tests
    ├── test_weaviate_integration.py    # Weaviate integration tests
    ├── test_qdrant_integration.py      # Qdrant integration tests
    └── test_end_to_end.py             # End-to-end integration tests
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

## Integration Tests with Testcontainers

### Overview
Integration tests use Testcontainers to spin up real database instances in Docker containers, providing realistic testing environments.

### Prerequisites
- Docker must be installed and running
- Install integration test dependencies:
```bash
pip install -r requirements-integration.txt
```

### Running Integration Tests

```bash
# Run only integration tests
python -m pytest tests/integration/ -m integration

# Run specific vector store integration tests
python -m pytest tests/integration/test_chromadb_integration.py
python -m pytest tests/integration/test_weaviate_integration.py
python -m pytest tests/integration/test_qdrant_integration.py

# Run end-to-end tests
python -m pytest tests/integration/test_end_to_end.py -m slow

# Run with verbose output
python -m pytest tests/integration/ -v -s
```

### Testcontainers Features

1. **Automatic Container Management**: Containers are automatically started before tests and cleaned up after
2. **Isolated Testing**: Each test gets a clean database instance
3. **Real Database Testing**: Tests run against actual database implementations
4. **Port Management**: Automatic port allocation prevents conflicts

### Available Fixtures

#### Vector Store Containers
- `chromadb_container`: ChromaDB server instance
- `weaviate_container`: Weaviate server instance
- `qdrant_container`: Qdrant server instance
- `milvus_container`: Milvus server instance (with dependencies)

#### Database Containers
- `postgres_container`: PostgreSQL database
- `redis_container`: Redis cache

#### Clean Instances
- `clean_chromadb`: Fresh ChromaDB client for each test
- `clean_weaviate`: Fresh Weaviate client for each test
- `clean_qdrant`: Fresh Qdrant client for each test

## Test Markers

Tests are marked with different categories for selective execution:

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests (requires Docker)
pytest -m integration

# Run slow tests
pytest -m slow

# Run tests that don't require Docker
pytest -m "not docker"
```

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
# Unit test dependencies
pip install -r requirements-test.txt

# Integration test dependencies
pip install -r requirements-integration.txt
```

### Docker Issues
For Testcontainers/integration tests:
- Ensure Docker is running: `docker ps`
- Check Docker permissions: `docker run hello-world`
- Clean up containers: `docker container prune`
- Clean up volumes: `docker volume prune`

### Mock Issues
If mocks aren't working correctly, check:
- Import paths in patch decorators
- Mock return values match expected types
- Mock side effects are properly configured

### Testcontainers Timeout
If containers take too long to start:
- Increase timeout in conftest.py `wait_for_logs(timeout=60)`
- Pre-pull images: `docker pull chromadb/chroma:latest`
- Check system resources

## Performance Considerations

### Integration Test Performance
- Integration tests are slower due to container startup
- Use `@pytest.mark.slow` for long-running tests
- Run integration tests separately in CI/CD
- Consider using container reuse for faster local development

### Parallel Execution
```bash
# Run tests in parallel (requires pytest-xdist)
pip install pytest-xdist
pytest -n auto tests/
```

## Contributing

When contributing tests:
1. Ensure all new code has corresponding tests
2. Add appropriate test markers (@pytest.mark.unit, @pytest.mark.integration)
3. Run the full test suite before submitting
4. Maintain or improve code coverage
5. Follow existing test patterns and conventions
6. Update this README if adding new test categories
7. For integration tests, ensure proper cleanup in fixtures