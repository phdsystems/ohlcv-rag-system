# Testing Strategy

## Overview

The OHLCV RAG System uses a **hybrid testing strategy** that combines co-located unit tests with centralized integration tests. This approach balances developer ergonomics with comprehensive test coverage.

## Test Organization

### Co-located Unit Tests (in `src/`)

Unit tests are placed directly next to the source files they test, following the pattern `*_test.py`:

```
src/
├── application.py
├── application_test.py              # Unit tests for application.py
├── application_integration_test.py  # Integration tests for application
├── rag_pipeline.py
├── rag_pipeline_test.py            # Unit tests for rag_pipeline.py
├── core/
│   ├── base_processor.py
│   ├── base_processor_test.py      # Unit tests for base_processor.py
│   ├── exceptions.py
│   └── exceptions_test.py          # Unit tests for exceptions.py
├── data_adapters/
│   ├── yahoo_finance.py
│   ├── yahoo_finance_test.py       # Unit tests for yahoo_finance.py
│   ├── indicators.py
│   └── indicators_test.py          # Unit tests for indicators.py
└── vector_stores/
    ├── chromadb_store.py
    └── chromadb_store_test.py      # Unit tests for chromadb_store.py
```

**Benefits:**
- ✅ Tests are immediately visible next to the code
- ✅ Easy to maintain - changes to code prompt test updates
- ✅ Fast feedback loop during development
- ✅ Can run individual module tests quickly
- ✅ Encourages test-driven development (TDD)

### Centralized Integration & E2E Tests (in `tests/`)

Integration and end-to-end tests are organized in a dedicated `tests/` directory:

```
tests/
├── integration/
│   ├── test_chromadb_integration.py    # ChromaDB integration
│   ├── test_qdrant_integration.py      # Qdrant integration
│   ├── test_weaviate_integration.py    # Weaviate integration
│   ├── test_end_to_end.py             # Full pipeline tests
│   └── test_real_dependencies.py       # Tests with real services
├── e2e/
│   ├── test_e2e_simple.py             # Simple E2E scenarios
│   ├── test_testcontainers.py         # Docker container tests
│   └── test_real_functionality.py      # Real-world workflows
├── pytest.ini                          # Pytest configuration
├── .coveragerc                         # Coverage configuration
└── conftest.py                         # Shared fixtures
```

**Benefits:**
- ✅ Clear separation of integration concerns
- ✅ Shared fixtures and utilities
- ✅ Tests that span multiple components
- ✅ Container-based testing support
- ✅ Easier CI/CD pipeline configuration

## Test Levels

### 1. Unit Tests
- **Location**: Co-located with source (`src/**/*_test.py`)
- **Purpose**: Test individual functions and classes in isolation
- **Dependencies**: Mocked
- **Speed**: Fast (< 1 second per test)
- **Run with**: `pytest src/`

### 2. Integration Tests
- **Location**: `tests/integration/`
- **Purpose**: Test component interactions
- **Dependencies**: May use real services or containers
- **Speed**: Medium (1-10 seconds per test)
- **Run with**: `pytest tests/integration/`

### 3. End-to-End Tests
- **Location**: `tests/e2e/`
- **Purpose**: Test complete user workflows
- **Dependencies**: Full system with real services
- **Speed**: Slow (10+ seconds per test)
- **Run with**: `pytest tests/e2e/`

## Running Tests

### Run All Tests
```bash
# Using pytest directly
pytest

# Using Make
make test

# With coverage
pytest --cov=src --cov-report=html
```

### Run Specific Test Levels
```bash
# Unit tests only
pytest src/

# Integration tests only
pytest tests/integration/

# E2E tests only
pytest tests/e2e/

# Specific module tests
pytest src/rag_pipeline_test.py
pytest src/data_adapters/
```

### Run with Coverage
```bash
# Generate coverage report
pytest --cov=src --cov-report=html

# Using Make
make test-coverage
```

### Run in Docker
```bash
# Run tests in container
make test-docker

# Run specific test suite
docker-compose run --rm test pytest tests/integration/
```

## Test Naming Conventions

### File Naming
- **Co-located unit tests**: `{module_name}_test.py`
- **Integration/E2E tests**: `test_{feature_name}.py`

### Test Function Naming
```python
# Unit tests
def test_should_process_valid_input():
    """Test that valid input is processed correctly."""
    pass

def test_should_raise_error_on_invalid_input():
    """Test that invalid input raises appropriate error."""
    pass

# Integration tests
def test_chromadb_connection():
    """Test ChromaDB connection and basic operations."""
    pass

# E2E tests
def test_full_rag_pipeline_workflow():
    """Test complete RAG pipeline from ingestion to query."""
    pass
```

## Test Categories

### By Speed (Pytest Markers)
```python
@pytest.mark.unit       # Fast, isolated tests
@pytest.mark.integration # Medium speed, some dependencies
@pytest.mark.e2e        # Slow, full system tests
@pytest.mark.slow       # Any slow test
```

