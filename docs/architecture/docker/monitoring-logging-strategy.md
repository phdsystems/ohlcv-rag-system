# Monitoring and Logging Strategy

## Overview

This document outlines our comprehensive monitoring and logging strategy for containerized deployments of the OHLCV RAG System, including metrics collection, log aggregation, alerting, and observability.

## Table of Contents

1. [Monitoring Architecture](#monitoring-architecture)
2. [Metrics Collection with Prometheus](#metrics-collection-with-prometheus)
3. [Logging Strategy with ELK Stack](#logging-strategy-with-elk-stack)
4. [Distributed Tracing with Jaeger](#distributed-tracing-with-jaeger)
5. [Health Checks and Readiness Probes](#health-checks-and-readiness-probes)
6. [Alerting Configuration](#alerting-configuration)
7. [Dashboards with Grafana](#dashboards-with-grafana)
8. [Application Performance Monitoring](#application-performance-monitoring)
9. [Cost and Resource Monitoring](#cost-and-resource-monitoring)

## Monitoring Architecture

### Three Pillars of Observability

```yaml
# Monitoring Stack Components
Metrics: Prometheus + Grafana
Logging: Elasticsearch + Logstash + Kibana
Tracing: Jaeger + OpenTelemetry
```

### Architecture Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   App Pod   │────▶│ Prometheus  │────▶│   Grafana   │
│  (metrics)  │     │   Server    │     │ (dashboards)│
└─────────────┘     └─────────────┘     └─────────────┘
       │                                         │
       │            ┌─────────────┐             │
       ├───────────▶│  Logstash   │             │
       │            └─────────────┘             │
       │                   │                     │
       │                   ▼                     │
       │            ┌─────────────┐             │
       │            │Elasticsearch│◀────────────┘
       │            └─────────────┘
       │                   │
       │                   ▼
       │            ┌─────────────┐
       └───────────▶│   Jaeger    │
        (traces)    └─────────────┘
```

## Metrics Collection with Prometheus

### Application Metrics Implementation

```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge, Info, start_http_server
from prometheus_client import CollectorRegistry, generate_latest
import time
from functools import wraps

# Create custom registry
registry = CollectorRegistry()

# Define metrics
request_count = Counter(
    'ohlcv_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)

request_latency = Histogram(
    'ohlcv_request_duration_seconds',
    'Request latency in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=registry
)

active_connections = Gauge(
    'ohlcv_active_connections',
    'Number of active connections',
    registry=registry
)

model_inference_time = Histogram(
    'ohlcv_model_inference_seconds',
    'Model inference time',
    ['model_name', 'operation'],
    registry=registry
)

vector_db_operations = Counter(
    'ohlcv_vector_db_operations_total',
    'Vector database operations',
    ['operation', 'status'],
    registry=registry
)

cache_hits = Counter(
    'ohlcv_cache_hits_total',
    'Cache hit count',
    ['cache_type'],
    registry=registry
)

app_info = Info(
    'ohlcv_app',
    'Application information',
    registry=registry
)

# Decorator for timing functions
def measure_latency(endpoint):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                status = 'success'
            except Exception as e:
                status = 'error'
                raise
            finally:
                duration = time.time() - start_time
                request_latency.labels(
                    method='GET',
                    endpoint=endpoint
                ).observe(duration)
                request_count.labels(
                    method='GET',
                    endpoint=endpoint,
                    status=status
                ).inc()
            return result
        return wrapper
    return decorator

# Start metrics server
def start_metrics_server(port=9090):
    start_http_server(port, registry=registry)
    app_info.info({
        'version': '1.0.0',
        'environment': 'production',
        'commit': 'abc123'
    })

# Example usage
@measure_latency('/api/query')
def process_query(query):
    with active_connections.track_inprogress():
        # Simulate processing
        time.sleep(0.1)
        return {"result": "processed"}
```

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'ohlcv-prod'
    environment: 'production'

# Alerting configuration
alerting:
  alertmanagers:
  - static_configs:
    - targets:
      - alertmanager:9093

# Load rules
rule_files:
  - "alerts/*.yml"
  - "recording_rules/*.yml"

# Scrape configurations
scrape_configs:
  # Application metrics
  - job_name: 'ohlcv-app'
    kubernetes_sd_configs:
    - role: pod
      namespaces:
        names:
        - ohlcv-system
    relabel_configs:
    - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
      action: keep
      regex: true
    - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
      action: replace
      target_label: __metrics_path__
      regex: (.+)
    - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
      action: replace
      regex: ([^:]+)(?::\d+)?;(\d+)
      replacement: $1:$2
      target_label: __address__
    - action: labelmap
      regex: __meta_kubernetes_pod_label_(.+)
    metric_relabel_configs:
    - source_labels: [__name__]
      regex: 'ohlcv_.*'
      action: keep

  # Node metrics
  - job_name: 'node-exporter'
    kubernetes_sd_configs:
    - role: node
    relabel_configs:
    - action: labelmap
      regex: __meta_kubernetes_node_label_(.+)

  # Container metrics
  - job_name: 'cadvisor'
    kubernetes_sd_configs:
    - role: node
    scheme: https
    tls_config:
      ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
    relabel_configs:
    - action: labelmap
      regex: __meta_kubernetes_node_label_(.+)
    metric_relabel_configs:
    - source_labels: [container]
      regex: 'ohlcv.*'
      action: keep

  # Docker metrics
  - job_name: 'docker'
    static_configs:
    - targets: ['docker-host:9323']
```

### Recording Rules

```yaml
# recording_rules/aggregations.yml
groups:
  - name: ohlcv_aggregations
    interval: 30s
    rules:
    - record: ohlcv:request_rate_5m
      expr: rate(ohlcv_requests_total[5m])
    
    - record: ohlcv:error_rate_5m
      expr: rate(ohlcv_requests_total{status="error"}[5m])
    
    - record: ohlcv:p95_latency_5m
      expr: histogram_quantile(0.95, rate(ohlcv_request_duration_seconds_bucket[5m]))
    
    - record: ohlcv:vector_ops_rate
      expr: sum(rate(ohlcv_vector_db_operations_total[5m])) by (operation)
    
    - record: ohlcv:cache_hit_ratio
      expr: |
        sum(rate(ohlcv_cache_hits_total[5m])) /
        (sum(rate(ohlcv_cache_hits_total[5m])) + sum(rate(ohlcv_cache_misses_total[5m])))
```

## Logging Strategy with ELK Stack

### Structured Logging Implementation

```python
# logging_config.py
import logging
import json
import sys
from pythonjsonlogger import jsonlogger
from datetime import datetime
import traceback

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno
        
        # Add container metadata
        log_record['container_id'] = os.environ.get('HOSTNAME', 'unknown')
        log_record['service'] = 'ohlcv-rag'
        log_record['environment'] = os.environ.get('ENVIRONMENT', 'development')
        log_record['version'] = os.environ.get('APP_VERSION', '1.0.0')
        
        # Add trace information if available
        if hasattr(record, 'trace_id'):
            log_record['trace_id'] = record.trace_id
        if hasattr(record, 'span_id'):
            log_record['span_id'] = record.span_id
        
        # Add exception info if present
        if record.exc_info:
            log_record['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'stacktrace': traceback.format_exception(*record.exc_info)
            }

def setup_logging():
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Create console handler with JSON formatter
    handler = logging.StreamHandler(sys.stdout)
    formatter = CustomJsonFormatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Add correlation ID filter
    logger.addFilter(CorrelationIdFilter())
    
    return logger

class CorrelationIdFilter(logging.Filter):
    def filter(self, record):
        record.correlation_id = get_correlation_id()
        return True

# Usage example
logger = setup_logging()

logger.info("Application started", extra={
    "config": {"db": "connected", "cache": "enabled"},
    "metrics": {"startup_time": 1.23}
})

logger.error("Database connection failed", extra={
    "error_code": "DB_001",
    "retry_count": 3,
    "trace_id": "abc-123-def"
}, exc_info=True)
```

### Logstash Configuration

```ruby
# logstash.conf
input {
  # Docker logs
  beats {
    port => 5044
    type => "docker"
  }
  
  # Application logs via TCP
  tcp {
    port => 5000
    codec => json
    type => "app"
  }
  
  # Kubernetes logs
  file {
    path => "/var/log/containers/ohlcv-*.log"
    type => "kubernetes"
    codec => "json"
  }
}

filter {
  # Parse JSON logs
  if [type] == "app" {
    json {
      source => "message"
    }
  }
  
  # Parse Docker logs
  if [type] == "docker" {
    grok {
      match => {
        "message" => "%{TIMESTAMP_ISO8601:timestamp} %{LOGLEVEL:level} %{GREEDYDATA:message}"
      }
    }
  }
  
  # Enrich with Docker metadata
  if [docker] {
    mutate {
      add_field => {
        "container_name" => "%{[docker][container][name]}"
        "container_id" => "%{[docker][container][id]}"
        "image" => "%{[docker][container][image]}"
      }
    }
  }
  
  # Add GeoIP information
  if [client_ip] {
    geoip {
      source => "client_ip"
      target => "geoip"
    }
  }
  
  # Parse stack traces
  if [exception] {
    mutate {
      add_field => {
        "error_type" => "%{[exception][type]}"
        "error_message" => "%{[exception][message]}"
      }
    }
  }
  
  # Calculate response time
  if [request_start] and [request_end] {
    ruby {
      code => "
        start_time = event.get('request_start').to_f
        end_time = event.get('request_end').to_f
        event.set('response_time', (end_time - start_time) * 1000)
      "
    }
  }
}

output {
  # Send to Elasticsearch
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "ohlcv-%{+YYYY.MM.dd}"
    template_name => "ohlcv"
    template => "/etc/logstash/templates/ohlcv.json"
    template_overwrite => true
  }
  
  # Debug output
  if [level] == "ERROR" {
    stdout {
      codec => rubydebug
    }
  }
}
```

### Elasticsearch Index Template

```json
{
  "index_patterns": ["ohlcv-*"],
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 1,
    "index.lifecycle.name": "ohlcv-ilm-policy",
    "index.lifecycle.rollover_alias": "ohlcv-logs"
  },
  "mappings": {
    "properties": {
      "@timestamp": {
        "type": "date"
      },
      "level": {
        "type": "keyword"
      },
      "message": {
        "type": "text",
        "fields": {
          "keyword": {
            "type": "keyword",
            "ignore_above": 256
          }
        }
      },
      "container_id": {
        "type": "keyword"
      },
      "service": {
        "type": "keyword"
      },
      "trace_id": {
        "type": "keyword"
      },
      "span_id": {
        "type": "keyword"
      },
      "correlation_id": {
        "type": "keyword"
      },
      "response_time": {
        "type": "float"
      },
      "error_code": {
        "type": "keyword"
      },
      "exception": {
        "properties": {
          "type": {
            "type": "keyword"
          },
          "message": {
            "type": "text"
          },
          "stacktrace": {
            "type": "text"
          }
        }
      }
    }
  }
}
```

## Distributed Tracing with Jaeger

### OpenTelemetry Integration

```python
# tracing.py
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

def setup_tracing(service_name="ohlcv-rag", jaeger_endpoint="http://jaeger:14268/api/traces"):
    # Create resource
    resource = Resource(attributes={
        SERVICE_NAME: service_name,
        "service.version": "1.0.0",
        "deployment.environment": os.environ.get("ENVIRONMENT", "development")
    })
    
    # Create tracer provider
    provider = TracerProvider(resource=resource)
    
    # Create Jaeger exporter
    jaeger_exporter = JaegerExporter(
        collector_endpoint=jaeger_endpoint,
    )
    
    # Create span processor
    span_processor = BatchSpanProcessor(jaeger_exporter)
    provider.add_span_processor(span_processor)
    
    # Set tracer provider
    trace.set_tracer_provider(provider)
    
    # Set propagator
    set_global_textmap(TraceContextTextMapPropagator())
    
    # Auto-instrument libraries
    RequestsInstrumentor().instrument()
    
    return trace.get_tracer(__name__)

# Usage
tracer = setup_tracing()

@tracer.start_as_current_span("process_ohlcv_query")
def process_query(query):
    span = trace.get_current_span()
    span.set_attribute("query.text", query)
    span.set_attribute("query.length", len(query))
    
    with tracer.start_as_current_span("vector_search") as search_span:
        search_span.set_attribute("db.system", "chromadb")
        # Perform vector search
        results = vector_search(query)
        search_span.set_attribute("results.count", len(results))
    
    with tracer.start_as_current_span("llm_inference") as llm_span:
        llm_span.set_attribute("model.name", "gpt-3.5-turbo")
        # Call LLM
        response = llm_call(query, results)
        llm_span.set_attribute("response.tokens", count_tokens(response))
    
    return response
```

### Jaeger Configuration

```yaml
# jaeger-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jaeger
  namespace: ohlcv-system
spec:
  replicas: 1
  selector:
    matchLabels:
      app: jaeger
  template:
    metadata:
      labels:
        app: jaeger
    spec:
      containers:
      - name: jaeger
        image: jaegertracing/all-in-one:1.45
        env:
        - name: COLLECTOR_ZIPKIN_HOST_PORT
          value: ":9411"
        - name: SPAN_STORAGE_TYPE
          value: elasticsearch
        - name: ES_SERVER_URLS
          value: http://elasticsearch:9200
        - name: ES_INDEX_PREFIX
          value: ohlcv-traces
        ports:
        - containerPort: 5775
          protocol: UDP
        - containerPort: 6831
          protocol: UDP
        - containerPort: 6832
          protocol: UDP
        - containerPort: 5778
          protocol: TCP
        - containerPort: 16686
          protocol: TCP
        - containerPort: 14268
          protocol: TCP
        - containerPort: 14250
          protocol: TCP
        - containerPort: 9411
          protocol: TCP
```

## Health Checks and Readiness Probes

### Health Check Implementation

```python
# health.py
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

@dataclass
class ComponentHealth:
    name: str
    status: HealthStatus
    message: Optional[str] = None
    last_check: Optional[datetime] = None
    metadata: Optional[Dict] = None

class HealthChecker:
    def __init__(self):
        self.components = {}
        
    async def check_database(self) -> ComponentHealth:
        try:
            # Check database connection
            conn = await get_db_connection()
            await conn.execute("SELECT 1")
            return ComponentHealth(
                name="database",
                status=HealthStatus.HEALTHY,
                message="Database is responsive",
                last_check=datetime.utcnow()
            )
        except Exception as e:
            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database error: {str(e)}",
                last_check=datetime.utcnow()
            )
    
    async def check_vector_store(self) -> ComponentHealth:
        try:
            # Check ChromaDB
            client = get_chromadb_client()
            client.heartbeat()
            return ComponentHealth(
                name="vector_store",
                status=HealthStatus.HEALTHY,
                message="Vector store is responsive",
                last_check=datetime.utcnow()
            )
        except Exception as e:
            return ComponentHealth(
                name="vector_store",
                status=HealthStatus.DEGRADED,
                message=f"Vector store warning: {str(e)}",
                last_check=datetime.utcnow()
            )
    
    async def check_cache(self) -> ComponentHealth:
        try:
            # Check Redis cache
            cache = get_redis_client()
            await cache.ping()
            return ComponentHealth(
                name="cache",
                status=HealthStatus.HEALTHY,
                message="Cache is responsive",
                last_check=datetime.utcnow()
            )
        except Exception as e:
            # Cache is optional, so degraded not unhealthy
            return ComponentHealth(
                name="cache",
                status=HealthStatus.DEGRADED,
                message=f"Cache unavailable: {str(e)}",
                last_check=datetime.utcnow()
            )
    
    async def check_llm_api(self) -> ComponentHealth:
        try:
            # Check LLM API availability
            response = await test_llm_connection()
            return ComponentHealth(
                name="llm_api",
                status=HealthStatus.HEALTHY,
                message="LLM API is responsive",
                last_check=datetime.utcnow(),
                metadata={"model": response.model, "latency": response.latency}
            )
        except Exception as e:
            return ComponentHealth(
                name="llm_api",
                status=HealthStatus.UNHEALTHY,
                message=f"LLM API error: {str(e)}",
                last_check=datetime.utcnow()
            )
    
    async def get_health(self) -> Dict:
        # Run all health checks in parallel
        checks = await asyncio.gather(
            self.check_database(),
            self.check_vector_store(),
            self.check_cache(),
            self.check_llm_api(),
            return_exceptions=True
        )
        
        # Process results
        overall_status = HealthStatus.HEALTHY
        components = []
        
        for check in checks:
            if isinstance(check, Exception):
                components.append(ComponentHealth(
                    name="unknown",
                    status=HealthStatus.UNHEALTHY,
                    message=str(check)
                ))
                overall_status = HealthStatus.UNHEALTHY
            else:
                components.append(check)
                if check.status == HealthStatus.UNHEALTHY:
                    overall_status = HealthStatus.UNHEALTHY
                elif check.status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED
        
        return {
            "status": overall_status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "components": [
                {
                    "name": c.name,
                    "status": c.status.value,
                    "message": c.message,
                    "last_check": c.last_check.isoformat() if c.last_check else None,
                    "metadata": c.metadata
                }
                for c in components
            ]
        }

# FastAPI endpoints
from fastapi import FastAPI, Response

app = FastAPI()
health_checker = HealthChecker()

@app.get("/health")
async def health_check(response: Response):
    health = await health_checker.get_health()
    
    if health["status"] == "unhealthy":
        response.status_code = 503
    elif health["status"] == "degraded":
        response.status_code = 200  # Still return 200 for degraded
    
    return health

@app.get("/ready")
async def readiness_check(response: Response):
    health = await health_checker.get_health()
    
    # Only ready if healthy (not degraded)
    if health["status"] != "healthy":
        response.status_code = 503
        return {"ready": False, "reason": health}
    
    return {"ready": True}

@app.get("/startup")
async def startup_check():
    # Simple check for startup probe
    return {"status": "ok"}
```

## Alerting Configuration

### Alert Rules

```yaml
# alerts/application.yml
groups:
  - name: ohlcv_application
    rules:
    - alert: HighErrorRate
      expr: |
        (sum(rate(ohlcv_requests_total{status="error"}[5m])) /
         sum(rate(ohlcv_requests_total[5m]))) > 0.05
      for: 5m
      labels:
        severity: warning
        component: application
      annotations:
        summary: "High error rate detected"
        description: "Error rate is {{ $value | humanizePercentage }} for the last 5 minutes"
    
    - alert: HighLatency
      expr: |
        histogram_quantile(0.95,
          sum(rate(ohlcv_request_duration_seconds_bucket[5m])) by (le)
        ) > 2
      for: 10m
      labels:
        severity: warning
        component: application
      annotations:
        summary: "High request latency"
        description: "95th percentile latency is {{ $value }}s"
    
    - alert: PodCrashLooping
      expr: |
        rate(kube_pod_container_status_restarts_total{namespace="ohlcv-system"}[15m]) > 0
      for: 5m
      labels:
        severity: critical
        component: kubernetes
      annotations:
        summary: "Pod {{ $labels.pod }} is crash looping"
        description: "Pod has restarted {{ $value }} times in the last 15 minutes"
    
    - alert: HighMemoryUsage
      expr: |
        (container_memory_usage_bytes{pod=~"ohlcv-.*"} /
         container_spec_memory_limit_bytes{pod=~"ohlcv-.*"}) > 0.9
      for: 5m
      labels:
        severity: warning
        component: resources
      annotations:
        summary: "High memory usage for {{ $labels.pod }}"
        description: "Memory usage is {{ $value | humanizePercentage }}"
    
    - alert: VectorDBUnresponsive
      expr: |
        up{job="chromadb"} == 0
      for: 2m
      labels:
        severity: critical
        component: database
      annotations:
        summary: "ChromaDB is down"
        description: "ChromaDB has been unresponsive for 2 minutes"
```

### AlertManager Configuration

```yaml
# alertmanager.yml
global:
  resolve_timeout: 5m
  slack_api_url: 'YOUR_SLACK_WEBHOOK_URL'

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'default'
  routes:
  - match:
      severity: critical
    receiver: 'critical'
    continue: true
  - match:
      severity: warning
    receiver: 'warning'

receivers:
  - name: 'default'
    slack_configs:
    - channel: '#ohlcv-alerts'
      title: 'OHLCV Alert'
      text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

  - name: 'critical'
    slack_configs:
    - channel: '#ohlcv-critical'
      title: '🚨 CRITICAL: {{ .GroupLabels.alertname }}'
      text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
    pagerduty_configs:
    - service_key: 'YOUR_PAGERDUTY_KEY'

  - name: 'warning'
    slack_configs:
    - channel: '#ohlcv-warnings'
      title: '⚠️ Warning: {{ .GroupLabels.alertname }}'
      text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'cluster', 'service']
```

## Dashboards with Grafana

### Dashboard Configuration

```json
{
  "dashboard": {
    "title": "OHLCV RAG System Overview",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "sum(rate(ohlcv_requests_total[5m])) by (endpoint)",
            "legendFormat": "{{ endpoint }}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "sum(rate(ohlcv_requests_total{status=\"error\"}[5m])) / sum(rate(ohlcv_requests_total[5m]))",
            "legendFormat": "Error Rate"
          }
        ],
        "type": "stat",
        "thresholds": {
          "mode": "absolute",
          "steps": [
            {"color": "green", "value": null},
            {"color": "yellow", "value": 0.01},
            {"color": "red", "value": 0.05}
          ]
        }
      },
      {
        "title": "Response Time (P50, P95, P99)",
        "targets": [
          {
            "expr": "histogram_quantile(0.5, sum(rate(ohlcv_request_duration_seconds_bucket[5m])) by (le))",
            "legendFormat": "P50"
          },
          {
            "expr": "histogram_quantile(0.95, sum(rate(ohlcv_request_duration_seconds_bucket[5m])) by (le))",
            "legendFormat": "P95"
          },
          {
            "expr": "histogram_quantile(0.99, sum(rate(ohlcv_request_duration_seconds_bucket[5m])) by (le))",
            "legendFormat": "P99"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Vector DB Operations",
        "targets": [
          {
            "expr": "sum(rate(ohlcv_vector_db_operations_total[5m])) by (operation)",
            "legendFormat": "{{ operation }}"
          }
        ],
        "type": "piechart"
      },
      {
        "title": "Cache Hit Ratio",
        "targets": [
          {
            "expr": "ohlcv:cache_hit_ratio",
            "legendFormat": "Hit Ratio"
          }
        ],
        "type": "gauge",
        "max": 1,
        "thresholds": {
          "mode": "absolute",
          "steps": [
            {"color": "red", "value": null},
            {"color": "yellow", "value": 0.5},
            {"color": "green", "value": 0.8}
          ]
        }
      },
      {
        "title": "Container Resources",
        "targets": [
          {
            "expr": "sum(container_memory_usage_bytes{pod=~\"ohlcv-.*\"}) by (pod)",
            "legendFormat": "{{ pod }} - Memory"
          },
          {
            "expr": "sum(rate(container_cpu_usage_seconds_total{pod=~\"ohlcv-.*\"}[5m])) by (pod)",
            "legendFormat": "{{ pod }} - CPU"
          }
        ],
        "type": "graph"
      }
    ]
  }
}
```

## Application Performance Monitoring

### APM Integration

```python
# apm.py
from elasticapm import Client
from elasticapm.contrib.flask import ElasticAPM

# Initialize APM client
apm_client = Client({
    'SERVICE_NAME': 'ohlcv-rag',
    'SERVER_URL': 'http://apm-server:8200',
    'ENVIRONMENT': 'production',
    'SECRET_TOKEN': 'your-secret-token'
})

# Flask integration
app = Flask(__name__)
apm = ElasticAPM(app, client=apm_client)

# Custom transaction
def process_data(data):
    # Start transaction
    apm_client.begin_transaction('custom')
    
    try:
        # Create span for database operation
        with apm_client.capture_span('db_query', span_type='db'):
            result = database_query(data)
        
        # Create span for processing
        with apm_client.capture_span('data_processing', span_type='app'):
            processed = process_result(result)
        
        # Set transaction result
        apm_client.end_transaction('process_data', 'success')
        return processed
        
    except Exception as e:
        # Capture exception
        apm_client.capture_exception()
        apm_client.end_transaction('process_data', 'error')
        raise
```

## Cost and Resource Monitoring

### Cost Tracking

```yaml
# cost-monitoring.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: kubecost-config
  namespace: ohlcv-system
data:
  pricing.yaml: |
    CPU: 0.031
    RAM: 0.004
    storage: 0.00013
    gpu: 0.45
    
  labels_to_track:
    - app
    - environment
    - team
    - cost-center
```

### Resource Metrics Collection

```python
# resource_metrics.py
import psutil
import GPUtil

def collect_resource_metrics():
    metrics = {
        "cpu": {
            "usage_percent": psutil.cpu_percent(interval=1),
            "count": psutil.cpu_count(),
            "freq": psutil.cpu_freq().current
        },
        "memory": {
            "total": psutil.virtual_memory().total,
            "available": psutil.virtual_memory().available,
            "percent": psutil.virtual_memory().percent,
            "used": psutil.virtual_memory().used
        },
        "disk": {
            "total": psutil.disk_usage('/').total,
            "used": psutil.disk_usage('/').used,
            "free": psutil.disk_usage('/').free,
            "percent": psutil.disk_usage('/').percent
        },
        "network": psutil.net_io_counters()._asdict()
    }
    
    # GPU metrics if available
    try:
        gpus = GPUtil.getGPUs()
        if gpus:
            metrics["gpu"] = [{
                "id": gpu.id,
                "name": gpu.name,
                "load": gpu.load,
                "memory_used": gpu.memoryUsed,
                "memory_total": gpu.memoryTotal,
                "temperature": gpu.temperature
            } for gpu in gpus]
    except:
        pass
    
    return metrics
```

## Best Practices

1. **Structured Logging**: Always use JSON format for logs
2. **Correlation IDs**: Track requests across services
3. **Metric Naming**: Follow Prometheus naming conventions
4. **Alert Fatigue**: Avoid noisy alerts, tune thresholds
5. **Dashboard Organization**: Group by service and criticality
6. **Log Retention**: Implement lifecycle policies
7. **Sampling**: Use trace sampling for high-volume services
8. **Cost Optimization**: Monitor and optimize resource usage
9. **Security**: Encrypt metrics and logs in transit
10. **Documentation**: Document all custom metrics and alerts

## Summary

This monitoring and logging strategy provides:
- **Complete observability** with metrics, logs, and traces
- **Proactive alerting** for issues before they impact users
- **Performance insights** through APM and custom metrics
- **Cost visibility** for resource optimization
- **Debugging capabilities** with distributed tracing
- **Compliance** through comprehensive audit logging