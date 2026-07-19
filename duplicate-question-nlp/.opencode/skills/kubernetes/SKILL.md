---
name: kubernetes
description: Use when orchestrating containers with Kubernetes. Covers pods, deployments, services, ingress, configmaps, and Helm.
---

# Kubernetes Skill

## Instructions

Kubernetes (K8s) is an open-source container orchestration platform that automates the deployment, scaling, and management of containerized applications. This skill covers core Kubernetes concepts including Pods, Deployments, Services, Ingress, ConfigMaps, Secrets, and Helm chart management.

### Core Concepts

Kubernetes operates on a declarative model: you specify the desired state of your application in YAML or JSON manifests, and Kubernetes works to maintain that state.

**Control Plane Components:**
- **kube-apiserver**: API gateway for all cluster operations
- **etcd**: Distributed key-value store for cluster state
- **kube-scheduler**: Assigns Pods to nodes
- **kube-controller-manager**: Runs controller processes
- **cloud-controller-manager**: Integrates with cloud provider APIs

**Node Components:**
- **kubelet**: Agent that runs on each node
- **kube-proxy**: Network proxy for service abstraction
- **Container runtime**: Docker, containerd, or CRI-O

### Pods

A Pod is the smallest deployable unit in Kubernetes, representing one or more containers with shared storage and network:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
  labels:
    app: myapp
spec:
  containers:
    - name: app
      image: myapp:1.0.0
      ports:
        - containerPort: 8080
      resources:
        requests:
          memory: "256Mi"
          cpu: "250m"
        limits:
          memory: "512Mi"
          cpu: "500m"
```

### Deployments

Deployments manage ReplicaSets and provide declarative updates for Pods:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
        - name: app
          image: myapp:1.0.0
          ports:
            - containerPort: 8080
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
```

### Services

Services provide stable networking and load balancing for Pods:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp-service
spec:
  type: ClusterIP
  selector:
    app: myapp
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8080
```

Service types:
- **ClusterIP**: Internal cluster IP (default)
- **NodePort**: Expose on each node's IP at a static port
- **LoadBalancer**: Cloud provider load balancer
- **ExternalName**: DNS CNAME record

### Ingress

Ingress exposes HTTP/HTTPS routes from outside the cluster to Services:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
    - hosts:
        - app.example.com
      secretName: app-tls
  rules:
    - host: app.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: myapp-service
                port:
                  number: 80
```

### ConfigMaps and Secrets

ConfigMaps store non-sensitive configuration data; Secrets store sensitive data:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  NODE_ENV: production
  LOG_LEVEL: info
  API_URL: https://api.example.com

---
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
stringData:
  DB_PASSWORD: supersecretpassword
  API_KEY: abc123def456
```

## Examples

### Example 1: Complete Application Stack

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  app.properties: |
    app.name=myapp
    app.version=1.0.0
    app.environment=production

---
# secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
stringData:
  database-url: postgresql://user:pass@postgres:5432/mydb
  redis-password: redispass

---
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  labels:
    app: api
    version: "1.0.0"
spec:
  replicas: 3
  revisionHistoryLimit: 3
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
        version: "1.0.0"
    spec:
      containers:
        - name: api
          image: myregistry.azurecr.io/api:1.0.0
          imagePullPolicy: Always
          ports:
            - containerPort: 3000
              protocol: TCP
          envFrom:
            - configMapRef:
                name: app-config
            - secretRef:
                name: app-secrets
          env:
            - name: POD_NAME
              valueFrom:
                fieldRef:
                  fieldPath: metadata.name
          resources:
            requests:
              cpu: "250m"
              memory: "256Mi"
            limits:
              cpu: "500m"
              memory: "512Mi"
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 3000
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /health/live
              port: 3000
            initialDelaySeconds: 15
            periodSeconds: 20
          volumeMounts:
            - name: config
              mountPath: /etc/config
      volumes:
        - name: config
          configMap:
            name: app-config

---
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: api
spec:
  type: ClusterIP
  selector:
    app: api
  ports:
    - name: http
      port: 80
      targetPort: 3000

---
# hpa.yaml (Horizontal Pod Autoscaler)
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  minReplicas: 3
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
```

### Example 2: StatefulSet for PostgreSQL

