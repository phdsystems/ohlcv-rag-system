# Testing Strategy for OHLCV RAG System

## Overview

This document outlines the comprehensive testing strategy for the OHLCV RAG System, designed to support both rapid development with mock tests and thorough CI/CD validation with real dependencies.

## Test Categories

### 1. Mock Tests (Development)
- **Purpose**: Fast feedback during development
- **Location**: `tests/test_mock_suite.py`, `tests/test_simple.py`
- **Dependencies**: None (pure mocking)
- **Run time**: < 5 seconds
- **Command**: `make test-mock` or `./scripts/test-profiles.sh dev-mock`

### 2. Unit Tests
- **Purpose**: Test individual components in isolation
- **Location**: `tests/test_*.py` (excluding integration/)
- **Dependencies**: Minimal, mostly mocked
- **Run time**: < 30 seconds
- **Command**: `make test` or `pytest -m unit`

### 3. Integration Tests (Docker)
- **Purpose**: Test with real vector stores and services
- **Location**: `tests/integration/`
- **Dependencies**: Docker containers (ChromaDB, Weaviate, Qdrant)
- **Run time**: 2-5 minutes
- **Command**: `make test-integration` or `./scripts/test-profiles.sh integration-local`

### 4. Integration Tests (Real Services)
- **Purpose**: Test with actual external APIs
- **Location**: `tests/integration/test_real_dependencies.py`
- **Dependencies**: API keys, internet connection
- **Run time**: 1-3 minutes
- **Command**: `./scripts/test-profiles.sh integration-real`

## Test Profiles

### Development Profiles

#### `dev-mock`
- Pure mock tests, no external dependencies
- Ideal for TDD and rapid iteration
- Run: `./scripts/test-profiles.sh dev-mock`

#### `dev-quick`
- Subset of fastest unit tests
- < 2 seconds execution time
- Run: `./scripts/test-profiles.sh dev-quick`

#### `pre-commit`
- Fast tests to run before committing
- Fails fast on first error
- Run: `./scripts/test-profiles.sh pre-commit`

### CI/CD Profiles

#### `ci-unit`
- Comprehensive unit tests with coverage
- No external dependencies
- Generates coverage reports
- Run: `./scripts/test-profiles.sh ci-unit`

#### `ci-integration`
- Integration tests with Docker containers
- Tests all vector stores
- Generates coverage reports
- Run: `./scripts/test-profiles.sh ci-integration`

#### `ci-full`
- Complete test suite (unit + integration)
- Combined coverage reporting
- Run: `./scripts/test-profiles.sh ci-full`

### Special Profiles

#### `smoke`
- Minimal set of critical tests
- Verifies basic functionality
- Run: `./scripts/test-profiles.sh smoke`

#### `performance`
- Benchmark and stress tests
- Measures performance metrics
- Run: `./scripts/test-profiles.sh performance`

#### `specific-service`
- Test specific vector store
- Example: `./scripts/test-profiles.sh specific-service chromadb`

## Test Markers

Tests are organized with pytest markers for flexible execution:

```python
@pytest.mark.unit          # Unit tests
@pytest.mark.mock          # Mock-only tests
@pytest.mark.integration   # Integration tests
@pytest.mark.real_deps     # Tests with real dependencies
@pytest.mark.docker        # Tests requiring Docker
@pytest.mark.slow          # Tests > 5 seconds
@pytest.mark.requires_api_key  # Tests needing API keys
```

## Running Tests

### Quick Start (Development)

```bash
# Run mock tests (fastest)
make test-mock

# Run quick development tests
make test-dev

# Run specific test file
pytest tests/test_mock_suite.py -v

# Run with debugging
pytest tests/test_simple.py --pdb
```

### Integration Testing

```bash
# Start required services
docker-compose -f docker/docker-compose.yml up -d chromadb qdrant weaviate

# Run integration tests
make test-integration

# Run specific service tests
pytest -m chromadb
```

### CI/CD Testing

