# Usage Guide

## Quick Start

```bash
# Setup with initial data
python main.py setup --tickers AAPL MSFT GOOGL

# Query the system
python main.py query "What are the recent trends in tech stocks?"

# Interactive mode
python main.py interactive
```

## Command Line Interface

### Main Commands

#### Setup Command
Initialize the system with market data:

```bash
# Basic setup with default tickers
python main.py setup

# Setup with specific tickers
python main.py setup --tickers AAPL MSFT GOOGL AMZN TSLA

# Setup with date range
python main.py setup --tickers AAPL --start-date 2023-01-01 --end-date 2024-01-01

# Setup with specific data source
python main.py setup --source alphavantage --tickers AAPL
```

#### Query Command
Query the RAG system for insights:

```bash
# Simple query
python main.py query "What is the trend for AAPL?"

# Technical analysis query
python main.py query "Show me RSI and MACD indicators for MSFT" --query-type technical

# Pattern recognition query
python main.py query "Find bullish patterns in tech stocks" --query-type pattern

# Comparison query
python main.py query "Compare AAPL and MSFT performance" --query-type comparison
```

#### Analyze Command
Perform specific analysis tasks:

```bash
# Pattern analysis
python main.py analyze pattern --pattern uptrend --tickers AAPL MSFT

# Technical indicator analysis
python main.py analyze technical --indicators RSI MACD --tickers GOOGL

# Volatility analysis
python main.py analyze volatility --tickers TSLA --period 30

# Correlation analysis
python main.py analyze correlation --tickers AAPL MSFT GOOGL
```

#### Interactive Mode
Start an interactive session:

```bash
python main.py interactive

# In interactive mode:
> help                          # Show available commands
> query: Show AAPL trends       # Execute a query
> analyze: pattern=breakout     # Run analysis
> add: TSLA                     # Add ticker to tracking
> status                        # Show system status
> exit                          # Exit interactive mode
```

#### Status Command
Check system status:

```bash
# Basic status
python main.py status

# Detailed status with statistics
python main.py status --detailed

# Vector store status
python main.py status --vector-store
```

## Docker Usage

### Basic Operations

```bash
# Start services
make up

# Run a query
make run-query QUERY="What are the trends?"

# Open shell in container
make shell

# View logs
make logs

# Stop services
make down
```

### Advanced Docker Commands

```bash
# Run with specific vector store
docker-compose -f docker-compose.yml -f docker-compose.chromadb.yml up

# Execute command in running container
docker-compose exec ohlcv-rag python main.py query "Show trends"

# Scale services
docker-compose -f docker/docker-compose.yml up --scale ohlcv-rag=3

# Run in development mode with hot-reload
make dev
```

## Python API Usage

### Basic Usage

```python
from src.application import OHLCVRAGApplication

# Initialize application
app = OHLCVRAGApplication()
app.initialize()

# Ingest data
result = app.ingest_data(
    tickers=['AAPL', 'MSFT'],
    start_date='2024-01-01',
    end_date='2024-12-31'
)

# Query the system
response = app.query(
    "What are the support and resistance levels for AAPL?",
    query_type="technical"
)
print(response)
```

### Advanced Usage

```python
from src.application import OHLCVRAGApplication
from src.config.settings import Settings

# Custom configuration
settings = Settings(
    vector_store_type="qdrant",
    llm_model="gpt-4",
    llm_temperature=0.2
)

# Initialize with custom settings
app = OHLCVRAGApplication(settings=settings)
app.initialize()

# Batch data ingestion
tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
for ticker in tickers:
    app.ingest_data(
        tickers=[ticker],
        start_date='2024-01-01',
        period='1y',
        interval='1d'
    )

# Complex analysis
analysis = app.analyze(
    analysis_type="pattern",
    tickers=['AAPL'],
    parameters={
        'pattern_type': 'breakout',
        'min_volume': 1000000,
        'price_threshold': 0.02
    }
)

# Multi-ticker comparison
comparison = app.compare_tickers(
    tickers=['AAPL', 'MSFT'],
    metrics=['returns', 'volatility', 'sharpe_ratio'],
    period='6mo'
)
```

### Streaming Data

```python
from src.application import OHLCVRAGApplication
import asyncio

async def stream_updates():
    app = OHLCVRAGApplication()
    await app.initialize_async()
    
    # Subscribe to real-time updates
    async for update in app.stream_data(['AAPL', 'MSFT']):
        print(f"Update: {update}")
        
        # Query on significant changes
        if update['change_percent'] > 2:
            response = await app.query_async(
                f"Why did {update['ticker']} move significantly?"
            )
            print(response)

# Run streaming
asyncio.run(stream_updates())
```

## Query Types and Examples

### Technical Analysis Queries

```python
# RSI and momentum
"What is the RSI for AAPL and is it overbought or oversold?"

# Moving averages
"Show me the 50-day and 200-day moving averages for MSFT"

# Support and resistance
"Identify support and resistance levels for GOOGL"

# Volume analysis
"Analyze volume patterns for TSLA over the last month"
```

