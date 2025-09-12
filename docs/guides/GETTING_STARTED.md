# Getting Started Guide

Welcome to the OHLCV RAG System! This guide will walk you through setting up and using the system for financial data analysis with AI.

## Prerequisites

Before you begin, ensure you have:

- **Python 3.11+** installed
- **Docker** (optional, but recommended)
- **OpenAI API key** for LLM features
- **Internet connection** for data fetching
- **~1GB free disk space**

## Installation Options

### Option 1: Docker (Recommended) 🐳

Docker provides the easiest setup with all dependencies pre-configured.

```bash
# 1. Clone the repository
git clone https://github.com/phdsystems/ohlcv-rag-system.git
cd ohlcv-rag-system

# 2. Copy and configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 3. Build and start the system
make build
make up
make run
```

That's it! The system is ready to use.

### Option 2: Local Installation 💻

For development or customization:

```bash
# 1. Clone the repository
git clone https://github.com/phdsystems/ohlcv-rag-system.git
cd ohlcv-rag-system

# 2. Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Install dependencies
uv sync

# 4. Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 5. Run the application
python main.py interactive
```

## Configuration

### Essential Settings

Edit your `.env` file:

```bash
# Required for LLM features
OPENAI_API_KEY=sk-your-api-key-here

# Optional: Customize data sources
DATA_SOURCE=yahoo  # Options: yahoo, alpha_vantage, polygon, csv
TICKER_SYMBOLS=AAPL,MSFT,GOOGL,AMZN
DATA_PERIOD=1y  # 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
DATA_INTERVAL=1d  # 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo

# Optional: Choose vector store
VECTOR_STORE_TYPE=chromadb  # chromadb, weaviate, qdrant, faiss, milvus
```

### API Keys for Additional Data Sources

If using alternative data sources:

```bash
# Alpha Vantage (free tier available)
ALPHA_VANTAGE_API_KEY=your-key

# Polygon.io (free tier available)
POLYGON_API_KEY=your-key
```

## Your First Analysis

### Step 1: Load Data

```bash
# Using CLI
python main.py setup --tickers AAPL MSFT GOOGL

# Or with Docker
docker run -it --rm -v $(pwd)/data:/data ohlcv-rag:main \
  setup --tickers AAPL MSFT GOOGL
```

Expected output:
```
Initializing OHLCV RAG Application...
✓ Application initialized successfully

Configuration:
- Data Source: yahoo
- Tickers: AAPL, MSFT, GOOGL
- Period: 1y
- Interval: 1d

Ingesting data...
✓ Data ingestion complete!
  - Chunks created: 90
  - Documents indexed: 90
```

### Step 2: Ask Questions

```bash
# Interactive mode
python main.py interactive

> query What are the recent trends in AAPL?
```

Example response:
```
Based on the OHLCV data for AAPL:

1. **Current Trend**: AAPL shows a strong uptrend over the past month
2. **Price Movement**: +8.3% gain from $180 to $195
3. **Technical Indicators**:
   - RSI at 65.4 (bullish but not overbought)
   - MACD showing positive momentum
   - Price above 20-day and 50-day moving averages
4. **Volume**: Average volume of 75M shares indicates healthy interest
5. **Key Levels**: 
   - Support at $185
   - Resistance at $200

[Based on 5 data chunks, 89% confidence]
```

### Step 3: Analyze Patterns

```bash
> pattern breakout

Analyzing breakout patterns...

Found 3 potential breakouts:
1. AAPL - Feb 15: Clear break above $195 resistance with volume surge
2. MSFT - Feb 20: Breaking out from consolidation range
3. GOOGL - Feb 18: Testing breakout above $150

Recommendation: Watch for volume confirmation on breakouts
```

## Common Use Cases

### 1. Technical Analysis

```python
# Find overbought stocks
python main.py query "Which stocks have RSI above 70?"

# Identify support/resistance
python main.py query "What are the key support levels for MSFT?"

# Analyze volatility
python main.py query "Compare volatility between tech stocks"
```

### 2. Pattern Recognition

```python
# Find specific patterns
python main.py analyze pattern --pattern uptrend --tickers AAPL

# Identify reversals
python main.py analyze pattern --pattern reversal

# Detect breakouts
python main.py analyze pattern --pattern breakout
```

### 3. Comparative Analysis

```python
# Compare multiple stocks
python main.py query "Compare performance of AAPL vs MSFT"

# Sector analysis
python main.py query "How are tech stocks performing overall?"

# Correlation analysis
python main.py query "Which stocks move together?"
```

## Interactive Commands

In interactive mode, you have access to these commands:

