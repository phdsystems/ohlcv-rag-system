# Testing Guide

## Overview

The OHLCV RAG System uses a **hybrid testing strategy** with co-located unit tests and centralized integration tests. For detailed information about our testing philosophy and organization, see the [Testing Strategy](../architecture/testing-strategy.md).

## Test Structure

Our tests follow a hybrid approach:

### Co-located Unit Tests (in `src/`)
```
src/
├── application_test.py              # Unit tests next to source
├── rag_pipeline_test.py            
├── core/
│   └── *_test.py                   # Module-specific tests
├── data_adapters/
│   └── *_test.py                   
└── vector_stores/
    └── *_test.py                   
```

### Centralized Integration & E2E Tests (in `tests/`)
```
tests/
├── integration/                     # Integration tests
│   ├── test_chromadb_integration.py
│   ├── test_weaviate_integration.py
│   ├── test_qdrant_integration.py
│   └── test_end_to_end.py
├── e2e/                            # End-to-end tests
│   ├── test_e2e_simple.py
│   └── test_testcontainers.py
├── conftest.py                     # Shared fixtures
├── pytest.ini                      # Pytest configuration
└── .coveragerc                     # Coverage configuration
```

## Running Tests

### Using Make Commands

```bash
# Run all unit tests
make test

# Run all tests with coverage report
make test-all

# Run simple mock-based tests only
make test-simple

# Install test dependencies
make test-install
```

### Integration Tests

```bash
# Run all integration tests (requires Docker)
make test-integration

# Run specific vector store integration tests
make test-chromadb
make test-weaviate
make test-qdrant

# Install integration test dependencies
make test-integration-install
```

### Using Pytest Directly

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_simple.py -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Run tests matching a pattern
python -m pytest tests/ -k "test_data_ingestion"

# Run tests in parallel (requires pytest-xdist)
python -m pytest tests/ -n auto

# Run with verbose output
python -m pytest tests/ -v

# Show local variables in tracebacks
python -m pytest tests/ -l

# Stop on first failure
python -m pytest tests/ -x

# Run only marked tests
python -m pytest tests/ -m "unit"
python -m pytest tests/ -m "integration"
```

## Test Configuration

### pytest.ini

The `pytest.ini` file configures test behavior:

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    unit: Unit tests
    integration: Integration tests requiring external services
    slow: Slow running tests
    requires_api: Tests requiring API keys
```

### Coverage Configuration

The `.coveragerc` file configures coverage reporting:

```ini
[run]
source = src
omit = 
    */tests/*
    */test_*.py
    */__init__.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
```

## Writing Tests

### Unit Test Example

```python
import pytest
from unittest.mock import Mock, patch
from src.data_adapters.yahoo_adapter import YahooFinanceAdapter

class TestYahooFinanceAdapter:
    def test_fetch_data_success(self):
        adapter = YahooFinanceAdapter()
        with patch('yfinance.download') as mock_download:
            mock_download.return_value = Mock()
            data = adapter.fetch_data(['AAPL'], '2024-01-01', '2024-01-31')
            assert data is not None
            mock_download.assert_called_once()
    
    def test_fetch_data_invalid_ticker(self):
        adapter = YahooFinanceAdapter()
        with pytest.raises(ValueError):
            adapter.fetch_data(['INVALID'], '2024-01-01', '2024-01-31')
```

### Integration Test Example

```python
import pytest
from testcontainers.compose import DockerCompose
from src.vector_stores.chromadb_store import ChromaDBStore

@pytest.mark.integration
class TestChromaDBIntegration:
    @pytest.fixture(scope="class")
    def docker_compose(self):
        with DockerCompose(".", compose_file_name="docker-compose.test.yml") as compose:
            compose.wait_for("chromadb")
            yield compose
    
    def test_chromadb_connection(self, docker_compose):
        store = ChromaDBStore(host="localhost", port=8000)
        assert store.health_check() is True
    
    def test_data_persistence(self, docker_compose):
        store = ChromaDBStore(host="localhost", port=8000)
        store.add_documents([{"text": "test", "metadata": {}}])
        results = store.search("test", k=1)
        assert len(results) == 1
```

## Test Fixtures

Common fixtures are defined in `conftest.py`:

```python
@pytest.fixture
def sample_ohlcv_data():
    """Provides sample OHLCV data for testing"""
    return pd.DataFrame({
        'Open': [100, 101, 102],
        'High': [105, 106, 107],
        'Low': [99, 100, 101],
        'Close': [104, 105, 106],
        'Volume': [1000000, 1100000, 1200000]
    })

@pytest.fixture
def mock_llm():
    """Provides a mock LLM for testing"""
    mock = Mock()
    mock.generate.return_value = "Test response"
    return mock

@pytest.fixture
def temp_vector_store(tmp_path):
    """Provides a temporary vector store for testing"""
    return ChromaDBStore(persist_directory=str(tmp_path))
```

## Continuous Integration

Tests run automatically on GitHub Actions for:
- Every push to main branch
- Every pull request
- Scheduled daily runs

### CI Configuration

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: make test-install
      - run: make test-all
```

## Test Dependencies

### Unit Tests
- pytest >= 7.0.0
- pytest-cov >= 4.0.0
- pytest-mock >= 3.10.0
- faker >= 18.0.0

### Integration Tests
- testcontainers >= 3.7.0
- pytest-asyncio >= 0.21.0
- pytest-xdist >= 3.0.0
- docker >= 6.0.0

## Troubleshooting

### Common Issues

1. **Tests fail with import errors**
   ```bash
   # Ensure you're in the project root
   cd /path/to/ohlcv-rag-system
   # Install in development mode
   pip install -e .
   ```

2. **Docker tests fail**
   ```bash
   # Ensure Docker is running
   docker version
   # Clean up containers
   docker-compose down -v
   ```

3. **Coverage reports missing files**
   ```bash
   # Run with explicit source
   pytest --cov=src --cov-report=html tests/
   ```

## Performance Testing

For performance testing, use pytest-benchmark:

```python
def test_vector_search_performance(benchmark, vector_store):
    result = benchmark(vector_store.search, "test query", k=10)
    assert len(result) <= 10
```

Run performance tests:
```bash
pytest tests/performance/ --benchmark-only
```

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Mock External Services**: Use mocks for APIs and databases in unit tests
3. **Use Fixtures**: Share common setup code via fixtures
4. **Test Edge Cases**: Include tests for error conditions
5. **Descriptive Names**: Use clear, descriptive test names
6. **Arrange-Act-Assert**: Follow the AAA pattern in tests
7. **Keep Tests Fast**: Unit tests should run in milliseconds
8. **Test Coverage**: Aim for >80% code coverage