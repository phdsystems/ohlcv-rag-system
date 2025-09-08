# syntax=docker/dockerfile:1.4
# Multi-stage Dockerfile with BuildKit optimizations

# Build stage for Python dependencies
FROM python:3.11-slim AS python-deps

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

WORKDIR /tmp

# Copy dependency files
COPY pyproject.toml .
COPY uv.lock* .

# Install dependencies with uv sync (use full path to uv)
RUN --mount=type=cache,target=/root/.cache/uv \
    /root/.cargo/bin/uv sync --no-dev --no-install-project

# Build stage for application
FROM python:3.11-slim AS app-build

WORKDIR /app

# Copy application code
COPY src/ ./src/
COPY main.py .
COPY main_oop.py .
COPY .env.example .

# Create necessary directories
RUN mkdir -p data/chroma_db data/csv logs

# Runtime stage
FROM python:3.11-slim AS runtime

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash ohlcv && \
    mkdir -p /app /data && \
    chown -R ohlcv:ohlcv /app /data

WORKDIR /app

# Copy Python packages from deps stage (uv installs to .venv)
COPY --from=python-deps /tmp/.venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}" \
    VIRTUAL_ENV=/opt/venv

# Copy application from build stage
COPY --from=app-build --chown=ohlcv:ohlcv /app /app

# Copy additional files
COPY --chown=ohlcv:ohlcv docs/ ./docs/
COPY --chown=ohlcv:ohlcv README.md .

# Switch to non-root user
USER ohlcv

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app:${PATH}" \
    DATA_DIR="/data" \
    LOG_LEVEL=INFO

# Volume for persistent data
VOLUME ["/data"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command
ENTRYPOINT ["python"]
CMD ["main_oop.py", "status"]

# Development stage with additional tools
FROM runtime AS development

USER root

# Install development tools
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && apt-get install -y \
    vim \
    git \
    htop \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# Install uv and development Python packages
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    /root/.cargo/bin/uv tool install ipython && \
    /root/.cargo/bin/uv tool install jupyter && \
    /root/.cargo/bin/uv tool install pytest && \
    /root/.cargo/bin/uv tool install black && \
    /root/.cargo/bin/uv tool install flake8 && \
    /root/.cargo/bin/uv tool install mypy
ENV PATH="/root/.cargo/bin:/root/.local/bin:${PATH}"

USER ohlcv

# Jupyter port
EXPOSE 8888

CMD ["python", "main_oop.py", "interactive"]

# Production stage optimized for size
FROM python:3.11-alpine AS production

# Install only essential runtime dependencies
RUN apk add --no-cache \
    libstdc++ \
    libgomp

# Create non-root user
RUN adduser -D -u 1000 -s /bin/sh ohlcv && \
    mkdir -p /app /data && \
    chown -R ohlcv:ohlcv /app /data

WORKDIR /app

# Copy Python packages from deps stage (uv installs to .venv)
COPY --from=python-deps /tmp/.venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}" \
    VIRTUAL_ENV=/opt/venv
COPY --from=app-build --chown=ohlcv:ohlcv /app/src ./src
COPY --from=app-build --chown=ohlcv:ohlcv /app/main_oop.py .

USER ohlcv

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

VOLUME ["/data"]

ENTRYPOINT ["python", "main_oop.py"]