### Pattern Recognition Queries

```python
# Bullish patterns
"Find bullish flag patterns in tech stocks"

# Breakout detection
"Show me stocks breaking out of consolidation"

# Trend analysis
"Identify stocks in strong uptrends with increasing volume"

# Reversal patterns
"Find potential reversal patterns in AAPL"
```

### Comparison Queries

```python
# Performance comparison
"Compare year-to-date performance of FAANG stocks"

# Volatility comparison
"Which is more volatile: TSLA or RIVN?"

# Correlation analysis
"Show correlation between AAPL and QQQ"

# Sector analysis
"Compare tech sector leaders by market cap and performance"
```

### Market Analysis Queries

```python
# Market overview
"Give me a market overview for today"

# Sector rotation
"Show sector rotation trends this quarter"

# Risk analysis
"Analyze portfolio risk for AAPL, MSFT, GOOGL"

# Economic indicators
"How are interest rates affecting tech stocks?"
```

## Configuration Options

### Data Sources

```python
# Yahoo Finance (default, free)
app.set_data_source('yahoo')

# Alpha Vantage (requires API key)
app.set_data_source('alphavantage', api_key='YOUR_KEY')

# Polygon.io (requires API key)
app.set_data_source('polygon', api_key='YOUR_KEY')

# CSV files
app.set_data_source('csv', file_path='./data/market_data.csv')
```

### Vector Stores

```python
# ChromaDB (embedded, default)
app.set_vector_store('chromadb')

# Weaviate (requires server)
app.set_vector_store('weaviate', host='localhost', port=8080)

# Qdrant (high performance)
app.set_vector_store('qdrant', host='localhost', port=6333)

# FAISS (CPU efficient)
app.set_vector_store('faiss')

# Milvus (enterprise)
app.set_vector_store('milvus', host='localhost', port=19530)
```

### LLM Configuration

```python
# Model selection
app.set_llm_model('gpt-3.5-turbo')  # Fast, cost-effective
app.set_llm_model('gpt-4')          # More capable
app.set_llm_model('gpt-4-turbo')    # Latest features

# Temperature (creativity)
app.set_llm_temperature(0.1)  # Factual, consistent
app.set_llm_temperature(0.7)  # Balanced
app.set_llm_temperature(1.0)  # Creative, varied

# Token limits
app.set_max_tokens(2000)  # Response length limit
```

## Output Formats

### JSON Output

```bash
python main.py query "AAPL trends" --output json
```

```json
{
  "query": "AAPL trends",
  "response": "Apple shows strong upward momentum...",
  "metadata": {
    "sources": ["yahoo_finance"],
    "timestamp": "2024-01-15T10:30:00Z",
    "confidence": 0.92
  }
}
```

### CSV Export

```bash
python main.py export --format csv --output results.csv
```

### Report Generation

```bash
python main.py report --ticker AAPL --type comprehensive --output report.pdf
```

## Batch Processing

### Batch Queries

```python
queries = [
    "AAPL technical analysis",
    "MSFT support levels",
    "GOOGL volume patterns"
]

results = app.batch_query(queries)
for query, result in zip(queries, results):
    print(f"{query}: {result}")
```

### Batch Analysis

```python
tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
analyses = app.batch_analyze(
    tickers=tickers,
    analysis_types=['technical', 'pattern', 'volatility']
)
```

## Error Handling

### Common Errors and Solutions

```python
try:
    response = app.query("Show AAPL trends")
except DataNotFoundError:
    print("No data available. Run setup first.")
except APIKeyError:
    print("Invalid API key. Check your .env file.")
except VectorStoreError:
    print("Vector store connection failed.")
except LLMError as e:
    print(f"LLM error: {e}")
```

## Performance Tips

1. **Use appropriate intervals**: Daily for long-term, hourly for short-term
2. **Batch operations**: Process multiple tickers together
3. **Cache results**: Enable caching for repeated queries
4. **Optimize vector store**: Use Qdrant or Milvus for large datasets
5. **Limit context**: Use date ranges to reduce data volume

## Extending Functionality

### Custom Indicators

```python
from src.indicators.base import BaseIndicator

class CustomIndicator(BaseIndicator):
    def calculate(self, data):
        # Your custom calculation
        return result

app.register_indicator('custom', CustomIndicator)
```

### Custom Data Sources

```python
from src.data_adapters.base import BaseDataAdapter

class CustomAdapter(BaseDataAdapter):
    def fetch_data(self, tickers, start_date, end_date):
        # Your data fetching logic
        return data

app.register_adapter('custom', CustomAdapter)
```

## Best Practices

1. **Regular Updates**: Ingest data daily for current analysis
2. **Query Specificity**: Be specific in queries for better results
3. **Resource Management**: Close connections when done
4. **Error Handling**: Always handle potential errors
5. **Logging**: Enable logging for debugging
6. **Testing**: Test queries in interactive mode first