```bash
# Run full CI suite locally
make test-ci

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific profile
PROFILE=ci-unit make test-profile
```

## Coverage Requirements

- **Unit Tests**: Minimum 80% coverage
- **Integration Tests**: Focus on critical paths
- **Combined**: Target 85% overall coverage

## Environment Variables

### Required for Real Integration Tests

```bash
# API Keys
export OPENAI_API_KEY="your-key"
export ALPHA_VANTAGE_API_KEY="your-key"
export POLYGON_API_KEY="your-key"

# Enable real API tests
export ENABLE_REAL_API_TESTS=true
```

### Docker Service Configuration

```bash
# Vector store hosts (defaults to localhost)
export CHROMADB_HOST=localhost
export CHROMADB_PORT=8000
export QDRANT_HOST=localhost
export QDRANT_PORT=6333
export WEAVIATE_HOST=localhost
export WEAVIATE_PORT=8080
```

## GitHub Actions Workflow

The CI/CD pipeline runs automatically on:
- Push to main/develop branches
- Pull requests
- Nightly schedule (2 AM UTC)
- Manual trigger with profile selection

### Pipeline Stages

1. **Validate**: Linting, type checking, formatting
2. **Unit Tests**: Run on multiple Python versions
3. **Integration Tests**: Run with Docker services
4. **Performance Tests**: Run nightly or on-demand
5. **Build Docker**: Create and push images
6. **Deploy**: Deploy to production (main branch only)

## Best Practices

### For Development

1. **Start with mocks**: Write mock tests first for new features
2. **Run pre-commit tests**: `./scripts/test-profiles.sh pre-commit`
3. **Use TDD**: Write tests before implementation
4. **Keep tests fast**: Mock external dependencies

### For CI/CD

1. **Parallel execution**: Tests run in parallel where possible
2. **Fail fast**: Critical tests run first
3. **Cache dependencies**: Speed up pipeline execution
4. **Generate artifacts**: Save test results and coverage

### Test Writing Guidelines

1. **Isolation**: Each test should be independent
2. **Clarity**: Clear test names and assertions
3. **Coverage**: Test both success and failure paths
4. **Performance**: Mark slow tests appropriately
5. **Documentation**: Add docstrings to complex tests

## Troubleshooting

### Common Issues

#### Docker services not starting
```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs chromadb

# Restart services
docker-compose restart
```

#### API key errors
```bash
# Verify keys are set
env | grep API_KEY

# Skip API tests
pytest -m "not requires_api_key"
```

#### Coverage not generating
```bash
# Install coverage tools
uv sync --dev

# Generate HTML report
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

## Maintenance

### Adding New Tests

1. Choose appropriate location:
   - Unit tests: `tests/test_*.py`
   - Integration: `tests/integration/test_*.py`
   - Mocks: `tests/test_mock_suite.py`

2. Add appropriate markers:
   ```python
   @pytest.mark.unit
   @pytest.mark.mock
   def test_new_feature():
       pass
   ```

3. Update test profiles if needed in `scripts/test-profiles.sh`

### Updating Dependencies

```bash
# Update test dependencies
uv add --dev pytest@latest pytest-cov@latest

# Update integration test deps
uv add --group test testcontainers@latest

# Sync and test
uv sync --dev
make test-all
```

## Performance Metrics

Target performance for test execution:
- Mock tests: < 5 seconds
- Unit tests: < 30 seconds
- Integration tests: < 5 minutes
- Full CI pipeline: < 15 minutes

## Conclusion

This testing strategy provides:
- **Fast feedback** during development with mock tests
- **Comprehensive validation** for production deployments
- **Flexible profiles** for different scenarios
- **Clear separation** between test types
- **Efficient CI/CD** pipeline execution

Choose the appropriate test profile based on your current needs:
- Development: `dev-mock` or `dev-quick`
- Pre-commit: `pre-commit`
- CI/CD: `ci-full`
- Production validation: `integration-real`