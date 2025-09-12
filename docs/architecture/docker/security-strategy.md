# Container Security Strategy

## Overview

This document outlines our comprehensive security strategy for Docker containers and Kubernetes deployments, covering image security, runtime protection, secrets management, and compliance.

## Table of Contents

1. [Security Architecture](#security-architecture)
2. [Image Security](#image-security)
3. [Secret Management](#secret-management)
4. [Runtime Security](#runtime-security)
5. [Network Security](#network-security)
6. [Access Control](#access-control)
7. [Vulnerability Management](#vulnerability-management)
8. [Compliance and Auditing](#compliance-and-auditing)
9. [Incident Response](#incident-response)
10. [Security Best Practices](#security-best-practices)

## Security Architecture

### Defense in Depth Layers

```
┌─────────────────────────────────────────────┐
│          External Security (WAF)            │
├─────────────────────────────────────────────┤
│        Network Security (Firewall)          │
├─────────────────────────────────────────────┤
│     Ingress Controller (Rate Limiting)      │
├─────────────────────────────────────────────┤
│    Kubernetes Security (RBAC, PSP, NSP)     │
├─────────────────────────────────────────────┤
│     Container Security (Non-root, RO)       │
├─────────────────────────────────────────────┤
│      Image Security (Scanning, Sign)        │
├─────────────────────────────────────────────┤
│     Application Security (SAST, DAST)       │
└─────────────────────────────────────────────┘
```

### Security Components

```yaml
# Security Stack
Image Security:
  - Trivy (Vulnerability Scanning)
  - Cosign (Image Signing)
  - OPA (Policy Enforcement)

Runtime Security:
  - Falco (Runtime Detection)
  - SELinux/AppArmor (MAC)
  - Seccomp (System Call Filtering)

Network Security:
  - Calico (Network Policies)
  - Istio (Service Mesh)
  - Cert-Manager (TLS)

Access Control:
  - RBAC (Role-Based Access)
  - OIDC (Authentication)
  - Vault (Secrets Management)
```

## Image Security

### Secure Base Images

```dockerfile
# Dockerfile.secure
# Use specific version tags, never 'latest'
FROM python:3.11.6-slim-bookworm@sha256:abc123...

# Security labels
LABEL security.scan-date="2024-01-01"
LABEL security.vulnerability-count="0"
LABEL security.compliance="CIS-1.5.0"

# Create non-root user first
RUN groupadd -r -g 1000 ohlcv && \
    useradd -r -u 1000 -g ohlcv -s /sbin/nologin -c "OHLCV User" ohlcv

# Install security updates only
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Remove unnecessary tools
RUN find / -type f -perm /6000 -exec chmod a-s {} \; 2>/dev/null || true && \
    rm -rf /usr/bin/wget /usr/bin/curl /usr/bin/nc || true

# Set secure file permissions
RUN chmod 700 /home/ohlcv && \
    chown -R ohlcv:ohlcv /home/ohlcv

WORKDIR /app

# Copy with specific ownership
COPY --chown=ohlcv:ohlcv --chmod=755 src/ ./src/
COPY --chown=ohlcv:ohlcv --chmod=644 pyproject.toml ./

# Install dependencies as root, then switch
RUN pip install --no-cache-dir -r requirements.txt && \
    pip uninstall -y pip setuptools wheel && \
    rm -rf /root/.cache

# Security hardening
RUN echo "Umask 077" >> /etc/profile && \
    echo "readonly TMOUT=900" >> /etc/profile && \
    echo "export TMOUT" >> /etc/profile

# Switch to non-root user
USER ohlcv

# Read-only root filesystem
# Mount points for writable data
VOLUME ["/tmp", "/app/logs"]

# Health check without shell
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD ["/usr/local/bin/python", "-c", "import sys; import requests; sys.exit(0 if requests.get('http://localhost:8000/health').status_code == 200 else 1)"]

# Minimal entrypoint
ENTRYPOINT ["/usr/local/bin/python"]
CMD ["main.py"]

# Security metadata
ARG BUILD_DATE
ARG VCS_REF
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.revision="${VCS_REF}"
LABEL org.opencontainers.image.source="https://github.com/org/repo"
```

### Image Scanning Pipeline

```yaml
# .github/workflows/image-security.yml
name: Image Security Scan

on:
  push:
    paths:
      - 'Dockerfile*'
      - 'requirements*.txt'
      - 'pyproject.toml'

jobs:
  scan-image:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build image
        run: |
          docker build -t scan-target:latest -f Dockerfile.secure .
      
      - name: Run Trivy scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: scan-target:latest
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH,MEDIUM'
          exit-code: '1'
      
      - name: Run Grype scan
        run: |
          curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin
          grype scan-target:latest --fail-on medium -o json > grype-results.json
      
      - name: Run Snyk scan
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        run: |
          docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
            -v $(pwd):/project \
            -e SNYK_TOKEN \
            snyk/snyk:docker test scan-target:latest \
            --severity-threshold=medium \
            --json-file-output=/project/snyk-results.json
      
      - name: Check with OPA
        run: |
          docker run --rm -v $(pwd):/project \
            openpolicyagent/opa:latest-debug \
            eval -d /project/policies/docker.rego \
            -i /project/Dockerfile.secure \
            "data.docker.deny[msg]"
```

### Image Signing

```bash
#!/bin/bash
# scripts/sign-image.sh

# Install cosign
curl -O -L https://github.com/sigstore/cosign/releases/latest/download/cosign-linux-amd64
mv cosign-linux-amd64 /usr/local/bin/cosign
chmod +x /usr/local/bin/cosign

# Generate keys (one-time)
cosign generate-key-pair

# Sign image
IMAGE="${REGISTRY}/${IMAGE_NAME}:${TAG}"
cosign sign --key cosign.key "${IMAGE}"

# Verify signature
cosign verify --key cosign.pub "${IMAGE}"

# Sign with SBOM
syft packages "${IMAGE}" -o spdx-json > sbom.spdx.json
cosign attach sbom --sbom sbom.spdx.json "${IMAGE}"
cosign sign --key cosign.key --attachment sbom "${IMAGE}"

# Attest vulnerability scan
cosign attest --key cosign.key --type vuln --predicate vuln-report.json "${IMAGE}"
```

## Secret Management

### Kubernetes Secrets Configuration

```yaml
# secrets/sealed-secret.yaml
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: ohlcv-secrets
  namespace: ohlcv-system
spec:
  encryptedData:
    api-key: AgBvA7JqF5z...encrypted...data...
    db-password: AgCxM9KpL2w...encrypted...data...
  template:
    metadata:
      name: ohlcv-secrets
      namespace: ohlcv-system
    type: Opaque
```

### HashiCorp Vault Integration

```yaml
# vault/vault-injector.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ohlcv-rag
  namespace: ohlcv-system
spec:
  template:
    metadata:
      annotations:
        vault.hashicorp.com/agent-inject: "true"
        vault.hashicorp.com/role: "ohlcv-app"
        vault.hashicorp.com/agent-inject-secret-api-key: "secret/data/ohlcv/api-key"
        vault.hashicorp.com/agent-inject-template-api-key: |
          {{- with secret "secret/data/ohlcv/api-key" -}}
          export API_KEY="{{ .Data.data.value }}"
          {{- end }}
    spec:
      serviceAccountName: ohlcv-vault
      containers:
      - name: app
        image: ohlcv-rag:latest
        command: ["/bin/sh"]
        args: ["-c", "source /vault/secrets/api-key && python main.py"]
```

### Secret Rotation

```python
# secret_rotation.py
import os
import time
import boto3
from kubernetes import client, config
from datetime import datetime, timedelta

class SecretRotator:
    def __init__(self):
        config.load_incluster_config()
        self.k8s_client = client.CoreV1Api()
        self.secrets_manager = boto3.client('secretsmanager')
        
    def rotate_secret(self, secret_name: str, namespace: str):
        """Rotate a secret in Kubernetes"""
        # Generate new secret value
        new_secret = self.generate_secret()
        
        # Update in AWS Secrets Manager
        self.secrets_manager.update_secret(
            SecretId=secret_name,
            SecretString=new_secret
        )
        
        # Update in Kubernetes
        body = client.V1Secret(
            metadata=client.V1ObjectMeta(name=secret_name),
            data={
                'value': base64.b64encode(new_secret.encode()).decode()
            }
        )
        
        self.k8s_client.patch_namespaced_secret(
            name=secret_name,
            namespace=namespace,
            body=body
        )
        
        # Trigger pod restart for new secret
        self.restart_pods(namespace, secret_name)
        
    def generate_secret(self, length=32):
        """Generate cryptographically secure secret"""
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits + string.punctuation
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def restart_pods(self, namespace: str, secret_name: str):
        """Rolling restart of pods using the secret"""
        deployments = self.k8s_client.list_namespaced_deployment(namespace)
        
        for deployment in deployments.items:
            # Check if deployment uses this secret
            if self.uses_secret(deployment, secret_name):
                # Trigger rolling restart
                deployment.spec.template.metadata.annotations = {
                    'kubectl.kubernetes.io/restartedAt': datetime.now().isoformat()
                }
                
                apps_api = client.AppsV1Api()
                apps_api.patch_namespaced_deployment(
                    name=deployment.metadata.name,
                    namespace=namespace,
                    body=deployment
                )
```

## Runtime Security

### Security Context

```yaml
# security/pod-security.yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
  namespace: ohlcv-system
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
    fsGroupChangePolicy: "OnRootMismatch"
    seccompProfile:
      type: RuntimeDefault
    supplementalGroups: [1000]
  
  containers:
  - name: app
    image: ohlcv-rag:latest
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop:
          - ALL
        add:
          - NET_BIND_SERVICE  # Only if needed
      privileged: false
      readOnlyRootFilesystem: true
      runAsNonRoot: true
      runAsUser: 1000
      runAsGroup: 1000
      seLinuxOptions:
        level: "s0:c123,c456"
    
    volumeMounts:
    - name: tmp
      mountPath: /tmp
    - name: cache
      mountPath: /app/.cache
    - name: logs
      mountPath: /app/logs
  
  volumes:
  - name: tmp
    emptyDir:
      medium: Memory
      sizeLimit: 100Mi
  - name: cache
    emptyDir:
      sizeLimit: 500Mi
  - name: logs
    emptyDir:
      sizeLimit: 1Gi
```

### Falco Runtime Detection

```yaml
# falco/falco-rules.yaml
- rule: Unexpected Network Connection
  desc: Detect unexpected network connections from containers
  condition: >
    container and 
    outbound and 
    not (container.image.repository in (allowed_images)) and
    not (fd.sip in (allowed_ips))
  output: >
    Unexpected network connection 
    (container=%container.name image=%container.image.repository 
    connection=%fd.name user=%user.name)
  priority: WARNING
  tags: [network, container]

- rule: Write to System Directory
  desc: Detect writes to system directories
  condition: >
    container and 
    write and 
    (fd.name startswith /bin or 
     fd.name startswith /sbin or 
     fd.name startswith /usr/bin or 
     fd.name startswith /usr/sbin)
  output: >
    Write to system directory 
    (container=%container.name file=%fd.name user=%user.name)
  priority: ERROR
  tags: [filesystem, container]

- rule: Spawned Shell in Container
  desc: Detect shell spawned in container
  condition: >
    container and 
    spawned_process and 
    shell_procs and 
    not container.image.repository in (debug_images)
  output: >
    Shell spawned in container 
    (container=%container.name image=%container.image.repository 
    shell=%proc.name user=%user.name)
  priority: WARNING
  tags: [process, container]
```

### AppArmor Profile

```
# /etc/apparmor.d/ohlcv-container
#include <tunables/global>

profile ohlcv-container flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>

  # Deny all network access
  deny network,
  
  # Allow specific network access
  network inet tcp,
  network inet6 tcp,
  
  # File access
  /usr/local/bin/python* ix,
  /app/ r,
  /app/** r,
  /tmp/ rw,
  /tmp/** rw,
  /app/logs/ rw,
  /app/logs/** rw,
  
  # Deny sensitive file access
  deny /etc/shadow r,
  deny /etc/passwd w,
  deny /root/** rwx,
  deny /home/** rwx,
  
  # Capabilities
  capability net_bind_service,
  capability setuid,
  capability setgid,
  
  # Deny other capabilities
  deny capability sys_admin,
  deny capability sys_module,
  deny capability sys_ptrace,
}
```

## Network Security

### Network Policies

```yaml
# network/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ohlcv-network-policy
  namespace: ohlcv-system
spec:
  podSelector:
    matchLabels:
      app: ohlcv-rag
  policyTypes:
  - Ingress
  - Egress
  
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    - podSelector:
        matchLabels:
          app: prometheus
    ports:
    - protocol: TCP
      port: 8000
    - protocol: TCP
      port: 9090  # Metrics
  
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: ohlcv-system
      podSelector:
        matchLabels:
          app: chromadb
    ports:
    - protocol: TCP
      port: 8000
  
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - protocol: UDP
      port: 53
  
  # Allow external HTTPS only
  - to:
    - podSelector: {}
    ports:
    - protocol: TCP
      port: 443
```

### Service Mesh Security (Istio)

```yaml
# istio/authorization-policy.yaml
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: ohlcv-authz
  namespace: ohlcv-system
spec:
  selector:
    matchLabels:
      app: ohlcv-rag
  action: ALLOW
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/ingress-nginx/sa/ingress-nginx"]
    to:
    - operation:
        methods: ["GET", "POST"]
        paths: ["/api/*"]
    when:
    - key: request.headers[authorization]
      values: ["Bearer *"]

---
# istio/peer-authentication.yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: ohlcv-mtls
  namespace: ohlcv-system
spec:
  selector:
    matchLabels:
      app: ohlcv-rag
  mtls:
    mode: STRICT
```

## Access Control

### RBAC Configuration

```yaml
# rbac/rbac.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ohlcv-sa
  namespace: ohlcv-system

---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: ohlcv-role
  namespace: ohlcv-system
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["secrets"]
  resourceNames: ["ohlcv-secrets"]
  verbs: ["get"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: ohlcv-rolebinding
  namespace: ohlcv-system
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: ohlcv-role
subjects:
- kind: ServiceAccount
  name: ohlcv-sa
  namespace: ohlcv-system

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: ohlcv-cluster-role
rules:
- apiGroups: [""]
  resources: ["nodes", "namespaces"]
  verbs: ["get", "list"]
- apiGroups: ["metrics.k8s.io"]
  resources: ["pods"]
  verbs: ["get", "list"]
```

### Pod Security Standards

```yaml
# security/pod-security-standard.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ohlcv-system
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted

---
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: ohlcv-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  hostNetwork: false
  hostIPC: false
  hostPID: false
  runAsUser:
    rule: 'MustRunAsNonRoot'
  runAsGroup:
    rule: 'MustRunAs'
    ranges:
      - min: 1000
        max: 65535
  seLinux:
    rule: 'RunAsAny'
  supplementalGroups:
    rule: 'MustRunAs'
    ranges:
      - min: 1000
        max: 65535
  fsGroup:
    rule: 'MustRunAs'
    ranges:
      - min: 1000
        max: 65535
  readOnlyRootFilesystem: true
```

## Vulnerability Management

### Automated Patching

```yaml
# .github/workflows/security-patch.yml
name: Security Patching

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  patch-dependencies:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Update Python dependencies
        run: |
          uv lock --upgrade
          uv sync --frozen
      
      - name: Security audit
        run: |
          pip-audit --fix --desc
          safety check --json
      
      - name: Create PR if changes
        uses: peter-evans/create-pull-request@v5
        with:
          commit-message: 'chore: security patches for dependencies'
          title: '[Security] Automated dependency updates'
          body: |
            ## Security Patches
            
            This PR contains automated security patches for dependencies.
            
            ### Changes
            - Updated vulnerable dependencies
            - Applied security patches
            
            ### Testing
            - [ ] All tests pass
            - [ ] Security scans pass
          branch: security-patches-${{ github.run_number }}
          labels: security, automated
```

### CVE Tracking

```python
# security/cve_tracker.py
import requests
from typing import List, Dict
import json

class CVETracker:
    def __init__(self):
        self.nvd_api = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        self.tracked_components = [
            "python",
            "docker",
            "kubernetes",
            "chromadb",
            "langchain"
        ]
    
    def check_cves(self) -> List[Dict]:
        """Check for new CVEs affecting our components"""
        cves = []
        
        for component in self.tracked_components:
            response = requests.get(
                self.nvd_api,
                params={
                    "keywordSearch": component,
                    "resultsPerPage": 10
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                for vulnerability in data.get("vulnerabilities", []):
                    cve = vulnerability.get("cve", {})
                    cves.append({
                        "id": cve.get("id"),
                        "description": cve.get("descriptions", [{}])[0].get("value"),
                        "severity": self.get_severity(cve),
                        "component": component
                    })
        
        return cves
    
    def get_severity(self, cve: Dict) -> str:
        """Extract CVE severity"""
        metrics = cve.get("metrics", {})
        cvss = metrics.get("cvssMetricV31", [{}])[0]
        score = cvss.get("cvssData", {}).get("baseScore", 0)
        
        if score >= 9.0:
            return "CRITICAL"
        elif score >= 7.0:
            return "HIGH"
        elif score >= 4.0:
            return "MEDIUM"
        else:
            return "LOW"
```

## Compliance and Auditing

### Compliance Checks

```yaml
# compliance/cis-benchmark.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cis-benchmark
  namespace: ohlcv-system
data:
  checks.yaml: |
    checks:
      - id: 5.1.1
        description: "Ensure that the cluster-admin role is only used where required"
        audit: "kubectl get clusterrolebindings -o json | jq '.items[] | select(.roleRef.name==\"cluster-admin\")'"
        remediation: "Remove unnecessary cluster-admin bindings"
      
      - id: 5.1.2
        description: "Minimize wildcard use in Roles and ClusterRoles"
        audit: "kubectl get roles,clusterroles -A -o yaml | grep -E '\\*'"
        remediation: "Replace wildcards with specific resources"
      
      - id: 5.2.1
        description: "Ensure that the pod security policy is enabled"
        audit: "kubectl get psp"
        remediation: "Enable and configure PodSecurityPolicy"
      
      - id: 5.3.1
        description: "Ensure that all namespaces have NetworkPolicy"
        audit: "kubectl get networkpolicy -A"
        remediation: "Create NetworkPolicy for each namespace"
```

### Audit Logging

```python
# audit/audit_logger.py
import json
import hashlib
import time
from datetime import datetime
from typing import Dict, Any

class AuditLogger:
    def __init__(self, output_file="/var/log/audit/security.log"):
        self.output_file = output_file
        
    def log_event(self, event_type: str, details: Dict[str, Any]):
        """Log security event with integrity protection"""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "details": details,
            "user": self.get_user_context(),
            "environment": self.get_environment_context()
        }
        
        # Add integrity hash
        event["hash"] = self.calculate_hash(event)
        
        # Write to audit log
        with open(self.output_file, 'a') as f:
            f.write(json.dumps(event) + "\n")
        
        # Send to SIEM if configured
        self.send_to_siem(event)
    
    def calculate_hash(self, event: Dict) -> str:
        """Calculate integrity hash for event"""
        event_str = json.dumps(event, sort_keys=True)
        return hashlib.sha256(event_str.encode()).hexdigest()
    
    def get_user_context(self) -> Dict:
        """Get current user context"""
        import os
        return {
            "uid": os.getuid(),
            "gid": os.getgid(),
            "username": os.environ.get("USER", "unknown"),
            "groups": os.getgroups()
        }
    
    def get_environment_context(self) -> Dict:
        """Get environment context"""
        import os
        return {
            "hostname": os.environ.get("HOSTNAME", "unknown"),
            "pod_name": os.environ.get("POD_NAME", "unknown"),
            "namespace": os.environ.get("POD_NAMESPACE", "unknown"),
            "container": os.environ.get("CONTAINER_NAME", "unknown")
        }
    
    def send_to_siem(self, event: Dict):
        """Send event to SIEM system"""
        # Implementation for specific SIEM
        pass

# Usage
audit = AuditLogger()

# Log security events
audit.log_event("authentication", {
    "action": "login",
    "result": "success",
    "method": "oauth2"
})

audit.log_event("authorization", {
    "action": "access_resource",
    "resource": "/api/sensitive",
    "result": "denied",
    "reason": "insufficient_privileges"
})

audit.log_event("data_access", {
    "action": "read",
    "resource": "customer_data",
    "records": 100
})
```

## Incident Response

### Incident Response Plan

```yaml
# incident/response-plan.yaml
incident_response:
  detection:
    sources:
      - Falco alerts
      - Prometheus alerts
      - Security scans
      - Audit logs
    
  classification:
    severity_levels:
      critical:
        description: "Active exploitation or data breach"
        response_time: "15 minutes"
        escalation: "immediate"
      
      high:
        description: "Vulnerability with exploit available"
        response_time: "1 hour"
        escalation: "within 2 hours"
      
      medium:
        description: "Security misconfiguration"
        response_time: "4 hours"
        escalation: "within 24 hours"
      
      low:
        description: "Minor security issue"
        response_time: "24 hours"
        escalation: "within 72 hours"
  
  response_steps:
    1_contain:
      - Isolate affected containers
      - Block malicious IPs
      - Revoke compromised credentials
    
    2_investigate:
      - Collect logs and evidence
      - Analyze attack vector
      - Identify scope of breach
    
    3_eradicate:
      - Remove malware/backdoors
      - Patch vulnerabilities
      - Update security controls
    
    4_recover:
      - Restore from clean backups
      - Rebuild affected systems
      - Verify system integrity
    
    5_lessons_learned:
      - Document incident
      - Update response procedures
      - Implement preventive measures
```

### Automated Response

```python
# incident/auto_response.py
import kubernetes
from typing import Dict, List

class IncidentResponder:
    def __init__(self):
        kubernetes.config.load_incluster_config()
        self.v1 = kubernetes.client.CoreV1Api()
        self.apps_v1 = kubernetes.client.AppsV1Api()
    
    def isolate_pod(self, namespace: str, pod_name: str):
        """Isolate a compromised pod"""
        # Add network policy to block all traffic
        network_policy = {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "NetworkPolicy",
            "metadata": {
                "name": f"isolate-{pod_name}",
                "namespace": namespace
            },
            "spec": {
                "podSelector": {
                    "matchLabels": {
                        "name": pod_name
                    }
                },
                "policyTypes": ["Ingress", "Egress"]
            }
        }
        
        # Apply network policy
        kubernetes.client.NetworkingV1Api().create_namespaced_network_policy(
            namespace=namespace,
            body=network_policy
        )
        
        # Label pod as compromised
        self.v1.patch_namespaced_pod(
            name=pod_name,
            namespace=namespace,
            body={"metadata": {"labels": {"security-status": "compromised"}}}
        )
    
    def kill_pod(self, namespace: str, pod_name: str):
        """Terminate a compromised pod"""
        self.v1.delete_namespaced_pod(
            name=pod_name,
            namespace=namespace,
            grace_period_seconds=0
        )
    
    def scale_down_deployment(self, namespace: str, deployment_name: str):
        """Scale down compromised deployment"""
        self.apps_v1.patch_namespaced_deployment_scale(
            name=deployment_name,
            namespace=namespace,
            body={"spec": {"replicas": 0}}
        )
    
    def block_ip(self, ip_address: str):
        """Block malicious IP address"""
        # Implementation depends on ingress controller
        pass
    
    def revoke_service_account(self, namespace: str, sa_name: str):
        """Revoke compromised service account"""
        # Delete service account token secrets
        secrets = self.v1.list_namespaced_secret(namespace)
        for secret in secrets.items:
            if secret.metadata.annotations and \
               secret.metadata.annotations.get("kubernetes.io/service-account.name") == sa_name:
                self.v1.delete_namespaced_secret(
                    name=secret.metadata.name,
                    namespace=namespace
                )
```

## Security Best Practices

### Container Security Checklist

```yaml
# Security Checklist
Image Security:
  ✓ Use specific version tags, not 'latest'
  ✓ Scan images for vulnerabilities
  ✓ Sign and verify images
  ✓ Use minimal base images (distroless/scratch)
  ✓ Remove unnecessary packages and tools
  ✓ Don't include secrets in images

Runtime Security:
  ✓ Run as non-root user
  ✓ Use read-only root filesystem
  ✓ Drop all capabilities by default
  ✓ Use security profiles (AppArmor/SELinux)
  ✓ Implement resource limits
  ✓ Use network policies

Secret Management:
  ✓ Never hardcode secrets
  ✓ Use external secret management
  ✓ Rotate secrets regularly
  ✓ Encrypt secrets at rest
  ✓ Limit secret access with RBAC
  ✓ Audit secret access

Access Control:
  ✓ Implement RBAC with least privilege
  ✓ Use service accounts
  ✓ Enable audit logging
  ✓ Implement MFA for admin access
  ✓ Regular access reviews
  ✓ Time-bound access tokens

Monitoring:
  ✓ Enable security monitoring
  ✓ Set up alerting for anomalies
  ✓ Log all security events
  ✓ Regular vulnerability scans
  ✓ Implement intrusion detection
  ✓ Monitor for compliance

Incident Response:
  ✓ Have response plan ready
  ✓ Regular drills and training
  ✓ Automated response for common threats
  ✓ Evidence collection procedures
  ✓ Communication protocols
  ✓ Post-incident reviews
```

## Summary

This security strategy provides:
- **Defense in depth** with multiple security layers
- **Zero-trust architecture** with strict access controls
- **Automated security** scanning and patching
- **Runtime protection** with monitoring and detection
- **Compliance support** for various standards
- **Incident response** capabilities for quick remediation
- **Best practices** implementation throughout the stack