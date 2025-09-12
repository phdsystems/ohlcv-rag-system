# Quick Start Guide

## Option 1: Docker (Recommended) 🐳

```bash
# Clone and run
git clone https://github.com/phdsystems/ohlcv-rag-system.git
cd ohlcv-rag-system
make quick-start
```

That's it! The system is running.

## Option 2: Local Setup 💻

```bash
# Clone repository
git clone https://github.com/phdsystems/ohlcv-rag-system.git
cd ohlcv-rag-system

# Install and run (uv auto-installs if needed)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync
python main.py
```

## Your First Query

```bash
# Load sample data
python main_oop.py setup --tickers AAPL MSFT GOOGL

# Ask a question
python main_oop.py query "What are the trends in tech stocks?"
```

## No API Key? No Problem!

The system works with a mock LLM provider:

```bash
# In .env or environment
LLM_PROVIDER=mock
```

## Common Commands

```bash
make help      # Show all commands
make test      # Run tests
make shell     # Interactive shell
make clean     # Clean up
```

## Next Steps

- 📖 [Full Documentation](docs/)
- 🚀 [Getting Started Guide](docs/guides/GETTING_STARTED.md)
- 🐳 [Docker Guide](docs/guides/DOCKER.md)
- 💡 [Usage Examples](docs/guides/USAGE.md)

---

**Need help?** [Open an issue](https://github.com/phdsystems/ohlcv-rag-system/issues)