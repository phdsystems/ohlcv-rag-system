# Data Source Adapters Documentation

The OHLCV RAG System supports multiple data sources through a pluggable adapter system. You can easily switch between different providers or add your own custom adapters.

## Available Adapters

### 1. Yahoo Finance (`yahoo`)

**Default adapter** - No API key required

```python
# In .env
DATA_SOURCE=yahoo
```

**Features:**
- Free, no registration needed
- Extensive historical data
- Global markets (stocks, ETFs, crypto, forex)
- 15-20 minute delay for real-time data

**Supported Intervals:** 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo

### 2. Alpha Vantage (`alpha_vantage`)

**Requires API key** - Get free key at https://www.alphavantage.co/support/#api-key

```python
# In .env
DATA_SOURCE=alpha_vantage
ALPHA_VANTAGE_API_KEY=your_api_key_here
```

**Features:**
- Free tier: 5 calls/min, 500 calls/day
- Premium tiers available
- 20+ years historical data
- Technical indicators API

**Rate Limits:**
- Free: 5 API calls per minute
- Premium: 75-1200 calls per minute

### 3. Polygon.io (`polygon`)

**Requires API key** - Get key at https://polygon.io

```python
# In .env
DATA_SOURCE=polygon
POLYGON_API_KEY=your_api_key_here
```

**Features:**
- Real-time data (all tiers)
- WebSocket streaming
- Options and forex data
- News and sentiment analysis

**Rate Limits:**
- Free: 5 calls per minute
- Paid: Unlimited

### 4. CSV Files (`csv`)

**For local data** - No API needed

```python
# In .env
DATA_SOURCE=csv
CSV_DATA_DIR=./data/csv
```

**Features:**
- Load historical data from CSV files
- Offline operation
- Custom data sources
- Data export/import

**File Format:**
```csv
Date,Open,High,Low,Close,Volume
2024-01-01,150.00,155.00,149.00,154.00,1000000
2024-01-02,154.00,156.00,153.00,155.50,1100000
```

## Usage Examples

### Basic Usage

```python
from src.data_ingestion import OHLCVDataIngestion

# Using default Yahoo Finance
ingestion = OHLCVDataIngestion(
    tickers=["AAPL", "MSFT"],
    source="yahoo",
    period="1y",
    interval="1d"
)

data = ingestion.fetch_ohlcv_data()
```

### With API Key Configuration

```python
# Alpha Vantage
ingestion = OHLCVDataIngestion(
    tickers=["AAPL"],
    source="alpha_vantage",
    adapter_config={"api_key": "your_key"}
)

# Polygon.io
ingestion = OHLCVDataIngestion(
    tickers=["AAPL"],
    source="polygon",
    adapter_config={"api_key": "your_key"}
)
```

### Loading from CSV

```python
# Ensure CSV files exist in ./data/csv/
# Files should be named: TICKER.csv (e.g., AAPL.csv)

ingestion = OHLCVDataIngestion(
    tickers=["AAPL", "MSFT"],
    source="csv",
    adapter_config={"data_dir": "./data/csv"}
)
```

### Switching Adapters at Runtime

```python
# Start with Yahoo
ingestion = OHLCVDataIngestion(
    tickers=["AAPL"],
    source="yahoo"
)

# Switch to Polygon
ingestion.switch_adapter(
    source="polygon",
    adapter_config={"api_key": "your_key"}
)
```

## Creating Custom Adapters

To create your own data adapter:

1. Inherit from `DataSourceAdapter` base class
2. Implement required methods
3. Register in `DataSourceManager`

```python
from src.data_adapters.base import DataSourceAdapter, OHLCVData
from src.data_adapters import DataSourceManager

class CustomAdapter(DataSourceAdapter):
    def _validate_config(self):
        # Validate configuration
        pass
    
    def fetch_ohlcv(self, ticker, period="1y", interval="1d", 
                   start_date=None, end_date=None):
        # Fetch data from your source
        df = your_data_fetching_logic()
        return OHLCVData(ticker=ticker, data=df, metadata={})
    
    def fetch_multiple(self, tickers, **kwargs):
        # Fetch multiple tickers
        results = {}
        for ticker in tickers:
            results[ticker] = self.fetch_ohlcv(ticker, **kwargs)
        return results
    
    def get_available_tickers(self):
        # Return list of available tickers
        return ["AAPL", "MSFT", ...]
    
    def get_adapter_info(self):
        # Return adapter information
        return {
            "name": "Custom Adapter",
            "requires_api_key": False,
            ...
        }

# Register the adapter
DataSourceManager.ADAPTERS['custom'] = CustomAdapter
```

## Adapter Selection Guide

| Adapter | Best For | API Key | Cost | Real-time |
|---------|----------|---------|------|-----------|
| Yahoo Finance | Development, Research | No | Free | 15-20min delay |
| Alpha Vantage | Historical analysis | Yes | Free/Paid | Paid only |
| Polygon.io | Production, Real-time | Yes | Free/Paid | Yes |
| CSV | Backtesting, Offline | No | Free | No |

## Environment Variables

```bash
# Choose data source
DATA_SOURCE=yahoo  # or alpha_vantage, polygon, csv

# API Keys (if needed)
ALPHA_VANTAGE_API_KEY=your_key
POLYGON_API_KEY=your_key

# CSV configuration
CSV_DATA_DIR=./data/csv

# Common settings
TICKER_SYMBOLS=AAPL,MSFT,GOOGL
DATA_PERIOD=1y
DATA_INTERVAL=1d
```

## Troubleshooting

### Yahoo Finance
- No issues typically, works out of the box
- If blocked, try using a VPN

### Alpha Vantage
- Check API key is valid
- Respect rate limits (12s between calls for free tier)
- Verify ticker symbols are US stocks

### Polygon.io
- Ensure API key has correct permissions
- Check if ticker is available in your subscription

### CSV Files
- Verify file exists in data directory
- Check column names match expected format
- Ensure Date column is properly formatted

## Data Format

All adapters return standardized OHLCV data:

```python
OHLCVData:
  ticker: str
  data: pd.DataFrame  # Columns: Open, High, Low, Close, Volume
  metadata: dict      # Source-specific metadata
```

The DataFrame index is always a DateTimeIndex for consistency across all adapters.