# Test Suite Documentation

## Clear, Specific Test Files

### External Services
- **`test_yahoo_finance.py`** - Tests Yahoo Finance API data fetching
- **`test_chromadb.py`** - Tests ChromaDB vector database operations

### Core Classes
- **`test_base_component.py`** - Tests BaseComponent abstract class
- **`test_data_processor.py`** - Tests DataProcessor abstract class
- **`test_exceptions.py`** - Tests custom exception classes

### Application Components
- **`test_ohlcv_rag_application.py`** - Tests OHLCVRAGApplication class methods
- **`test_application_state_tracking.py`** - Tests ApplicationState query/error tracking
- **`test_main_functionality.py`** - Tests main.py CLI script

### Data Processing
- **`test_technical_indicators.py`** - Tests technical indicator calculations (RSI, SMA, Bollinger Bands)

## Each File Tests ONE Thing

No more vague names:
- ❌ ~~test_core_base_classes~~ → ✅ Split into: test_base_component.py, test_data_processor.py, test_exceptions.py
- ❌ ~~test_application_state~~ → ✅ Renamed: test_application_state_tracking.py
- ❌ ~~test_imports_and_initialization~~ → ✅ Deleted (too vague)
- ❌ ~~test_external_integrations~~ → ✅ Split into: test_yahoo_finance.py, test_chromadb.py

## Test Philosophy

1. **One file, one purpose** - Each test file tests exactly one class or service
2. **Clear naming** - File name tells you exactly what's being tested
3. **Real implementations** - Tests use actual services, minimal mocking
4. **No mixed concerns** - Don't mix unrelated tests in one file

## Running Tests

```bash
# Run all tests
uv run pytest tests/

# Run specific component tests
uv run pytest tests/test_yahoo_finance.py          # Test Yahoo Finance API
uv run pytest tests/test_chromadb.py               # Test ChromaDB
uv run pytest tests/test_base_component.py         # Test BaseComponent class
uv run pytest tests/test_exceptions.py             # Test exception classes

# Run with coverage
uv run pytest tests/ --cov=src --cov-report=term-missing
```

## Integration Tests (in `integration/` directory)

Separate directory for tests requiring Docker containers:
- `test_chromadb_integration.py`
- `test_weaviate_integration.py`
- `test_qdrant_integration.py`
- `test_end_to_end.py`

## Writing New Tests

Use clear, specific names:

✅ **GOOD:**
- `test_redis_cache.py` - Tests Redis caching
- `test_openai_api.py` - Tests OpenAI API
- `test_user_authentication.py` - Tests user auth

❌ **BAD:**
- `test_utils.py` - What utils?
- `test_helpers.py` - Which helpers?
- `test_integration.py` - Integration of what?
- `test_core.py` - What core component?

## Test Organization Example

If you have related classes, create separate files:
```
tests/
  test_base_component.py      # Tests BaseComponent class
  test_data_processor.py       # Tests DataProcessor class
  test_configurable.py         # Tests Configurable interface
```

NOT:
```
tests/
  test_core_classes.py        # Too vague - what classes?
```