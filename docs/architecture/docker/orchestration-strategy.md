# Container Orchestration Strategy

## Overview

This document details our container orchestration strategy for the OHLCV RAG System, covering deployment patterns, scaling configurations, and production orchestration using Docker Swarm and Kubernetes.

## Table of Contents

1. [Orchestration Platform Selection](#orchestration-platform-selection)
2. [Docker Swarm Configuration](#docker-swarm-configuration)
3. [Kubernetes Deployment](#kubernetes-deployment)
4. [Service Discovery and Load Balancing](#service-discovery-and-load-balancing)
5. [Auto-scaling Strategy](#auto-scaling-strategy)
6. [Rolling Updates and Rollbacks](#rolling-updates-and-rollbacks)
7. [High Availability Configuration](#high-availability-configuration)
8. [Resource Management](#resource-management)

## Orchestration Platform Selection

### Decision Matrix

| Feature | Docker Swarm | Kubernetes | Docker Compose | Our Choice |
|---------|--------------|------------|----------------|------------|
| **Complexity** | Low | High | Minimal | Swarm for simple, K8s for scale |
| **Learning Curve** | Easy | Steep | Very Easy | Start with Swarm |
| **Scalability** | Good | Excellent | Limited | K8s for >10 nodes |
| **Community** | Smaller | Huge | Large | K8s for long-term |
| **Built-in Features** | Basic | Extensive | Minimal | K8s for advanced |

### Implementation Strategy

```yaml
# Progressive adoption path
Development: Docker Compose
Staging: Docker Swarm
Production (Small): Docker Swarm
Production (Large): Kubernetes
```

## Docker Swarm Configuration

### Initialize Swarm Cluster

```bash
# Initialize swarm on manager node
docker swarm init --advertise-addr 10.0.0.1

# Join worker nodes
docker swarm join --token SWMTKN-1-xxx 10.0.0.1:2377

# Verify cluster
docker node ls
```

### Stack Deployment

```yaml
# docker-stack.yml
version: '3.9'

services:
  app:
    image: ohlcv-rag:latest
    deploy:
      replicas: 3
      placement:
        constraints:
          - node.role == worker
          - node.labels.type == compute
        preferences:
          - spread: node.labels.zone
      update_config:
        parallelism: 1
        delay: 30s
        failure_action: rollback
        monitor: 60s
        max_failure_ratio: 0.3
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
        window: 120s
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
      labels:
        - "traefik.enable=true"
        - "traefik.http.routers.app.rule=Host(`api.ohlcv.example.com`)"
        - "traefik.http.services.app.loadbalancer.server.port=8000"
    networks:
      - ohlcv-network
    secrets:
      - api_key
      - db_password
    configs:
      - source: app_config
        target: /app/config.json
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  chromadb:
    image: chromadb/chroma:latest
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.labels.type == storage
      endpoint_mode: dnsrr
    volumes:
      - type: volume
        source: chromadb-data
        target: /chroma/chroma
        volume:
          nocopy: true
    networks:
      - ohlcv-network

  load-balancer:
    image: traefik:v2.10
    deploy:
      placement:
        constraints:
          - node.role == manager
      labels:
        - "traefik.enable=true"
        - "traefik.http.routers.api.rule=Host(`traefik.ohlcv.example.com`)"
        - "traefik.http.routers.api.service=api@internal"
    ports:
      - target: 80
        published: 80
        mode: host
      - target: 443
        published: 443
        mode: host
      - target: 8080
        published: 8080
        mode: ingress
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - traefik-certs:/certs
    networks:
      - ohlcv-network

networks:
  ohlcv-network:
    driver: overlay
    attachable: true
    encrypted: true
    driver_opts:
      encrypted: "true"
      com.docker.network.driver.mtu: 1450

volumes:
  chromadb-data:
    driver: local
    driver_opts:
      type: nfs
      o: addr=nfs-server.local,vers=4,soft,timeo=180,retrans=2
      device: ":/data/chromadb"
  
  traefik-certs:
    driver: local

secrets:
  api_key:
    external: true
    name: ohlcv_api_key_v1
  
  db_password:
    external: true
    name: ohlcv_db_pass_v1

configs:
  app_config:
    file: ./configs/app.json
    name: ohlcv_config_v1
```

### Deploy Stack

```bash
# Deploy stack
docker stack deploy -c docker-stack.yml ohlcv

# Check services
docker service ls
docker service ps ohlcv_app

# Scale service
docker service scale ohlcv_app=5

# Update service
docker service update --image ohlcv-rag:v2 ohlcv_app

# Rolling restart
docker service update --force ohlcv_app
```

## Kubernetes Deployment

### Namespace and ConfigMap

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ohlcv-system
  labels:
    name: ohlcv-system
    environment: production

---
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ohlcv-config
  namespace: ohlcv-system
data:
  LOG_LEVEL: "INFO"
  DATA_SOURCE: "yahoo"
  VECTOR_STORE_TYPE: "chromadb"
  CHROMADB_HOST: "chromadb-service"
  CHROMADB_PORT: "8000"
```

### Deployment Configuration

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ohlcv-rag
  namespace: ohlcv-system
  labels:
    app: ohlcv-rag
    version: v1
spec:
  replicas: 3
  revisionHistoryLimit: 10
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
        version: v1
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9090"
        prometheus.io/path: "/metrics"
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - ohlcv-rag
              topologyKey: kubernetes.io/hostname
      
      initContainers:
      - name: wait-for-chromadb
        image: busybox:1.35
        command: ['sh', '-c', 'until nc -z chromadb-service 8000; do echo waiting for chromadb; sleep 2; done']
      
      containers:
      - name: app
        image: ohlcv-rag:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
          name: http
          protocol: TCP
        - containerPort: 9090
          name: metrics
          protocol: TCP
        
        envFrom:
        - configMapRef:
            name: ohlcv-config
        
        env:
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: POD_NAMESPACE
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
        - name: API_KEY
          valueFrom:
            secretKeyRef:
              name: ohlcv-secrets
              key: api-key
        
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
            ephemeral-storage: "1Gi"
          limits:
            memory: "2Gi"
            cpu: "2000m"
            ephemeral-storage: "5Gi"
        
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
            scheme: HTTP
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          successThreshold: 1
          failureThreshold: 3
        
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
            scheme: HTTP
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          successThreshold: 1
          failureThreshold: 3
        
        startupProbe:
          httpGet:
            path: /startup
            port: 8000
          initialDelaySeconds: 0
          periodSeconds: 10
          timeoutSeconds: 3
          successThreshold: 1
          failureThreshold: 30
        
        volumeMounts:
        - name: data
          mountPath: /data
        - name: cache
          mountPath: /app/.cache
        - name: tmp
          mountPath: /tmp
      
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: ohlcv-data-pvc
      - name: cache
        emptyDir:
          sizeLimit: 1Gi
      - name: tmp
        emptyDir:
          medium: Memory
          sizeLimit: 500Mi
```

### Service Configuration

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: ohlcv-service
  namespace: ohlcv-system
  labels:
    app: ohlcv-rag
spec:
  type: ClusterIP
  selector:
    app: ohlcv-rag
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
    name: http
  - port: 9090
    targetPort: 9090
    protocol: TCP
    name: metrics
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 10800

---
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ohlcv-ingress
  namespace: ohlcv-system
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.ohlcv.example.com
    secretName: ohlcv-tls
  rules:
  - host: api.ohlcv.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ohlcv-service
            port:
              number: 80
```

## Service Discovery and Load Balancing

### Internal Service Discovery

```yaml
# headless-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: ohlcv-headless
  namespace: ohlcv-system
spec:
  clusterIP: None
  selector:
    app: ohlcv-rag
  ports:
  - port: 8000
    targetPort: 8000
```

### External Load Balancer

```yaml
# loadbalancer.yaml
apiVersion: v1
kind: Service
metadata:
  name: ohlcv-lb
  namespace: ohlcv-system
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
    service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled: "true"
spec:
  type: LoadBalancer
  selector:
    app: ohlcv-rag
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
  externalTrafficPolicy: Local
```

## Auto-scaling Strategy

### Horizontal Pod Autoscaler

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ohlcv-hpa
  namespace: ohlcv-system
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ohlcv-rag
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
      - type: Pods
        value: 2
        periodSeconds: 60
      selectPolicy: Min
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
      - type: Pods
        value: 4
        periodSeconds: 30
      selectPolicy: Max
```

### Vertical Pod Autoscaler

```yaml
# vpa.yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: ohlcv-vpa
  namespace: ohlcv-system
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ohlcv-rag
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: app
      minAllowed:
        cpu: 250m
        memory: 256Mi
      maxAllowed:
        cpu: 4
        memory: 4Gi
      controlledResources: ["cpu", "memory"]
```

## Rolling Updates and Rollbacks

### Update Strategy

```yaml
# deployment-update.yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%        # Max pods above desired replicas
      maxUnavailable: 0    # No downtime during update
```

### Rollback Procedure

```bash
# Check rollout status
kubectl rollout status deployment/ohlcv-rag -n ohlcv-system

# View rollout history
kubectl rollout history deployment/ohlcv-rag -n ohlcv-system

# Rollback to previous version
kubectl rollout undo deployment/ohlcv-rag -n ohlcv-system

# Rollback to specific revision
kubectl rollout undo deployment/ohlcv-rag --to-revision=2 -n ohlcv-system

# Pause rollout
kubectl rollout pause deployment/ohlcv-rag -n ohlcv-system

# Resume rollout
kubectl rollout resume deployment/ohlcv-rag -n ohlcv-system
```

## High Availability Configuration

### Multi-Zone Deployment

```yaml
# statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: ohlcv-stateful
  namespace: ohlcv-system
spec:
  serviceName: ohlcv-headless
  replicas: 3
  podManagementPolicy: Parallel
  updateStrategy:
    type: RollingUpdate
  selector:
    matchLabels:
      app: ohlcv-stateful
  template:
    metadata:
      labels:
        app: ohlcv-stateful
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: app
                operator: In
                values:
                - ohlcv-stateful
            topologyKey: topology.kubernetes.io/zone
      containers:
      - name: app
        image: ohlcv-rag:latest
        volumeMounts:
        - name: data
          mountPath: /data
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: "fast-ssd"
      resources:
        requests:
          storage: 10Gi
```

### Pod Disruption Budget

```yaml
# pdb.yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: ohlcv-pdb
  namespace: ohlcv-system
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: ohlcv-rag
  unhealthyPodEvictionPolicy: IfHealthyBudget
```

## Resource Management

### Resource Quotas

```yaml
# resource-quota.yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: ohlcv-quota
  namespace: ohlcv-system
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 20Gi
    limits.cpu: "20"
    limits.memory: 40Gi
    persistentvolumeclaims: "10"
    services.loadbalancers: "2"
```

### Limit Ranges

```yaml
# limit-range.yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: ohlcv-limits
  namespace: ohlcv-system
spec:
  limits:
  - max:
      cpu: "4"
      memory: "4Gi"
    min:
      cpu: "100m"
      memory: "128Mi"
    default:
      cpu: "1"
      memory: "1Gi"
    defaultRequest:
      cpu: "500m"
      memory: "512Mi"
    type: Container
  - max:
      storage: "100Gi"
    min:
      storage: "1Gi"
    type: PersistentVolumeClaim
```

## Monitoring Integration

```yaml
# servicemonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: ohlcv-metrics
  namespace: ohlcv-system
spec:
  selector:
    matchLabels:
      app: ohlcv-rag
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
```

## Best Practices

1. **Start Simple**: Begin with Docker Swarm for <5 nodes
2. **Use Health Checks**: Define comprehensive health probes
3. **Resource Limits**: Always set resource requests and limits
4. **Anti-affinity Rules**: Spread pods across nodes/zones
5. **PodDisruptionBudgets**: Maintain availability during updates
6. **Gradual Rollouts**: Use conservative update strategies
7. **Monitoring**: Integrate metrics from day one
8. **Secrets Management**: Never hardcode sensitive data
9. **Network Policies**: Implement least-privilege networking
10. **Regular Backups**: Backup stateful components

## Summary

This orchestration strategy provides:
- **Production-ready** deployment configurations
- **High availability** with multi-zone support
- **Auto-scaling** based on metrics
- **Zero-downtime** updates
- **Resource management** and quotas
- **Service discovery** and load balancing
- **Progressive adoption** path from Swarm to Kubernetes