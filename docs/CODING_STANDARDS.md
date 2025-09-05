# Coding Standards & Best Practices

## Core Principle: Self-Documenting Code

The codebase follows the principle of **self-documenting code** - code that clearly expresses its intent through thoughtful naming, structure, and design patterns, minimizing the need for comments.

## Naming Conventions

### Classes
✅ **Good Examples:**
- `DataSourceManager` - Clearly indicates it manages data sources
- `OHLCVDataIngestion` - Specifies exactly what data it ingests
- `YahooFinanceAdapter` - Immediately tells you the data source
- `OHLCVVectorStore` - Describes both the data type and storage method

❌ **Avoid:**
- `AdapterFactory` - "Factory" is redundant with "Adapter"
- `DataHelper` - Too vague, what does it help with?
- `Manager` - Manager of what?
- `Processor` - Processing what?

### Key Principles

1. **Names Should Tell a Story**
   ```python
   # ❌ Bad - What does this do?
   def proc_data(d):
       return transform(d)
   
   # ✅ Good - Intent is clear
   def calculate_technical_indicators(ohlcv_dataframe):
       return add_rsi_and_macd_indicators(ohlcv_dataframe)
   ```

2. **Avoid Redundancy**
   ```python
   # ❌ Bad - "Factory" doesn't add meaning
   class AdapterFactory:
       def create_adapter():
   
   # ✅ Good - Clear and concise
   class DataSourceManager:
       def create_adapter():
   ```

3. **Use Domain Language**
   ```python
   # Financial domain terms are self-explanatory
   class OHLCVData:  # Open, High, Low, Close, Volume
   def identify_support_resistance():
   def calculate_bollinger_bands():
   ```

## File & Module Organization

### Self-Documenting Structure
```
src/
├── data_adapters/          # Clearly groups all data source adapters
│   ├── base.py            # Obviously the base/abstract class
│   ├── yahoo_finance.py   # Source is in the filename
│   └── csv_adapter.py     # Purpose clear from name
├── data_ingestion.py      # Single responsibility: ingesting data
└── vector_store.py        # Single responsibility: vector storage
```

### Naming Patterns

| Pattern | Purpose | Example |
|---------|---------|---------|
| `*_adapter.py` | Data source adapters | `yahoo_finance_adapter.py` |
| `*_manager.py` | Managing/coordinating classes | `data_source_manager.py` |
| `*_store.py` | Storage/persistence | `vector_store.py` |
| `*_pipeline.py` | Multi-step processes | `rag_pipeline.py` |

## Method Naming

### Action-Oriented Names
```python
# Methods should start with verbs that describe what they do
fetch_ohlcv_data()      # Not: ohlcv_data()
calculate_rsi()         # Not: rsi()
create_embeddings()     # Not: embeddings()
validate_config()       # Not: config_check()
```

### Boolean Methods
```python
# Use is_, has_, can_, should_ prefixes
def is_valid_interval(interval: str) -> bool:
def has_required_columns(df: DataFrame) -> bool:
def can_fetch_realtime() -> bool:
```

## Design Patterns for Self-Documentation

### 1. Factory Pattern → Manager Pattern
Instead of generic "Factory" suffix, use descriptive names:
- `DataSourceManager` - Manages data sources
- `AdapterRegistry` - Registry of adapters
- `ConfigurationBuilder` - Builds configurations

### 2. Adapter Pattern
Adapter names should include the source:
- `YahooFinanceAdapter`
- `AlphaVantageAdapter`
- Not just: `YahooAdapter` (adapter for what?)

### 3. Type Hints as Documentation
```python
def fetch_ohlcv(
    self,
    ticker: str,
    period: str = "1y",
    interval: str = "1d"
) -> OHLCVData:  # Return type tells you exactly what you get
    """Fetch OHLCV data for a single ticker"""
```

## Configuration & Constants

### Self-Explanatory Variable Names
```python
# ❌ Bad
DELAY = 12

# ✅ Good  
ALPHA_VANTAGE_RATE_LIMIT_SECONDS = 12
DEFAULT_CHUNK_WINDOW_SIZE = 30
MAX_EMBEDDING_BATCH_SIZE = 100
```

### Environment Variables
```bash
# Clear, prefixed, purposeful
DATA_SOURCE=yahoo              # Not: SOURCE=yahoo
OPENAI_API_KEY=xxx            # Not: API_KEY=xxx
CSV_DATA_DIR=./data/csv       # Not: DATA_DIR=./data/csv
```

## Error Messages

### Descriptive Errors
```python
# ❌ Bad
raise ValueError("Invalid input")

# ✅ Good
raise ValueError(
    f"Interval '{interval}' not supported. "
    f"Valid intervals: {', '.join(VALID_INTERVALS)}"
)
```

## Documentation Strategy

### When Comments ARE Needed
1. **Complex algorithms** - Explain the "why", not the "what"
2. **External API quirks** - Document workarounds
3. **Performance optimizations** - Explain trade-offs

### When Comments AREN'T Needed
```python
# ❌ Unnecessary comment - code is self-documenting
# Fetch data from Yahoo Finance
data = yahoo_adapter.fetch_ohlcv_data(ticker="AAPL")

# ✅ Code speaks for itself
data = yahoo_adapter.fetch_ohlcv_data(ticker="AAPL")
```

## Testing for Self-Documentation

### Test Method Names as Specifications
```python
def test_fetch_ohlcv_returns_dataframe_with_required_columns():
def test_invalid_ticker_raises_runtime_error():
def test_rate_limit_delays_between_requests():
```

## Benefits of Self-Documenting Code

1. **Reduces cognitive load** - Understand at a glance
2. **Fewer bugs** - Clear intent reduces misunderstandings  
3. **Easier onboarding** - New developers understand quickly
4. **Less maintenance** - No outdated comments to update
5. **Better collaboration** - Team members grasp intent immediately

## Checklist for Self-Documenting Code

Before committing, ask yourself:
- [ ] Would a new developer understand this without comments?
- [ ] Do variable/function names clearly express intent?
- [ ] Is there any redundancy in naming?
- [ ] Are domain terms used consistently?
- [ ] Do type hints clarify expected inputs/outputs?
- [ ] Are error messages helpful and specific?
- [ ] Is the file/folder structure logical and predictable?

## Example: Refactoring for Self-Documentation

### Before:
```python
class DF:
    def __init__(self, src, cfg=None):
        self.s = src
        self.c = cfg or {}
    
    def get(self, t):
        # Get data
        d = self._fetch(t)
        return self._proc(d)
```

### After:
```python
class DataSourceManager:
    def __init__(
        self, 
        source_name: str, 
        config: Optional[Dict[str, Any]] = None
    ):
        self.source_name = source_name
        self.config = config or {}
    
    def fetch_ohlcv_data(self, ticker: str) -> OHLCVData:
        raw_data = self._fetch_from_source(ticker)
        return self._standardize_to_ohlcv(raw_data)
```

---

*Remember: Code is read far more often than it's written. Invest time in making it self-documenting.*