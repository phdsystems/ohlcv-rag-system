# Docker Documentation

## Overview

The OHLCV RAG System is fully containerized using Docker with BuildKit optimizations for fast, parallel builds. The image name defaults to the current Git branch name for easy version management.

## Features

- 🚀 **BuildKit Optimization**: Fast parallel builds with advanced caching
- 🎯 **Multi-stage Builds**: Separate targets for runtime, development, and production
- 🔄 **Parallel Building**: Build multiple targets simultaneously
- 🌳 **Branch-based Tagging**: Automatic image tagging based on Git branch
- 📦 **Multiple Vector Stores**: Support for ChromaDB, Weaviate, Qdrant, and Milvus
- 🛠️ **Development Tools**: Integrated Jupyter, debugging, and hot-reload

## Quick Start

```bash
# Build and run with one command
make quick-start

# Or manually
make build
make up
make logs
```

## Build System

### BuildKit Features

The Dockerfile uses BuildKit syntax for optimizations:

```dockerfile
# syntax=docker/dockerfile:1.4
```

Key optimizations:
- **Cache mounts**: Dependencies cached between builds
- **Parallel stages**: Multiple stages built simultaneously
- **Layer caching**: Intelligent layer reuse
- **Inline cache**: Cache embedded in images

### Build Script

The `scripts/docker-build.sh` script provides:

```bash
# Build default (runtime) target
./scripts/docker-build.sh

# Build all targets in parallel
./scripts/docker-build.sh --all

# Build specific target
./scripts/docker-build.sh --dev
./scripts/docker-build.sh --prod

# Build without cache
./scripts/docker-build.sh --no-cache

# Build and push to registry
./scripts/docker-build.sh --all --push
```

### Automatic Branch Tagging

Images are automatically tagged with the current Git branch:

```bash
# On branch 'main'
ohlcv-rag:main

# On branch 'feature/new-indicators'
ohlcv-rag:feature-new-indicators

# On branch 'fix/bug-123'
ohlcv-rag:fix-bug-123
```

## Docker Targets

### 1. Runtime (Default)
```dockerfile
FROM python:3.11-slim AS runtime
```
- Standard application runtime
- Non-root user execution
- Minimal dependencies
- ~500MB image size

### 2. Development
```dockerfile
FROM runtime AS development
```
- All runtime features
- Development tools (git, vim, htop)
- Jupyter notebook
- Testing frameworks
- ~700MB image size

### 3. Production
```dockerfile
FROM python:3.11-alpine AS production
```
- Alpine-based for minimal size
- Only essential dependencies
- Optimized for deployment
- ~250MB image size

## Docker Compose Services

### Main Application

```yaml
ohlcv-rag:
  image: ohlcv-rag:${IMAGE_TAG:-latest}
  volumes:
    - ./data:/data
    - ./.env:/app/.env:ro
```

### Vector Stores

Start with specific vector store:

```bash
# ChromaDB (embedded, default)
make up-chromadb

# Weaviate
make up-weaviate

# Qdrant
make up-qdrant

# Milvus (requires etcd and minio)
make up-milvus
```

## Usage

### Using Make

```bash
# Show all commands
make help

# Build operations
make build          # Build runtime image
make build-all      # Build all targets in parallel
make build-dev      # Build development image
make build-prod     # Build production image
make build-nocache  # Build without cache

# Container operations
make up            # Start services
make down          # Stop services
make logs          # Show logs
make shell         # Open shell in container
make clean         # Clean up resources

# Run commands
make run           # Run interactive mode
make run-setup     # Run data setup
make run-query QUERY="What are the trends?"

# Development
make dev           # Start dev environment
make jupyter       # Start Jupyter notebook
make test          # Run tests
make lint          # Run linters
make format        # Format code
```

### Using Docker Directly

```bash
# Build with BuildKit
DOCKER_BUILDKIT=1 docker build -t ohlcv-rag:latest .

# Run interactively
docker run -it --rm \
  -v $(pwd)/data:/data \
  -v $(pwd)/.env:/app/.env:ro \
  ohlcv-rag:latest \
  interactive

# Run specific command
docker run -it --rm \
  -v $(pwd)/data:/data \
  -v $(pwd)/.env:/app/.env:ro \
  ohlcv-rag:latest \
  query "What are the recent trends?"
```

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# Start with specific profile
docker-compose --profile chromadb up -d

# View logs
docker-compose logs -f ohlcv-rag

# Execute command in running container
docker-compose exec ohlcv-rag python main_oop.py status

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Environment Variables

### Build-time Variables

```bash
# Image naming
IMAGE_NAME=ohlcv-rag          # Base image name
IMAGE_TAG=main                # Tag (defaults to branch)

# BuildKit
DOCKER_BUILDKIT=1             # Enable BuildKit
BUILDKIT_PROGRESS=plain       # Progress output format
```

### Runtime Variables

```bash
# Application
OPENAI_API_KEY=sk-...         # OpenAI API key
DATA_SOURCE=yahoo             # Data source
VECTOR_STORE_TYPE=chromadb    # Vector store type
LLM_MODEL=gpt-3.5-turbo      # LLM model
LOG_LEVEL=INFO                # Log level

# Data
TICKER_SYMBOLS=AAPL,MSFT,GOOGL
DATA_PERIOD=1y
DATA_INTERVAL=1d
```

