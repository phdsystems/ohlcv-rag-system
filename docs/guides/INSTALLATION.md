# Installation Guide

## Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose (for containerized deployment)
- Git
- 4GB RAM minimum (8GB recommended)
- 10GB free disk space

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/phdsystems/ohlcv-rag-system.git
cd ohlcv-rag-system

# Copy and configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Build and run
make build
make up
```

### Option 2: Local Installation

```bash
# Clone the repository
git clone https://github.com/phdsystems/ohlcv-rag-system.git
cd ohlcv-rag-system

# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

## Detailed Installation

### System Requirements

#### Hardware
- **CPU**: 2+ cores recommended
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 10GB for base installation, additional space for data

#### Software
- **Operating System**: Linux, macOS, or Windows with WSL2
- **Python**: 3.11, 3.12, or 3.13
- **Docker**: 20.10+ (if using Docker)
- **Git**: 2.x

### Python Environment Setup

#### Using uv (Recommended)

```bash
# Install uv globally
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv sync

# Activate environment (automatically handled by uv)
uv run python main.py
```

#### Using pip

```bash
# Create virtual environment
python -m venv venv

# Activate environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Using conda

```bash
# Create conda environment
conda create -n ohlcv-rag python=3.11

# Activate environment
conda activate ohlcv-rag

# Install dependencies
pip install -r requirements.txt
```

### Environment Configuration

Create a `.env` file with the following variables:

```bash
# Required
OPENAI_API_KEY=sk-your-openai-api-key

# Data Source Configuration
DATA_SOURCE=yahoo  # Options: yahoo, alphavantage, polygon, csv
TICKER_SYMBOLS=AAPL,MSFT,GOOGL,AMZN,TSLA
DATA_PERIOD=1y  # 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
DATA_INTERVAL=1d  # 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo

# Vector Store Configuration
VECTOR_STORE_TYPE=chromadb  # Options: chromadb, weaviate, qdrant, faiss, milvus
COLLECTION_NAME=ohlcv_data
PERSIST_DIRECTORY=./data/chromadb

# LLM Configuration
LLM_MODEL=gpt-3.5-turbo  # Options: gpt-3.5-turbo, gpt-4, gpt-4-turbo
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=2000

# Optional API Keys (for additional data sources)
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-key
POLYGON_API_KEY=your-polygon-key

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=./logs/ohlcv_rag.log
```

### Docker Installation

#### Building Images

```bash
# Build main runtime image
make build

# Build all targets (runtime, development, testing)
make build-all

# Build specific target
docker build --target runtime -t ohlcv-rag:latest .
```

#### Docker Compose Setup

```bash
# Start all services
docker-compose up -d

# Start specific vector store configuration
docker-compose -f docker-compose.yml -f docker-compose.chromadb.yml up -d
docker-compose -f docker-compose.yml -f docker-compose.weaviate.yml up -d
docker-compose -f docker-compose.yml -f docker-compose.qdrant.yml up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### Vector Store Installation

#### ChromaDB (Default)
No additional installation needed - embedded by default.

#### Weaviate
```bash
# Using Docker
docker run -d \
  -p 8080:8080 \
  -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
  -e PERSISTENCE_DATA_PATH=/var/lib/weaviate \
  semitechnologies/weaviate:latest
```

#### Qdrant
```bash
# Using Docker
docker run -d \
  -p 6333:6333 \
  -v ./data/qdrant:/qdrant/storage \
  qdrant/qdrant
```

#### Milvus
```bash
# Download docker-compose file
wget https://github.com/milvus-io/milvus/releases/download/v2.3.0/milvus-standalone-docker-compose.yml -O docker-compose-milvus.yml

# Start Milvus
docker-compose -f docker-compose-milvus.yml up -d
```

### Development Installation

For development with hot-reload and debugging:

```bash
# Install development dependencies
uv sync --dev

# Or with pip
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run development server
make dev
```

### Verification

Verify your installation:

```bash
# Check Python version
python --version

# Check dependencies
python -c "import src; print('Core package OK')"
python -c "import openai; print('OpenAI OK')"
python -c "import chromadb; print('ChromaDB OK')"

# Test basic functionality
python main.py status

# Run tests
make test-simple
```

## Troubleshooting

### Common Issues

#### 1. OpenAI API Key Error
```
Error: OpenAI API key not found
```
**Solution**: Ensure your `.env` file contains a valid `OPENAI_API_KEY`

#### 2. Docker Build Fails
```
Error: Cannot connect to Docker daemon
```
**Solution**: 
- Ensure Docker is running: `docker version`
- On Linux, add user to docker group: `sudo usermod -aG docker $USER`

#### 3. Python Version Error
```
Error: Python 3.11+ required
```
**Solution**: Install Python 3.11 or higher:
```bash
# Using pyenv
pyenv install 3.11.0
pyenv local 3.11.0
```

#### 4. Memory Error with Large Datasets
```
Error: Out of memory
```
**Solution**: 
- Increase Docker memory limit in Docker Desktop settings
- Use batch processing: `--batch-size 100`
- Use a more efficient vector store (Qdrant or Milvus)

#### 5. Port Already in Use
```
Error: bind: address already in use
```
**Solution**: 
- Change ports in `docker-compose.yml`
- Or stop conflicting service: `lsof -i :8000` and `kill <PID>`

### Getting Help

- Check logs: `make logs` or `docker-compose logs`
- Enable debug mode: Set `LOG_LEVEL=DEBUG` in `.env`
- Open an issue: [GitHub Issues](https://github.com/phdsystems/ohlcv-rag-system/issues)

## Next Steps

After installation:
1. Configure your data sources in `.env`
2. Run initial data ingestion: `python main.py setup`
3. Test with a query: `python main.py query "Show me AAPL trends"`
4. See [Usage Guide](USAGE.md) for detailed instructions