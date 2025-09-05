# OHLCV RAG System

A Retrieval-Augmented Generation (RAG) system for analyzing OHLCV (Open, High, Low, Close, Volume) financial market data. This system combines vector similarity search with LLM capabilities to answer complex queries about market patterns, trends, and technical indicators.

## Features

- **Data Ingestion**: Automatically fetches OHLCV data from Yahoo Finance
- **Technical Indicators**: Calculates RSI, MACD, Moving Averages, Bollinger Bands, and more
- **Pattern Recognition**: Identifies trends, support/resistance levels, and market patterns
- **Vector Search**: Embeddings-based retrieval for finding relevant market conditions
- **RAG Pipeline**: Combines retrieval with LLM for intelligent market analysis
- **Interactive Query Interface**: Command-line interface for exploring the data

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Yahoo      │────▶│   Data       │────▶│   Vector     │
│   Finance    │     │   Ingestion  │     │   Store      │
└──────────────┘     └──────────────┘     └──────────────┘
                            │                     │
                            ▼                     ▼
                     ┌──────────────┐     ┌──────────────┐
                     │  Technical   │     │  Retriever   │
                     │  Indicators  │     └──────────────┘
                     └──────────────┘            │
                                                 ▼
                                          ┌──────────────┐
                                          │     RAG      │
                                          │   Pipeline   │
                                          └──────────────┘
                                                 │
                                                 ▼
                                          ┌──────────────┐
                                          │   LLM        │
                                          │  (OpenAI)    │
                                          └──────────────┘
```

### RAG Pipeline

The system uses a sophisticated RAG (Retrieval-Augmented Generation) pipeline that combines vector search with LLM analysis. 

**How it works:**
1. **Retrieval**: Finds relevant OHLCV data chunks using semantic search
2. **Augmentation**: Enriches the query with retrieved market data and indicators
3. **Generation**: LLM analyzes the context to provide data-driven insights

📚 **[Comprehensive RAG Pipeline Documentation](./docs/RAG_PIPELINE.md)**  
🎨 **[Visual Guide to RAG Pipeline](./docs/RAG_PIPELINE_VISUAL.md)**

## Installation

1. Clone the repository:
```bash
cd ohlcv-rag-system
```

2. Install uv (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# or on macOS/Linux with Homebrew:
brew install uv
```

3. Install dependencies with uv:
```bash
# Simple one-command setup (uv handles venv automatically)
uv sync

# For development with additional tools
uv sync --dev
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

## Configuration

Edit the `.env` file to configure:

- `OPENAI_API_KEY`: Your OpenAI API key (required for LLM features)
- `TICKER_SYMBOLS`: Comma-separated list of stock tickers (default: AAPL,MSFT,GOOGL,AMZN)
- `DATA_PERIOD`: Time period for data (default: 1y)
- `DATA_INTERVAL`: Data interval (default: 1d)

## Usage

### Quick Start

Using uv directly:
```bash
uv run python main.py
```

Or use the Makefile:
```bash
make run
```

Or use the shell script:
```bash
./run.sh
```

This will:
1. Fetch OHLCV data for configured tickers
2. Calculate technical indicators
3. Create embeddings and index in vector store
4. Launch interactive query interface

### Interactive Commands

Once in interactive mode, you can use:

- `query <question>` - Ask any question about the market data
- `pattern <type>` - Analyze specific patterns (uptrend/downtrend/breakout/reversal)
- `indicator <name> <condition> <value>` - Search by technical indicator
- `similar <ticker> <date>` - Find similar historical patterns
- `stats` - Show vector store statistics
- `exit` - Exit the program

### Example Queries

```
> query What are the recent trends in tech stocks?

> pattern breakout

> indicator RSI > 70

> similar AAPL 2024-01-15
```

## System Components

### 1. Data Ingestion (`src/data_ingestion.py`)
- **Pluggable adapter system** for multiple data sources
- Supported data sources:
  - **Yahoo Finance**: Free, no API key required
  - **Alpha Vantage**: Free/paid tiers, API key required
  - **Polygon.io**: Real-time data, API key required
  - **CSV Files**: Local data import/export
- Calculates technical indicators (SMA, EMA, RSI, MACD, Bollinger Bands)
- Identifies trends and support/resistance levels
- Creates contextual chunks with 30-day windows

### 2. Vector Store (`src/vector_store.py`)
- Uses ChromaDB for persistent vector storage
- Embeddings via sentence-transformers (all-MiniLM-L6-v2)
- Supports filtered search by ticker, date range, and metadata

### 3. Retriever (`src/retriever.py`)
- Semantic search for relevant market conditions
- Pattern-based retrieval (trends, breakouts, reversals)
- Technical indicator filtering
- Similar pattern matching

### 4. RAG Pipeline (`src/rag_pipeline.py`)
- Integrates with OpenAI LLM (GPT-3.5/GPT-4)
- Multiple prompt templates for different query types
- Combines retrieved context with LLM reasoning
- Provides detailed market analysis

## Technical Indicators

The system calculates and tracks:
- **Moving Averages**: SMA (20, 50), EMA (12, 26)
- **Momentum**: RSI (14-period)
- **Trend**: MACD with signal line
- **Volatility**: Bollinger Bands
- **Volume**: Volume-weighted average price
- **Price Changes**: 1-day, 5-day, 20-day returns

## Data Structure

Each chunk contains:
- Raw OHLCV data points
- Calculated technical indicators
- Trend identification (Uptrend/Downtrend/Sideways)
- Support/Resistance levels
- Statistical summaries
- Metadata for filtering

## Documentation

- 📚 **[RAG Pipeline Deep Dive](docs/RAG_PIPELINE.md)** - Complete technical documentation of the RAG system
- 🎨 **[RAG Pipeline Visual Guide](docs/RAG_PIPELINE_VISUAL.md)** - Visual explanations and diagrams
- 🔌 **[Data Adapters Guide](docs/DATA_ADAPTERS.md)** - How to add custom data sources
- 🗄️ **[Vector Stores Guide](docs/VECTOR_STORES.md)** - Supported vector databases
- 📝 **[Coding Standards](docs/CODING_STANDARDS.md)** - Self-documenting code principles

## Development Philosophy

This project follows **self-documenting code** principles and **Object-Oriented Programming (OOP)** architecture. The codebase is designed for clarity, maintainability, and extensibility.

## Extending the System

### Adding New Indicators
Edit `src/data_ingestion.py` and add calculations in `_add_technical_indicators()`

### Custom Patterns
Modify `src/retriever.py` to add new pattern recognition logic

### Different Embeddings
Change the model in `src/vector_store.py` (default: all-MiniLM-L6-v2)

### Alternative LLMs
Update `src/rag_pipeline.py` to use different LLM providers

### Adding Data Sources
See [DATA_ADAPTERS.md](docs/DATA_ADAPTERS.md) for creating custom adapters

## Requirements

- Python 3.8+
- uv package manager
- OpenAI API key (for LLM features)
- Internet connection (for data fetching)
- ~500MB disk space for vector store

## Limitations

- Historical data only (no real-time streaming)
- Limited to daily intervals by default
- Requires OpenAI API for full RAG capabilities
- Technical analysis only (no fundamental data)

## License

MIT License

## Disclaimer

This system is for educational and research purposes only. It provides technical analysis based on historical data and should not be used as the sole basis for investment decisions. Always consult with qualified financial advisors and conduct your own research before making investment decisions.