```yaml
apiVersion: v1
kind: Service
metadata:
  name: postgres
  labels:
    app: postgres
spec:
  type: ClusterIP
  clusterIP: None  # Headless service for StatefulSet
  selector:
    app: postgres
  ports:
    - port: 5432
      targetPort: 5432

---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
spec:
  serviceName: postgres
  replicas: 3
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: postgres:16-alpine
          ports:
            - containerPort: 5432
          env:
            - name: POSTGRES_DB
              value: myapp
            - name: POSTGRES_USER
              value: appuser
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: password
          volumeMounts:
            - name: postgres-data
              mountPath: /var/lib/postgresql/data
              subPath: postgres
  volumeClaimTemplates:
    - metadata:
        name: postgres-data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 50Gi
        storageClassName: standard
```

### Example 3: Canary Deployment with Ingress

```yaml
# Primary deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-stable
spec:
  replicas: 9
  selector:
    matchLabels:
      app: myapp
      track: stable
  template:
    metadata:
      labels:
        app: myapp
        track: stable
    spec:
      containers:
        - name: app
          image: myapp:1.0.0

---
# Canary deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-canary
spec:
  replicas: 1
  selector:
    matchLabels:
      app: myapp
      track: canary
  template:
    metadata:
      labels:
        app: myapp
        track: canary
    spec:
      containers:
        - name: app
          image: myapp:2.0.0-rc.1

---
# Service targets all instances
apiVersion: v1
kind: Service
metadata:
  name: myapp
spec:
  selector:
    app: myapp
  ports:
    - port: 80
      targetPort: 3000
```

### Example 4: Job and CronJob

```yaml
# One-time job
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migration
spec:
  ttlSecondsAfterFinished: 86400  # Clean up after 24 hours
  backoffLimit: 3
  activeDeadlineSeconds: 300  # Timeout after 5 minutes
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: migration
          image: myapp:1.0.0
          command: ["npm", "run", "migrate"]
          envFrom:
            - secretRef:
                name: app-secrets

---
# Scheduled job
apiVersion: batch/v1
kind: CronJob
metadata:
  name: cleanup-job
spec:
  schedule: "0 3 * * *"  # Daily at 3 AM
  concurrencyPolicy: Forbid  # Don't run if previous is still running
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: cleanup
              image: myapp:1.0.0
              command: ["node", "scripts/cleanup.js"]
          restartPolicy: OnFailure
```

### Example 5: Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-network-policy
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: ingress-gateway
        - namespaceSelector:
            matchLabels:
              name: monitoring
      ports:
        - protocol: TCP
          port: 3000
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: database
      ports:
        - protocol: TCP
          port: 5432
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0
            except:
              - 10.0.0.0/8
              - 172.16.0.0/12
              - 192.168.0.0/16
```

### Example 6: Helm Chart Structure

```yaml
# Chart.yaml
apiVersion: v2
name: myapp
description: A Helm chart for deploying myapp on Kubernetes
type: application
version: 0.1.0
appVersion: "1.0.0"
dependencies:
  - name: postgresql
    version: 12.x.x
    repository: https://charts.bitnami.com/bitnami
    condition: postgresql.enabled

# values.yaml
replicaCount: 3
image:
  repository: myregistry/myapp
  tag: "1.0.0"
  pullPolicy: Always
service:
  type: ClusterIP
  port: 80
ingress:
  enabled: true
  hosts:
    - host: app.example.com
      paths:
        - path: /
          pathType: Prefix
resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 250m
    memory: 256Mi

# templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "myapp.fullname" . }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "myapp.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "myapp.selectorLabels" . | nindent 8 }}
    spec:
      containers:
        - name: {{ .Chart.Name }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - containerPort: 3000
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
```

### Example 7: Pod Disruption Budget

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: api-pdb
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: api
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: db-pdb
spec:
  maxUnavailable: 1
  selector:
    matchLabels:
      app: postgres
```

## Best Practices

### Development Practices

- Use `kubectl apply` with directory-based manifests for environment-specific configs
- Use `kustomize` for environment overlay management
- Implement GitOps with ArgoCD or Flux for automated deployments
- Use `kubectl diff` before applying changes in production
- Set resource requests and limits on all containers
- Use readiness and liveness probes on every service
- Use `kubectl port-forward` for local debugging
- Enable audit logging in production clusters

### Security Practices

- Enable RBAC with least-privilege service accounts
- Use Pod Security Standards (baseline or restricted profiles)
- Implement NetworkPolicies for micro-segmentation
- Use Secrets (not ConfigMaps) for sensitive data
- Enable encryption at rest for etcd
- Use container image scanning (Trivy, Snyk)
- Enable OPA/Gatekeeper for policy enforcement
- Restrict pod-to-pod communication with network policies
- Use Seccomp and AppArmor profiles
- Never run containers as root

### Resource Management

- Set CPU and memory requests equal to limits for guaranteed QoS class
- Use HorizontalPodAutoscaler for stateless workloads
- Use VerticalPodAutoscaler for stateful workloads (in recommendation mode)
- Implement PodDisruptionBudgets for critical services
- Use resource quotas at namespace level
- Limit range with LimitRange objects
- Monitor resource utilization with metrics-server

### High Availability

- Deploy multiple replicas across different nodes
- Use PodAntiAffinity to spread pods across nodes
- Configure PodDisruptionBudgets for minimum availability
- Use multi-zone deployments for regional HA
- Use Cluster Autoscaler for node-level scaling
- Implement backup and disaster recovery procedures
- Use StatefulSets with persistent volumes for stateful services

## Common Mistakes

- **No resource limits**: Containers without resource limits can consume all node resources, causing node instability and OOM kills.
- **Using `:latest` tag**: Always use specific image tags. Latest is ambiguous and can cause unexpected updates.
- **No health checks**: Without probes, Kubernetes cannot know when a pod is ready or healthy, causing routing issues.
- **Running as root**: Containers default to root. Use `securityContext.runAsNonRoot: true` and specify a non-root user.
- **Storing secrets in ConfigMaps**: ConfigMaps store data in plaintext. Use Secrets for sensitive data.
- **Overly permissive RBAC**: Using cluster-admin for applications is dangerous. Create specific roles and service accounts.
- **Not using anti-affinity**: All pods can land on the same node, creating a single point of failure.
- **Large ConfigMaps/Secrets**: These are stored in etcd and have size limits. Use external storage for large configurations.
- **Not cleaning up completed Jobs**: Completed Jobs accumulate in the system. Set `ttlSecondsAfterFinished`.
- **Manually modifying resources**: Editing resources with `kubectl edit` bypasses GitOps. Always use declarative manifests.

## Libraries

### Kubernetes Tools

| Tool | Purpose |
|------|---------|
| kubectl | Primary CLI for Kubernetes operations |
| Helm | Package manager for Kubernetes |
| Kustomize | Native configuration management |
| Skaffold | Continuous development for Kubernetes |
| ArgoCD | GitOps continuous delivery |
| Flux | GitOps continuous delivery |
| Prometheus | Monitoring and alerting |
| Grafana | Dashboard visualization |
| Istio | Service mesh |
| cert-manager | TLS certificate management |
| NGINX Ingress Controller | Traffic routing |

### Kubernetes APIs and Clients

| Language | Client Library |
|----------|---------------|
| Go | client-go (official) |
| Python | kubernetes-client |
| Java | fabric8-kubernetes-client |
| JavaScript | @kubernetes/client-node |
| .NET | KubernetesClient |
| Rust | kube-rs |

## Design Principles

### Declarative Configuration

All Kubernetes resources should be defined declaratively in version-controlled YAML files. Manual changes to resources should be avoided. Declarative configuration enables audit trails, rollbacks, and reproducibility across environments.

### Self-Healing Systems

Kubernetes continuously works to maintain the desired state. Design applications to take advantage of this: use readiness probes for traffic routing, liveness probes for automatic restarts, and replica sets for self-healing from pod failures.

### Loose Coupling

Services should communicate through well-defined APIs and service discovery (Services), not through direct pod references. This enables independent scaling, deployment, and failure isolation of components.

### Immutable Infrastructure

Once deployed, pods should not be modified in place. Application updates should result in pod replacement, not in-place modification. This ensures consistency and enables reliable rollbacks to previous versions.

## Coding Standards

### Manifest Organization

```
k8s/
  base/
    kustomization.yaml
    deployment.yaml
    service.yaml
    configmap.yaml
  overlays/
    development/
      kustomization.yaml
      deployment-patch.yaml
    staging/
      kustomization.yaml
      ingress.yaml
    production/
      kustomization.yaml
      ingress.yaml
      hpa.yaml
```

### Naming Conventions

- Resources: `{app-name}-{resource-type}` (e.g., `api-deployment`, `postgres-service`)
- Namespaces: `{team}-{environment}` (e.g., `platform-prod`, `data-staging`)
- Labels: Use recommended labels (`app.kubernetes.io/name`, `app.kubernetes.io/instance`)
- Selectors: match resource-specific labels precisely

### Resource Tagging

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: team-awesome
  labels:
    app.kubernetes.io/name: awesome-app
    app.kubernetes.io/part-of: platform
    app.kubernetes.io/managed-by: kubectl
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: awesome-api
  labels:
    app.kubernetes.io/name: awesome-api
    app.kubernetes.io/instance: awesome-api-v1
    app.kubernetes.io/component: backend
    app.kubernetes.io/part-of: awesome-app
    app.kubernetes.io/managed-by: kustomize
```
