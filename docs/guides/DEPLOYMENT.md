# Deployment Guide

## Overview

This guide covers deployment options for the OHLCV RAG System, from development to production environments.

## Deployment Options

- **Local Development**: Quick setup for development and testing
- **Docker Single Host**: Production deployment on a single server
- **Docker Swarm**: Multi-node orchestration
- **Kubernetes**: Enterprise-scale deployment
- **Cloud Platforms**: AWS, GCP, Azure deployment

## Local Development

### Development Server

```bash
# Start development server with hot-reload
make dev

# Or manually
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### Environment Variables

```bash
# Development .env
DEBUG=true
LOG_LEVEL=DEBUG
RELOAD=true
WORKERS=1
```

## Production Deployment

### Single Host Deployment

#### 1. Server Requirements

- **OS**: Ubuntu 20.04+ or RHEL 8+
- **CPU**: 4+ cores
- **RAM**: 8GB minimum
- **Storage**: 50GB SSD
- **Network**: Static IP, ports 80/443

#### 2. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
```

#### 3. Application Deployment

```bash
# Clone repository
git clone https://github.com/phdsystems/ohlcv-rag-system.git
cd ohlcv-rag-system

# Configure production environment
cp .env.example .env.production
# Edit .env.production with production values

# Build production image
docker build --target production -t ohlcv-rag:prod .

# Start services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Production Configuration

#### docker-compose.prod.yml

```yaml
version: '3.8'

