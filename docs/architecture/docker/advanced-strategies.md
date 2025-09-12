# Advanced Docker Strategies

## Overview

This document covers advanced Docker optimization strategies that complement our existing build and package management optimizations, focusing on runtime performance, orchestration, monitoring, and production deployment patterns.

## Table of Contents

1. [Container Orchestration Strategy](#container-orchestration-strategy)
2. [Volume Management & Performance](#volume-management--performance)
3. [Networking Optimization](#networking-optimization)
4. [Secret Management](#secret-management)
5. [Logging & Monitoring Strategy](#logging--monitoring-strategy)
6. [CI/CD Pipeline Optimization](#cicd-pipeline-optimization)
7. [Container Registry Strategy](#container-registry-strategy)
8. [Disaster Recovery & Backup](#disaster-recovery--backup)
9. [GPU Support Strategy](#gpu-support-strategy)
10. [Development Container Strategy](#development-container-strategy)

## Container Orchestration Strategy

### Docker Swarm Mode (Simple)

```yaml
# docker-compose.prod.yml
version: '3.9'

services:
  app:
    image: ohlcv-rag:latest
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
        failure_action: rollback
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      placement:
        constraints:
          - node.role == worker
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### Kubernetes Deployment (Advanced)

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ohlcv-rag
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: ohlcv-rag
  template:
    metadata:
      labels:
        app: ohlcv-rag
    spec:
      containers:
      - name: app
        image: ohlcv-rag:latest
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

## Volume Management & Performance

### Optimized Volume Mounts

```yaml
# docker-compose.yml
services:
  app:
    volumes:
      # Read-only mounts for security
      - ./config:/app/config:ro
      
      # Cached mounts for macOS performance
      - ./src:/app/src:cached
      
      # Delegated for write-heavy operations
      - ./data:/data:delegated
      
      # tmpfs for temporary files (RAM)
      - type: tmpfs
        target: /tmp
        tmpfs:
          size: 100M
```

### Named Volumes with Drivers

```yaml
volumes:
  data-volume:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /mnt/fast-ssd/data
  
  cache-volume:
    driver: local
    driver_opts:
      type: tmpfs
      o: size=1g,uid=1000,gid=1000
```

### Volume Performance Tuning

```dockerfile
# Use separate volumes for different I/O patterns
VOLUME ["/data/read-heavy"]  # SSD-backed
VOLUME ["/data/write-heavy"] # NVMe-backed
VOLUME ["/data/cache"]       # tmpfs (RAM)
```

## Networking Optimization

### Custom Networks with DNS

```yaml
# docker-compose.yml
networks:
  frontend:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/24
    driver_opts:
      com.docker.network.mtu: 9000  # Jumbo frames
  
  backend:
    driver: overlay
    encrypted: true
    internal: true
    attachable: true
```

### Service Mesh Pattern

```yaml
services:
  app:
    networks:
      - frontend
      - backend
    extra_hosts:
      - "host.docker.internal:host-gateway"
    sysctls:
      - net.core.somaxconn=1024
      - net.ipv4.tcp_syncookies=0
```

### Network Performance Tuning

```dockerfile
# Optimize network stack
RUN sysctl -w net.core.rmem_max=134217728 && \
    sysctl -w net.core.wmem_max=134217728 && \
    sysctl -w net.ipv4.tcp_rmem="4096 87380 134217728" && \
    sysctl -w net.ipv4.tcp_wmem="4096 65536 134217728"
```

## Secret Management

### Docker Secrets (Swarm)

```yaml
# docker-compose.yml
secrets:
  api_key:
    external: true
  db_password:
    file: ./secrets/db_password.txt

services:
  app:
    secrets:
      - api_key
      - db_password
    environment:
      API_KEY_FILE: /run/secrets/api_key
```

### BuildKit Secrets (Build-time)

```dockerfile
# Dockerfile
RUN --mount=type=secret,id=npm_token \
    NPM_TOKEN=$(cat /run/secrets/npm_token) && \
    npm config set //registry.npmjs.org/:_authToken=$NPM_TOKEN && \
    npm install --production
```

```bash
# Build command
docker build --secret id=npm_token,src=$HOME/.npm_token .
```

### Runtime Secret Injection

```yaml
# docker-compose.yml
services:
  app:
    environment:
      - AWS_ACCESS_KEY_ID_FILE=/run/secrets/aws_key
      - AWS_SECRET_ACCESS_KEY_FILE=/run/secrets/aws_secret
    configs:
      - source: app_config
        target: /app/config.json
        mode: 0440
```

## Logging & Monitoring Strategy

### Centralized Logging

```yaml
# docker-compose.yml
services:
  app:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        labels: "app=ohlcv-rag"
        env: "LOG_LEVEL,NODE_ENV"
    
  # Fluentd for log aggregation
  fluentd:
    image: fluent/fluentd:v1.14-alpine
    volumes:
      - ./fluent.conf:/fluentd/etc/fluent.conf
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
```

### Prometheus Metrics

```dockerfile
# Add metrics endpoint
RUN pip install prometheus-client

# Expose metrics port
EXPOSE 9090
```

```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server

request_count = Counter('app_requests_total', 'Total requests')
request_latency = Histogram('app_request_latency_seconds', 'Request latency')
active_connections = Gauge('app_active_connections', 'Active connections')
```

### Health Monitoring

```yaml
# docker-compose.yml
services:
  app:
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    
  # Healthcheck sidecar
  autoheal:
    image: willfarrell/autoheal
    environment:
      - AUTOHEAL_CONTAINER_LABEL=all
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
```

## CI/CD Pipeline Optimization

### GitHub Actions with Cache

```yaml
# .github/workflows/docker.yml
name: Docker CI/CD

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
        with:
          driver-opts: |
            network=host
            image=moby/buildkit:master
      
      - name: Cache Docker layers
        uses: actions/cache@v3
        with:
          path: /tmp/.buildx-cache
          key: ${{ runner.os }}-buildx-${{ github.sha }}
          restore-keys: |
            ${{ runner.os }}-buildx-
      
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ohlcv-rag:latest
            ohlcv-rag:${{ github.sha }}
          cache-from: type=local,src=/tmp/.buildx-cache
          cache-to: type=local,dest=/tmp/.buildx-cache-new,mode=max
          build-args: |
            BUILDKIT_INLINE_CACHE=1
            UV_CONCURRENT_DOWNLOADS=10
```

### Multi-Platform Builds

```bash
# Build for multiple architectures
docker buildx build \
  --platform linux/amd64,linux/arm64,linux/arm/v7 \
  --tag ohlcv-rag:multi-arch \
  --push .
```

### Automated Testing

```yaml
# docker-compose.test.yml
services:
  sut:
    build:
      context: .
      target: test
    command: pytest -v --cov --junitxml=/reports/junit.xml
    volumes:
      - test-reports:/reports
```

## Container Registry Strategy

### Registry Optimization

```yaml
# docker-compose.yml
services:
  registry:
    image: registry:2
    environment:
      REGISTRY_STORAGE_DELETE_ENABLED: "true"
      REGISTRY_STORAGE_CACHE_BLOBDESCRIPTOR: redis
      REGISTRY_REDIS_ADDR: redis:6379
    volumes:
      - registry-data:/var/lib/registry
    
  registry-ui:
    image: joxit/docker-registry-ui:latest
    environment:
      REGISTRY_URL: http://registry:5000
```

### Image Scanning

```yaml
# .github/workflows/security.yml
- name: Run Trivy vulnerability scanner
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: ohlcv-rag:${{ github.sha }}
    format: 'sarif'
    output: 'trivy-results.sarif'
    severity: 'CRITICAL,HIGH'
```

### Registry Mirroring

```json
// /etc/docker/daemon.json
{
  "registry-mirrors": [
    "https://mirror.gcr.io",
    "https://docker-mirror.internal"
  ],
  "insecure-registries": ["registry.internal:5000"]
}
```

## Disaster Recovery & Backup

### Automated Backups

```yaml
# docker-compose.backup.yml
services:
  backup:
    image: ohlcv-rag:latest
    command: /scripts/backup.sh
    environment:
      - BACKUP_SCHEDULE="0 2 * * *"
      - S3_BUCKET=ohlcv-backups
    volumes:
      - /data:/data:ro
      - ./scripts:/scripts:ro
```

### Volume Snapshots

```bash
#!/bin/bash
# backup-volumes.sh

# Create volume snapshot
docker run --rm \
  -v ohlcv-data:/data:ro \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/data-$(date +%Y%m%d).tar.gz /data

# Restore volume
docker run --rm \
  -v ohlcv-data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar xzf /backup/data-20240101.tar.gz -C /
```

### State Replication

```yaml
# docker-compose.yml
services:
  app-primary:
    image: ohlcv-rag:latest
    environment:
      - ROLE=primary
    
  app-replica:
    image: ohlcv-rag:latest
    environment:
      - ROLE=replica
      - PRIMARY_HOST=app-primary
    depends_on:
      - app-primary
```

## GPU Support Strategy

### NVIDIA GPU Support

```dockerfile
# Dockerfile.gpu
FROM nvidia/cuda:12.0-runtime-ubuntu22.04

# Install Python and dependencies
RUN apt-get update && apt-get install -y python3.11

# Install GPU-accelerated libraries
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

```yaml
# docker-compose.gpu.yml
services:
  app-gpu:
    build:
      dockerfile: Dockerfile.gpu
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - NVIDIA_DRIVER_CAPABILITIES=compute,utility
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

### CPU Fallback

```python
# gpu_utils.py
import torch

def get_device():
    if torch.cuda.is_available():
        return torch.device("cuda")
    elif torch.backends.mps.is_available():
        return torch.device("mps")  # Apple Silicon
    else:
        return torch.device("cpu")
```

## Development Container Strategy

### VS Code Dev Container

```json
// .devcontainer/devcontainer.json
{
  "name": "OHLCV RAG Dev",
  "dockerComposeFile": "../docker-compose.yml",
  "service": "dev",
  "workspaceFolder": "/app",
  "features": {
    "ghcr.io/devcontainers/features/python:1": {
      "version": "3.11"
    },
    "ghcr.io/devcontainers/features/git:1": {}
  },
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.vscode-pylance",
        "charliermarsh.ruff",
        "ms-azuretools.vscode-docker"
      ],
      "settings": {
        "python.defaultInterpreter": "/opt/venv/bin/python",
        "python.linting.enabled": true,
        "python.formatting.provider": "black"
      }
    }
  },
  "postCreateCommand": "uv sync --frozen",
  "remoteUser": "ohlcv"
}
```

### Codespaces Configuration

```yaml
# .devcontainer/docker-compose.yml
services:
  dev:
    build:
      context: ..
      dockerfile: Dockerfile.optimized
      target: development
    volumes:
      - ..:/workspace:cached
      - ~/.ssh:/home/ohlcv/.ssh:ro
      - ~/.gitconfig:/home/ohlcv/.gitconfig:ro
    environment:
      - DISPLAY=:0
    network_mode: host
```

## Performance Profiling

### Container Performance Analysis

```bash
# CPU profiling
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# I/O profiling
docker exec app iotop -b -n 1

# Network profiling
docker exec app iftop -t -s 10
```

### Build Performance Analysis

```dockerfile
# Add build-time metrics
ARG BUILD_START
RUN echo "Build started at: ${BUILD_START}"
RUN --mount=type=cache,target=/root/.cache \
    time uv sync --frozen
ARG BUILD_END
RUN echo "Build completed at: ${BUILD_END}"
```

## Summary

These advanced strategies complement our existing optimizations:

1. **Orchestration** - Scaling and deployment patterns
2. **Volumes** - Performance optimization and persistence
3. **Networking** - Custom networks and service mesh
4. **Secrets** - Secure credential management
5. **Monitoring** - Comprehensive logging and metrics
6. **CI/CD** - Automated building and testing
7. **Registry** - Image management and distribution
8. **Disaster Recovery** - Backup and restoration
9. **GPU Support** - Hardware acceleration
10. **Development** - Optimized dev environments

Together with our Docker optimization and UV strategies, these provide a complete containerization solution for development through production.