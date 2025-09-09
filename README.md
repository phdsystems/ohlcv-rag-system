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

# Setup environment
cp .env.example .env
# Add your OPENAI_API_KEY to .env

# Run with Docker
make build
make up
```

## Documentation

- **[Installation Guide](docs/INSTALLATION.md)** - Setup instructions and requirements
- **[Usage Guide](docs/USAGE.md)** - Commands, API usage, and examples
- **[Testing Guide](docs/TESTING.md)** - Running tests and writing test cases
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment options
- **[Architecture Overview](docs/ARCHITECTURE.md)** - System design and components
- **[API Reference](docs/API_REFERENCE.md)** - Detailed API documentation

### Deep Dives

- **[RAG Pipeline](docs/RAG_PIPELINE.md)** - Understanding the RAG architecture
- **[Visual RAG Guide](docs/RAG_PIPELINE_VISUAL.md)** - Visual explanations
- **[Vector Stores](docs/VECTOR_STORES.md)** - Database options and configuration
- **[Data Adapters](docs/DATA_ADAPTERS.md)** - Adding data sources
- **[Docker Guide](docs/DOCKER.md)** - Container configuration
- **[Coding Standards](docs/CODING_STANDARDS.md)** - Development practices

## Basic Usage

```bash
# Setup with initial data
python main_oop.py setup --tickers AAPL MSFT GOOGL

# Query the system
python main_oop.py query "What are the recent trends in tech stocks?"

# Run tests
make test
```

For detailed usage instructions, see the [Usage Guide](docs/USAGE.md).

## Requirements

- Python 3.11+
- Docker (optional)
- OpenAI API key

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