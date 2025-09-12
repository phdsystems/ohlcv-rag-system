# OHLCV RAG System

A production-ready Retrieval-Augmented Generation (RAG) system for analyzing OHLCV (Open, High, Low, Close, Volume) financial market data.

## Features

- **Multi-Source Data Ingestion**: Yahoo Finance, Alpha Vantage, Polygon.io, CSV
- **Technical Analysis**: 15+ indicators including RSI, MACD, Bollinger Bands
- **Advanced RAG Pipeline**: Semantic search with LLM-powered analysis
- **Multiple Vector Stores**: ChromaDB, Weaviate, Qdrant, FAISS, Milvus
- **Docker Support**: Full containerization with optimized builds
- **OOP Architecture**: Clean, maintainable, extensible codebase

## Quick Start

```bash
# Clone repository
git clone https://github.com/phdsystems/ohlcv-rag-system.git
cd ohlcv-rag-system

# Install with uv (recommended)
uv pip install -e .
uv pip install -e ".[integration]"  # Optional: for testcontainers
uv pip install -e ".[vector-stores]"  # Optional: for additional vector stores

# Setup environment (optional - mock LLM provider available)
cp .env.example .env
# Add your API keys to .env (or use llm_provider="mock")

# Run locally
python main.py

# Or run with Docker
make build
make up
```

## Documentation

### Guides
- **[Installation Guide](docs/guides/INSTALLATION.md)** - Setup instructions and requirements
- **[Getting Started](docs/guides/GETTING_STARTED.md)** - Quick start tutorial
- **[Usage Guide](docs/guides/USAGE.md)** - Commands, API usage, and examples
- **[Testing Guide](docs/guides/TESTING.md)** - Running tests and writing test cases
- **[Deployment Guide](docs/guides/DEPLOYMENT.md)** - Production deployment options
- **[Docker Guide](docs/guides/DOCKER.md)** - Container configuration
- **[Optimization Guide](docs/guides/OPTIMIZATION_GUIDE.md)** - Dependency and performance optimizations

### Technical Documentation
- **[Architecture Overview](docs/ARCHITECTURE.md)** - System design and components
- **[Docker Architecture](docs/architecture/docker/)** - Container strategies and optimizations
- **[API Reference](docs/API_REFERENCE.md)** - Detailed API documentation
- **[RAG Pipeline](docs/RAG_PIPELINE.md)** - Understanding the RAG architecture
- **[Vector Stores](docs/VECTOR_STORES.md)** - Database options and configuration

## Basic Usage

```bash
# Setup with initial data
python main_oop.py setup --tickers AAPL MSFT GOOGL

# Query the system
python main_oop.py query "What are the recent trends in tech stocks?"
```

See [Usage Guide](docs/guides/USAGE.md) for detailed instructions.

## Requirements

- Python 3.11+
- Docker (optional)
- OpenAI API key (or use mock provider)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/phdsystems/ohlcv-rag-system/issues)
- **Discussions**: [GitHub Discussions](https://github.com/phdsystems/ohlcv-rag-system/discussions)
- **Email**: support@phdsystems.com

## Disclaimer

This system is for educational and research purposes only. Not financial advice.

---

Built with ❤️ by [PhD Systems](https://phdsystems.com)