| Command | Description | Example |
|---------|-------------|---------|
| `query <question>` | Ask any question | `query What's the trend?` |
| `pattern <type>` | Find patterns | `pattern uptrend` |
| `indicator <name> <op> <value>` | Search by indicator | `indicator RSI > 70` |
| `status` | Show system status | `status` |
| `help` | Show help | `help` |
| `exit` | Exit interactive mode | `exit` |

## Understanding the Output

### Query Response Structure

```
Answer: [The actual analysis]
Sources: [Number of data chunks used]
Confidence: [0-100% confidence score]
Processing time: [Time taken]
```

### Confidence Levels

- **90-100%**: Very high confidence, multiple confirming sources
- **70-89%**: High confidence, good data coverage
- **50-69%**: Moderate confidence, limited data
- **Below 50%**: Low confidence, use with caution

## Advanced Usage

### Using Different Vector Stores

```bash
# Start with Weaviate (more features)
VECTOR_STORE_TYPE=weaviate python main.py setup

# Or with Docker
docker-compose --profile weaviate up -d
```

### Custom Data Sources

```bash
# Use Alpha Vantage for more detailed data
DATA_SOURCE=alpha_vantage python main.py setup

# Load from CSV files
DATA_SOURCE=csv CSV_DATA_DIR=./mydata python main.py setup
```

### Batch Processing

```python
from src.application import OHLCVRAGApplication

app = OHLCVRAGApplication()
app.initialize()

# Process multiple tickers
tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']
for ticker in tickers:
    result = app.query(f"Analyze {ticker}", context={'ticker': ticker})
    print(f"{ticker}: {result['answer'][:100]}...")
```

## Troubleshooting

### Issue: "No OpenAI API key found"

**Solution**: Add your API key to `.env`:
```bash
OPENAI_API_KEY=sk-your-actual-api-key
```

### Issue: "No data fetched"

**Solutions**:
1. Check internet connection
2. Verify ticker symbols are correct
3. Try a different data source
4. Check if market is open (for intraday data)

### Issue: "Docker build fails"

**Solutions**:
1. Ensure Docker is running
2. Enable BuildKit: `export DOCKER_BUILDKIT=1`
3. Clear cache: `docker system prune -af`
4. Build without cache: `make build-nocache`

### Issue: "Low confidence results"

**Solutions**:
1. Ingest more data: `python main.py setup --period 2y`
2. Be more specific in queries
3. Use exact ticker symbols
4. Check if data exists for the time period

## Best Practices

### 1. Data Management

- **Regular Updates**: Refresh data daily for accuracy
- **Historical Depth**: Use at least 1 year of data
- **Multiple Tickers**: Compare related stocks

### 2. Query Formulation

**Good Queries:**
- "What is the trend for AAPL in the last month?"
- "Show me stocks with RSI below 30"
- "Compare volatility between MSFT and GOOGL"

**Poor Queries:**
- "stocks" (too vague)
- "predict price tomorrow" (beyond capability)
- "AAPL" (no specific question)

### 3. Interpretation

- Always check the confidence score
- Verify with multiple indicators
- Consider the data timeframe
- This is analysis, not financial advice

## Next Steps

Now that you're up and running:

1. **Explore Documentation**:
   - [RAG Pipeline Details](RAG_PIPELINE.md)
   - [Architecture Overview](ARCHITECTURE.md)
   - [API Reference](API_REFERENCE.md)

2. **Customize the System**:
   - Add custom indicators
   - Create new data adapters
   - Implement trading strategies

3. **Scale Up**:
   - Process more tickers
   - Use production vector stores
   - Deploy with Kubernetes

## Getting Help

### Resources

- **Documentation**: Full docs in `/docs` folder
- **Examples**: See `/examples` for code samples
- **Issues**: [GitHub Issues](https://github.com/phdsystems/ohlcv-rag-system/issues)

### Common Commands Reference

```bash
# Quick setup
make quick-start

# View logs
make logs

# Open shell in container
make shell

# Run tests
make test

# Clean everything
make clean-all
```

## FAQ

**Q: Can I use this without OpenAI?**
A: Yes, retrieval features work without OpenAI. Only the generation part requires it.

**Q: How much data can it handle?**
A: Tested with up to 100 tickers with 10 years of daily data.

**Q: Is real-time data supported?**
A: Currently historical only. Real-time is on the roadmap.

**Q: Can I add custom indicators?**
A: Yes! See the [Architecture docs](ARCHITECTURE.md) for how to extend.

**Q: Is this financial advice?**
A: No, this is a technical analysis tool for educational purposes.

---

Ready to analyze markets with AI? Start with `python main.py interactive` and explore! 🚀