## Volumes

### Persistent Data

```yaml
volumes:
  - ./data:/data           # OHLCV data and vector stores
  - ./logs:/app/logs       # Application logs
  - ./.env:/app/.env:ro    # Environment configuration
```

### Vector Store Volumes

```yaml
volumes:
  chromadb-data:    # ChromaDB persistence
  weaviate-data:    # Weaviate persistence
  qdrant-data:      # Qdrant persistence
  milvus-data:      # Milvus persistence
```

## Networking

All services use a bridge network for inter-container communication:

```yaml
networks:
  ohlcv-network:
    driver: bridge
```

Service discovery uses container names:
- `ohlcv-rag` → Main application
- `chromadb` → ChromaDB service
- `weaviate` → Weaviate service
- `qdrant` → Qdrant service

## Health Checks

The application includes health checks:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s \
  --start-period=5s --retries=3 \
  CMD python -c "import sys; sys.exit(0)"
```

## Security

### Non-root User

Containers run as non-root user:

```dockerfile
RUN useradd -m -u 1000 -s /bin/bash ohlcv
USER ohlcv
```

### Read-only Mounts

Sensitive files mounted read-only:

```yaml
volumes:
  - ./.env:/app/.env:ro
```

### Secret Management

Never include secrets in images:

```bash
# Pass at runtime
docker run -e OPENAI_API_KEY=$OPENAI_API_KEY ...

# Or use env file
docker run --env-file .env ...
```

## Optimization Tips

### 1. Layer Caching

Order Dockerfile instructions from least to most frequently changing:

```dockerfile
# System dependencies (rarely change)
RUN apt-get update && apt-get install -y ...

# Python dependencies (occasionally change)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Application code (frequently changes)
COPY src/ ./src/
```

### 2. Multi-stage Builds

Use separate stages to minimize final image size:

```dockerfile
# Build stage
FROM python:3.11 AS builder
RUN pip install --user -r requirements.txt

# Runtime stage
FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
```

### 3. BuildKit Cache

Use cache mounts for package managers:

```dockerfile
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt
```

### 4. Parallel Builds

Build multiple images simultaneously:

```bash
# Enable BuildKit
export DOCKER_BUILDKIT=1

# Build in parallel
./scripts/docker-build.sh --all
```

## Troubleshooting

### Build Issues

```bash
# Clear Docker cache
docker system prune -af

# Build without cache
make build-nocache

# Check BuildKit status
echo $DOCKER_BUILDKIT

# View detailed build output
BUILDKIT_PROGRESS=plain make build
```

### Runtime Issues

```bash
# Check container logs
docker-compose logs ohlcv-rag

# Inspect running container
docker exec -it ohlcv-rag-app /bin/bash

# Check resource usage
docker stats

# View container details
docker inspect ohlcv-rag-app
```

### Permission Issues

```bash
# Fix data directory permissions
sudo chown -R 1000:1000 ./data

# Run with correct user
docker run --user 1000:1000 ...
```

### Network Issues

```bash
# List networks
docker network ls

# Inspect network
docker network inspect ohlcv-rag-system_ohlcv-network

# Test connectivity
docker exec ohlcv-rag-app ping chromadb
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Docker Build

on:
  push:
    branches: [main, develop]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Build images
        run: |
          export DOCKER_BUILDKIT=1
          ./scripts/docker-build.sh --all
      
      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          ./scripts/docker-build.sh --push
```

### Local Testing

```bash
# Test build
make build

# Run tests in container
make test

# Validate compose file
docker-compose config

# Dry run
docker-compose up --no-start
```

## Best Practices

1. **Always use BuildKit** for faster builds
2. **Tag images with branch names** for version tracking
3. **Use multi-stage builds** to minimize image size
4. **Run as non-root user** for security
5. **Mount secrets at runtime**, never build them in
6. **Use specific base image versions** (not `latest`)
7. **Leverage build cache** with proper layer ordering
8. **Clean up regularly** with `docker system prune`
9. **Monitor resource usage** with `docker stats`
10. **Use health checks** for production deployments

## Commands Reference

### Quick Reference

```bash
# Build and run
make quick-start

# Development
make dev

# Production build
make build-prod

# Clean everything
make clean-all

# Show status
make status
```

### Full Command List

Run `make help` to see all available commands with descriptions.

## Advanced Documentation

For detailed Docker strategies and best practices, see:

### Architecture Documentation
- **[Docker Optimization Strategy](../architecture/docker/optimization-strategy.md)** - Multi-stage builds, caching, parallelism
- **[UV Build Strategy](../architecture/docker/uv-build-strategy.md)** - Fast Python package management
- **[Container Orchestration](../architecture/docker/orchestration-strategy.md)** - Kubernetes and Swarm deployment
- **[Monitoring & Logging](../architecture/docker/monitoring-logging-strategy.md)** - Observability stack
- **[CI/CD Pipeline](../architecture/docker/cicd-pipeline-strategy.md)** - Automated builds and deployments
- **[Security Strategy](../architecture/docker/security-strategy.md)** - Container hardening and compliance