services:
  ohlcv-rag:
    image: ohlcv-rag:prod
    restart: always
    environment:
      - NODE_ENV=production
      - LOG_LEVEL=INFO
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - ohlcv-rag
```

#### Nginx Configuration

```nginx
upstream ohlcv_rag {
    server ohlcv-rag:8000;
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    location / {
        proxy_pass http://ohlcv_rag;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### SSL/TLS Setup

#### Using Let's Encrypt

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

#### Using Self-Signed (Development)

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/key.pem \
  -out ssl/cert.pem
```

## Docker Swarm Deployment

### Initialize Swarm

```bash
# On manager node
docker swarm init --advertise-addr <MANAGER-IP>

# Join worker nodes
docker swarm join --token <TOKEN> <MANAGER-IP>:2377
```

### Deploy Stack

```bash
# Create secrets
echo "your-api-key" | docker secret create openai_api_key -

# Deploy stack
docker stack deploy -c docker-stack.yml ohlcv-rag
```

### docker-stack.yml

```yaml
version: '3.8'

services:
  ohlcv-rag:
    image: ohlcv-rag:prod
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
    secrets:
      - openai_api_key
    networks:
      - ohlcv-net

  vector-store:
    image: qdrant/qdrant
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.role == manager
    volumes:
      - vector-data:/qdrant/storage
    networks:
      - ohlcv-net

networks:
  ohlcv-net:
    driver: overlay

volumes:
  vector-data:
    driver: local

secrets:
  openai_api_key:
    external: true
```

## Kubernetes Deployment

### Prerequisites

```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

### Kubernetes Manifests

#### deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ohlcv-rag
  namespace: ohlcv-system
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ohlcv-rag
  template:
    metadata:
      labels:
        app: ohlcv-rag
    spec:
      containers:
      - name: ohlcv-rag
        image: ohlcv-rag:prod
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: ohlcv-secrets
              key: openai-api-key
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
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

#### service.yaml

```yaml
apiVersion: v1
kind: Service
metadata:
  name: ohlcv-rag-service
  namespace: ohlcv-system
spec:
  selector:
    app: ohlcv-rag
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: LoadBalancer
```

#### ingress.yaml

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ohlcv-rag-ingress
  namespace: ohlcv-system
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.your-domain.com
    secretName: ohlcv-tls
  rules:
  - host: api.your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ohlcv-rag-service
            port:
              number: 80
```

### Deploy to Kubernetes

```bash
# Create namespace
kubectl create namespace ohlcv-system

# Create secrets
kubectl create secret generic ohlcv-secrets \
  --from-literal=openai-api-key=your-key \
  -n ohlcv-system

# Apply manifests
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml

# Check status
kubectl get pods -n ohlcv-system
kubectl get svc -n ohlcv-system
```

## Cloud Deployments

### AWS ECS

```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_URI
docker build -t ohlcv-rag .
docker tag ohlcv-rag:latest $ECR_URI/ohlcv-rag:latest
docker push $ECR_URI/ohlcv-rag:latest

# Create task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create service
aws ecs create-service \
  --cluster ohlcv-cluster \
  --service-name ohlcv-rag \
  --task-definition ohlcv-rag:1 \
  --desired-count 2
```

### Google Cloud Run

```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/$PROJECT_ID/ohlcv-rag

# Deploy to Cloud Run
gcloud run deploy ohlcv-rag \
  --image gcr.io/$PROJECT_ID/ohlcv-rag \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars OPENAI_API_KEY=$OPENAI_API_KEY
```

### Azure Container Instances

```bash
# Create resource group
az group create --name ohlcv-rg --location eastus

# Create container registry
az acr create --resource-group ohlcv-rg --name ohlcvregistry --sku Basic

# Build and push
az acr build --registry ohlcvregistry --image ohlcv-rag:latest .

# Deploy container
az container create \
  --resource-group ohlcv-rg \
  --name ohlcv-rag \
  --image ohlcvregistry.azurecr.io/ohlcv-rag:latest \
  --cpu 2 --memory 4 \
  --environment-variables OPENAI_API_KEY=$OPENAI_API_KEY
```

## Monitoring and Logging

### Prometheus + Grafana

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    volumes:
      - grafana-data:/var/lib/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

volumes:
  prometheus-data:
  grafana-data:
```

### ELK Stack

```bash
# Deploy Elasticsearch, Logstash, Kibana
docker-compose -f docker-compose.elk.yml up -d

# Configure Logstash pipeline
cat > logstash/pipeline/ohlcv.conf << EOF
input {
  tcp {
    port => 5000
    codec => json
  }
}
output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "ohlcv-logs-%{+YYYY.MM.dd}"
  }
}
EOF
```

## Backup and Recovery

### Automated Backups

```bash
#!/bin/bash
# backup.sh

# Backup vector store
docker exec vector-store qdrant-backup /backup/qdrant-$(date +%Y%m%d).tar

# Backup application data
tar -czf /backup/ohlcv-data-$(date +%Y%m%d).tar.gz /app/data

# Upload to S3
aws s3 cp /backup/ s3://ohlcv-backups/ --recursive

# Clean old backups
find /backup -mtime +7 -delete
```

### Restore Procedure

```bash
# Restore vector store
docker exec vector-store qdrant-restore /backup/qdrant-20240115.tar

# Restore application data
tar -xzf /backup/ohlcv-data-20240115.tar.gz -C /
```

## Performance Tuning

### Docker Optimization

```dockerfile
# Multi-stage build for smaller image
FROM python:3.11-slim as builder
# Build stage...

FROM python:3.11-alpine as runtime
# Runtime stage...
```

### Resource Limits

```yaml
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 8G
    reservations:
      cpus: '2'
      memory: 4G
```

### Scaling Configuration

```bash
# Horizontal scaling
docker-compose up --scale ohlcv-rag=5

# Vertical scaling
docker update --cpus 4 --memory 8g ohlcv-rag
```

## Security Considerations

1. **API Keys**: Use secrets management (Docker secrets, K8s secrets)
2. **Network**: Use private networks, firewall rules
3. **SSL/TLS**: Always use HTTPS in production
4. **Updates**: Regular security updates
5. **Monitoring**: Set up intrusion detection
6. **Backups**: Regular encrypted backups

## Troubleshooting

### Common Issues

1. **Container fails to start**
   - Check logs: `docker logs ohlcv-rag`
   - Verify environment variables
   - Check resource limits

2. **Performance issues**
   - Monitor with `docker stats`
   - Check vector store performance
   - Review query patterns

3. **Network connectivity**
   - Test with `docker exec ohlcv-rag ping vector-store`
   - Check firewall rules
   - Verify DNS resolution

## Support

- Documentation: [docs/](../docs/)
- Issues: [GitHub Issues](https://github.com/phdsystems/ohlcv-rag-system/issues)
- Community: [Discussions](https://github.com/phdsystems/ohlcv-rag-system/discussions)