### By Requirements
```python
@pytest.mark.requires_docker  # Needs Docker
@pytest.mark.requires_gpu     # Needs GPU
@pytest.mark.requires_api_key # Needs API keys
```

### Run by Category
```bash
# Run only unit tests
pytest -m unit

# Skip slow tests
pytest -m "not slow"

# Run tests that don't require Docker
pytest -m "not requires_docker"
```

## Mocking Strategy

### Unit Tests
```python
# Use unittest.mock or pytest-mock
from unittest.mock import Mock, patch

def test_application_with_mock():
    mock_llm = Mock()
    mock_llm.query.return_value = "Mocked response"
    
    app = Application(llm=mock_llm)
    result = app.process("test query")
    
    assert result == "Mocked response"
    mock_llm.query.assert_called_once_with("test query")
```

### Integration Tests
```python
# Use test containers or in-memory databases
import testcontainers.compose as tc

@pytest.fixture
def chromadb_container():
    with tc.DockerCompose(".", compose_file_name="docker-compose.test.yml") as compose:
        compose.wait_for("chromadb")
        yield compose
```

## Coverage Requirements

### Minimum Coverage Thresholds
- **Overall**: 80%
- **Unit tests**: 90% for business logic
- **Integration tests**: 70% for workflows
- **Critical paths**: 100%

### Coverage Configuration (`.coveragerc`)
```ini
[run]
source = src
omit = 
    *_test.py
    */tests/*
    */migrations/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
```

## CI/CD Integration

### GitHub Actions Workflow
```yaml
test:
  runs-on: ubuntu-latest
  strategy:
    matrix:
      test-type: [unit, integration, e2e]
  steps:
    - name: Run ${{ matrix.test-type }} tests
      run: |
        if [ "${{ matrix.test-type }}" = "unit" ]; then
          pytest src/ -m unit
        elif [ "${{ matrix.test-type }}" = "integration" ]; then
          pytest tests/integration/ -m integration
        else
          pytest tests/e2e/ -m e2e
        fi
```

## Best Practices

### 1. Test Isolation
- Each test should be independent
- Use fixtures for setup/teardown
- Clean up resources after tests

### 2. Test Data
- Use factories or builders for test data
- Keep test data minimal but realistic
- Store large fixtures in separate files

### 3. Assertions
- One logical assertion per test
- Use descriptive assertion messages
- Test both positive and negative cases

### 4. Performance
- Keep unit tests under 1 second
- Use markers for slow tests
- Parallelize test execution with `pytest-xdist`

### 5. Maintenance
- Update tests when code changes
- Remove obsolete tests
- Refactor tests to reduce duplication

## Test Utilities

### Fixtures (`conftest.py`)
```python
@pytest.fixture
def sample_ohlcv_data():
    """Provide sample OHLCV data for tests."""
    return pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=5),
        'open': [100, 101, 102, 103, 104],
        'high': [105, 106, 107, 108, 109],
        'low': [99, 100, 101, 102, 103],
        'close': [104, 105, 106, 107, 108],
        'volume': [1000000, 1100000, 1200000, 1300000, 1400000]
    })

@pytest.fixture
def mock_llm():
    """Provide a mocked LLM for tests."""
    llm = Mock()
    llm.query = Mock(return_value="Test response")
    return llm
```

### Helper Functions
```python
def assert_dataframe_equal(df1, df2):
    """Assert two dataframes are equal."""
    pd.testing.assert_frame_equal(df1, df2)

def create_test_vector_store(store_type='chromadb'):
    """Create a test vector store."""
    return VectorStoreFactory.create(store_type, test_mode=True)
```

## Debugging Tests

### Run with Verbose Output
```bash
pytest -vv src/application_test.py
```

### Run with Debug Info
```bash
pytest --pdb  # Drop into debugger on failure
pytest --pdb-trace  # Drop into debugger at start
```

### Run Specific Test
```bash
pytest src/application_test.py::test_specific_function
```

### Show Test Output
```bash
pytest -s  # Don't capture stdout
pytest --capture=no  # Don't capture any output
```

## Continuous Improvement

### Metrics to Track
- Test coverage percentage
- Test execution time
- Test flakiness rate
- Time to fix failing tests

### Regular Reviews
- Monthly: Review test coverage gaps
- Quarterly: Refactor test utilities
- Bi-annually: Update testing strategy

## Migration Guide

### Adding New Tests
1. **Unit tests**: Create `*_test.py` next to source file
2. **Integration tests**: Add to `tests/integration/`
3. **E2E tests**: Add to `tests/e2e/`

### Converting Existing Tests
If migrating from a different structure:
1. Move unit tests to be co-located with source
2. Keep integration/E2E tests centralized
3. Update import paths
4. Verify all tests still pass

## Conclusion

This hybrid testing strategy provides:
- **Fast feedback** through co-located unit tests
- **Comprehensive coverage** through centralized integration tests
- **Clear organization** that scales with the project
- **Flexibility** to run specific test suites as needed

The strategy balances developer productivity with test maintainability, ensuring high code quality while keeping the development cycle efficient.