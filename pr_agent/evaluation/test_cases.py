"""
Kubernetes Test Cases for PR Agent Evaluation

This module contains 40 carefully crafted test cases with known errors
across different categories relevant to Kubernetes development.
"""

from dataclasses import dataclass
from typing import List, Dict, Any
from enum import Enum

class ErrorCategory(Enum):
    SECURITY = "security"
    RESOURCE_MANAGEMENT = "resource_management"
    NETWORKING = "networking"
    CONFIGURATION = "configuration"
    PERFORMANCE = "performance"
    RELIABILITY = "reliability"
    OBSERVABILITY = "observability"
    RBAC = "rbac"

class ErrorSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class KnownError:
    """Represents a known error in the test case"""
    line_number: int
    error_type: str
    description: str
    category: ErrorCategory
    severity: ErrorSeverity
    fix_suggestion: str

@dataclass
class TestCase:
    """A single test case with known errors"""
    id: str
    title: str
    description: str
    file_path: str
    code_content: str
    known_errors: List[KnownError]
    language: str = "yaml"
    
    def get_errors_by_category(self, category: ErrorCategory) -> List[KnownError]:
        return [error for error in self.known_errors if error.category == category]
    
    def get_errors_by_severity(self, severity: ErrorSeverity) -> List[KnownError]:
        return [error for error in self.known_errors if error.severity == severity]

class KubernetesTestCases:
    """Collection of 40 Kubernetes test cases with known errors"""
    
    @staticmethod
    def get_all_test_cases() -> List[TestCase]:
        """Return all 40 test cases"""
        test_cases = []
        
        # Security Issues (10 cases)
        test_cases.extend(KubernetesTestCases._get_security_test_cases())
        
        # Resource Management (8 cases)
        test_cases.extend(KubernetesTestCases._get_resource_management_test_cases())
        
        # Networking (6 cases)
        test_cases.extend(KubernetesTestCases._get_networking_test_cases())
        
        # Configuration (6 cases)
        test_cases.extend(KubernetesTestCases._get_configuration_test_cases())
        
        # Performance (4 cases)
        test_cases.extend(KubernetesTestCases._get_performance_test_cases())
        
        # Reliability (3 cases)
        test_cases.extend(KubernetesTestCases._get_reliability_test_cases())
        
        # Observability (2 cases)
        test_cases.extend(KubernetesTestCases._get_observability_test_cases())
        
        # RBAC (1 case)
        test_cases.extend(KubernetesTestCases._get_rbac_test_cases())
        
        return test_cases
    
    @staticmethod
    def _get_security_test_cases() -> List[TestCase]:
        """Security-related test cases"""
        return [
            TestCase(
                id="SEC-001",
                title="Privileged container without justification",
                description="Deployment runs container with privileged access",
                file_path="deployments/web-app.yaml",
                code_content="""apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
  namespace: default
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
    spec:
      containers:
      - name: web-app
        image: nginx:1.20
        ports:
        - containerPort: 80
        securityContext:
          privileged: true
          runAsUser: 0
        resources:
          requests:
            memory: "64Mi"
            cpu: "250m"
          limits:
            memory: "128Mi"
            cpu: "500m"
""",
                known_errors=[
                    KnownError(
                        line_number=20,
                        error_type="privileged_container",
                        description="Container runs with privileged: true without justification",
                        category=ErrorCategory.SECURITY,
                        severity=ErrorSeverity.CRITICAL,
                        fix_suggestion="Remove privileged: true or provide justification and use specific capabilities instead"
                    ),
                    KnownError(
                        line_number=21,
                        error_type="root_user",
                        description="Container runs as root user (runAsUser: 0)",
                        category=ErrorCategory.SECURITY,
                        severity=ErrorSeverity.HIGH,
                        fix_suggestion="Set runAsUser to a non-root user ID (e.g., 1000)"
                    )
                ]
            ),
            
            TestCase(
                id="SEC-002",
                title="Secret exposed in environment variables",
                description="Database credentials exposed as plain environment variables",
                file_path="deployments/api-server.yaml",
                code_content="""apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server
spec:
  replicas: 2
  selector:
    matchLabels:
      app: api-server
  template:
    metadata:
      labels:
        app: api-server
    spec:
      containers:
      - name: api-server
        image: myapp/api:v1.2.3
        env:
        - name: DB_PASSWORD
          value: "supersecret123"
        - name: API_KEY
          value: "sk-abc123def456"
        - name: JWT_SECRET
          value: "my-jwt-secret-key"
        ports:
        - containerPort: 8080
""",
                known_errors=[
                    KnownError(
                        line_number=18,
                        error_type="hardcoded_secret",
                        description="Database password hardcoded in environment variable",
                        category=ErrorCategory.SECURITY,
                        severity=ErrorSeverity.CRITICAL,
                        fix_suggestion="Use Kubernetes Secret and reference it with secretKeyRef"
                    ),
                    KnownError(
                        line_number=20,
                        error_type="hardcoded_secret",
                        description="API key hardcoded in environment variable",
                        category=ErrorCategory.SECURITY,
                        severity=ErrorSeverity.CRITICAL,
                        fix_suggestion="Use Kubernetes Secret and reference it with secretKeyRef"
                    ),
                    KnownError(
                        line_number=22,
                        error_type="hardcoded_secret",
                        description="JWT secret hardcoded in environment variable",
                        category=ErrorCategory.SECURITY,
                        severity=ErrorSeverity.CRITICAL,
                        fix_suggestion="Use Kubernetes Secret and reference it with secretKeyRef"
                    )
                ]
            ),
            
            TestCase(
                id="SEC-003",
                title="Missing security context and capabilities",
                description="Deployment lacks proper security context configuration",
                file_path="deployments/worker.yaml",
                code_content="""apiVersion: apps/v1
kind: Deployment
metadata:
  name: worker-deployment
spec:
  replicas: 5
  selector:
    matchLabels:
      app: worker
  template:
    metadata:
      labels:
        app: worker
    spec:
      containers:
      - name: worker
        image: worker:latest
        command: ["/bin/sh"]
        args: ["-c", "while true; do process_jobs; sleep 10; done"]
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
""",
                known_errors=[
                    KnownError(
                        line_number=16,
                        error_type="missing_security_context",
                        description="Container lacks securityContext configuration",
                        category=ErrorCategory.SECURITY,
                        severity=ErrorSeverity.HIGH,
                        fix_suggestion="Add securityContext with runAsNonRoot: true, readOnlyRootFilesystem: true, and drop all capabilities"
                    ),
                    KnownError(
                        line_number=16,
                        error_type="latest_tag",
                        description="Using 'latest' tag for container image",
                        category=ErrorCategory.SECURITY,
                        severity=ErrorSeverity.MEDIUM,
                        fix_suggestion="Use specific version tags instead of 'latest'"
                    )
                ]
            ),
            
            TestCase(
                id="SEC-004",
                title="Insecure service account configuration",
                description="Pod uses default service account with excessive permissions",
                file_path="deployments/admin-tool.yaml",
                code_content="""apiVersion: apps/v1
kind: Deployment
metadata:
  name: admin-tool
spec:
  replicas: 1
  selector:
    matchLabels:
      app: admin-tool
  template:
    metadata:
      labels:
        app: admin-tool
    spec:
      automountServiceAccountToken: true
      containers:
      - name: admin-tool
        image: admin-tool:v2.1
        command: ["kubectl"]
        args: ["get", "pods", "--all-namespaces"]
""",
                known_errors=[
                    KnownError(
                        line_number=14,
                        error_type="service_account_token_auto_mount",
                        description="Service account token automatically mounted without explicit service account",
                        category=ErrorCategory.SECURITY,
                        severity=ErrorSeverity.HIGH,
                        fix_suggestion="Set automountServiceAccountToken: false or create dedicated service account with minimal permissions"
                    ),
                    KnownError(
                        line_number=18,
                        error_type="kubectl_in_container",
                        description="kubectl command used in container indicates potential over-privileged access",
                        category=ErrorCategory.SECURITY,
                        severity=ErrorSeverity.MEDIUM,
                        fix_suggestion="Use specific API calls instead of kubectl or ensure proper RBAC restrictions"
                    )
                ]
            ),
            
            TestCase(
                id="SEC-005",
                title="Exposed sensitive ports",
                description="Service exposes administrative ports externally",
                file_path="services/monitoring.yaml",
                code_content="""apiVersion: v1
kind: Service
metadata:
  name: monitoring-service
spec:
  type: LoadBalancer
  ports:
  - name: metrics
    port: 9090
    targetPort: 9090
  - name: admin
    port: 8080
    targetPort: 8080
  - name: debug
    port: 6060
    targetPort: 6060
  selector:
    app: monitoring
""",
                known_errors=[
                    KnownError(
                        line_number=5,
                        error_type="exposed_admin_port",
                        description="LoadBalancer service exposes administrative/debug ports externally",
                        category=ErrorCategory.SECURITY,
                        severity=ErrorSeverity.HIGH,
                        fix_suggestion="Use ClusterIP for admin/debug ports or separate internal service"
                    ),
                    KnownError(
                        line_number=15,
                        error_type="debug_port_exposed",
                        description="Debug port 6060 exposed externally via LoadBalancer",
                        category=ErrorCategory.SECURITY,
                        severity=ErrorSeverity.HIGH,
                        fix_suggestion="Remove debug port from external service or use separate internal service"
                    )
                ]
            ),
            
            TestCase(
                id="SEC-006",
                title="Weak network policy",
                description="Network policy allows all traffic",
                file_path="policies/network-policy.yaml",
                code_content="""apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: web-netpol
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: web
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - {}
  egress:
  - {}
""",
                known_errors=[
                    KnownError(
                        line_number=13,
                        error_type="allow_all_ingress",
                        description="Network policy allows all ingress traffic with empty rule",
                        category=ErrorCategory.SECURITY,
                        severity=ErrorSeverity.HIGH,
                        fix_suggestion="Specify explicit ingress rules with source selectors"
                    ),
                    KnownError(
                        line_number=15,
                        error_type="allow_all_egress",
                        description="Network policy allows all egress traffic with empty rule",
                        category=ErrorCategory.SECURITY,
                        severity=ErrorSeverity.MEDIUM,
                        fix_suggestion="Specify explicit egress rules limiting outbound access"
                    )
                ]
            ),
            
            TestCase(
                id="SEC-007",
                title="Insecure volume mount",
                description="Sensitive host paths mounted in container",
                file_path="deployments/system-monitor.yaml",
                code_content="""apiVersion: apps/v1
kind: Deployment
metadata:
  name: system-monitor
spec:
  replicas: 1
  selector:
    matchLabels:
      app: system-monitor
  template:
    metadata:
      labels:
        app: system-monitor
    spec:
      containers:
      - name: monitor
        image: monitor:v1.0
        volumeMounts:
        - name: host-root
          mountPath: /host
        - name: docker-sock
          mountPath: /var/run/docker.sock
      volumes:
      - name: host-root
        hostPath:
          path: /
      - name: docker-sock
        hostPath:
          path: /var/run/docker.sock
""",
                known_errors=[
                    KnownError(
                        line_number=25,
                        error_type="host_root_mount",
                        description="Mounting host root filesystem (/) provides excessive access",
                        category=ErrorCategory.SECURITY,
                        severity=ErrorSeverity.CRITICAL,
                        fix_suggestion="Mount only specific directories needed, not the entire root filesystem"
                    ),
                    KnownError(
                        line_number=28,
                        error_type="docker_socket_mount",
                        description="Mounting Docker socket provides container escape capability",
                        category=ErrorCategory.SECURITY,
                        severity=ErrorSeverity.CRITICAL,
                        fix_suggestion="Use Kubernetes API instead of Docker socket or ensure proper security controls"
                    )
                ]
            ),
            
            TestCase(
                id="SEC-008",
                title="Missing pod security standards",
                description="Deployment doesn't enforce pod security standards",
                file_path="deployments/web-frontend.yaml",
                code_content="""apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-frontend
  namespace: default
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-frontend
  template:
    metadata:
      labels:
        app: web-frontend
    spec:
      containers:
      - name: frontend
        image: nginx:1.21
        ports:
        - containerPort: 80
        env:
        - name: NODE_ENV
          value: production
""",
                known_errors=[
                    KnownError(
                        line_number=5,
                        error_type="default_namespace",
                        description="Deployment uses default namespace instead of dedicated namespace",
                        category=ErrorCategory.SECURITY,
                        severity=ErrorSeverity.MEDIUM,
                        fix_suggestion="Use dedicated namespace with appropriate security policies"
                    ),
                    KnownError(
                        line_number=16,
                        error_type="missing_security_context",
                        description="No security context defined for container",
                        category=ErrorCategory.SECURITY,
                        severity=ErrorSeverity.HIGH,
                        fix_suggestion="Add securityContext with runAsNonRoot, readOnlyRootFilesystem, and capability restrictions"
                    )
                ]
            ),
            
            TestCase(
                id="SEC-009",
                title="Inadequate resource quotas",
                description="Resource quota allows excessive resource consumption",
                file_path="quotas/namespace-quota.yaml",
                code_content="""apiVersion: v1
kind: ResourceQuota
metadata:
  name: namespace-quota
  namespace: development
spec:
  hard:
    requests.cpu: "100"
    requests.memory: 200Gi
    limits.cpu: "200"
    limits.memory: 400Gi
    persistentvolumeclaims: "50"
    pods: "100"
""",
                known_errors=[
                    KnownError(
                        line_number=8,
                        error_type="excessive_cpu_quota",
                        description="CPU request quota of 100 cores is extremely high for development namespace",
                        category=ErrorCategory.SECURITY,
                        severity=ErrorSeverity.MEDIUM,
                        fix_suggestion="Set reasonable CPU limits based on actual development needs (e.g., 10-20 cores)"
                    ),
                    KnownError(
                        line_number=9,
                        error_type="excessive_memory_quota",
                        description="Memory quota of 200Gi is excessive for development environment",
                        category=ErrorCategory.SECURITY,
                        severity=ErrorSeverity.MEDIUM,
                        fix_suggestion="Set appropriate memory limits for development workloads (e.g., 50Gi)"
                    )
                ]
            ),
            
            TestCase(
                id="SEC-010",
                title="Insecure ingress configuration",
                description="Ingress allows HTTP traffic for sensitive application",
                file_path="ingress/api-ingress.yaml",
                code_content="""apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: api.company.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
  - host: admin.company.com
    http:
      paths:
      - path: /admin
        pathType: Prefix
        backend:
          service:
            name: admin-service
            port:
              number: 8080
""",
                known_errors=[
                    KnownError(
                        line_number=8,
                        error_type="missing_tls",
                        description="Ingress allows HTTP traffic without TLS termination",
                        category=ErrorCategory.SECURITY,
                        severity=ErrorSeverity.HIGH,
                        fix_suggestion="Add TLS configuration with appropriate certificates"
                    ),
                    KnownError(
                        line_number=19,
                        error_type="admin_endpoint_insecure",
                        description="Admin endpoint exposed over HTTP without TLS",
                        category=ErrorCategory.SECURITY,
                        severity=ErrorSeverity.CRITICAL,
                        fix_suggestion="Ensure admin endpoints use TLS and additional authentication"
                    )
                ]
            )
        ]
    
    @staticmethod
    def _get_resource_management_test_cases() -> List[TestCase]:
        """Resource management test cases"""
        return [
            TestCase(
                id="RES-001",
                title="Missing resource limits",
                description="Container lacks resource limits and requests",
                file_path="deployments/backend.yaml",
                code_content="""apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-api
spec:
  replicas: 5
  selector:
    matchLabels:
      app: backend-api
  template:
    metadata:
      labels:
        app: backend-api
    spec:
      containers:
      - name: api
        image: backend-api:v2.1.0
        ports:
        - containerPort: 3000
        env:
        - name: NODE_ENV
          value: production
""",
                known_errors=[
                    KnownError(
                        line_number=16,
                        error_type="missing_resource_requests",
                        description="Container has no resource requests defined",
                        category=ErrorCategory.RESOURCE_MANAGEMENT,
                        severity=ErrorSeverity.HIGH,
                        fix_suggestion="Add resource requests for CPU and memory"
                    ),
                    KnownError(
                        line_number=16,
                        error_type="missing_resource_limits",
                        description="Container has no resource limits defined",
                        category=ErrorCategory.RESOURCE_MANAGEMENT,
                        severity=ErrorSeverity.HIGH,
                        fix_suggestion="Add resource limits to prevent resource exhaustion"
                    )
                ]
            ),
            
            TestCase(
                id="RES-002",
                title="Excessive resource allocation",
                description="Container requests more resources than necessary",
                file_path="deployments/cache.yaml",
                code_content="""apiVersion: apps/v1
kind: Deployment
metadata:
  name: cache-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: cache
  template:
    metadata:
      labels:
        app: cache
    spec:
      containers:
      - name: redis
        image: redis:6.2
        resources:
          requests:
            memory: "8Gi"
            cpu: "4000m"
          limits:
            memory: "16Gi"
            cpu: "8000m"
""",
                known_errors=[
                    KnownError(
                        line_number=20,
                        error_type="excessive_memory_request",
                        description="Redis container requests 8Gi memory which is excessive for typical cache usage",
                        category=ErrorCategory.RESOURCE_MANAGEMENT,
                        severity=ErrorSeverity.MEDIUM,
                        fix_suggestion="Reduce memory request to appropriate size based on cache requirements (e.g., 512Mi-2Gi)"
                    ),
                    KnownError(
                        line_number=21,
                        error_type="excessive_cpu_request",
                        description="Redis container requests 4 CPU cores which is excessive",
                        category=ErrorCategory.RESOURCE_MANAGEMENT,
                        severity=ErrorSeverity.MEDIUM,
                        fix_suggestion="Reduce CPU request to 100m-500m based on actual usage patterns"
                    )
                ]
            ),
            
            TestCase(
                id="RES-003",
                title="Improper resource ratio",
                description="Resource limits are disproportionate to requests",
                file_path="deployments/worker-pool.yaml",
                code_content="""apiVersion: apps/v1
kind: Deployment
metadata:
  name: worker-pool
spec:
  replicas: 10
  selector:
    matchLabels:
      app: worker
  template:
    metadata:
      labels:
        app: worker
    spec:
      containers:
      - name: worker
        image: worker:v1.5
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "4Gi"
            cpu: "100m"
""",
                known_errors=[
                    KnownError(
                        line_number=22,
                        error_type="disproportionate_memory_limit",
                        description="Memory limit (4Gi) is 64x larger than request (64Mi), indicating poor resource planning",
                        category=ErrorCategory.RESOURCE_MANAGEMENT,
                        severity=ErrorSeverity.MEDIUM,
                        fix_suggestion="Set memory limit closer to actual usage, typically 1.5-2x the request"
                    ),
                    KnownError(
                        line_number=19,
                        error_type="low_memory_request",
                        description="Memory request of 64Mi is too low for most applications",
                        category=ErrorCategory.RESOURCE_MANAGEMENT,
                        severity=ErrorSeverity.LOW,
                        fix_suggestion="Increase memory request to realistic minimum (e.g., 128Mi-256Mi)"
                    )
                ]
            ),
            
            TestCase(
                id="RES-004",
                title="Missing horizontal pod autoscaler",
                description="High-load deployment without HPA configuration",
                file_path="deployments/high-traffic-api.yaml",
                code_content="""apiVersion: apps/v1
kind: Deployment
metadata:
  name: high-traffic-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: high-traffic-api
  template:
    metadata:
      labels:
        app: high-traffic-api
    spec:
      containers:
      - name: api
        image: api:v3.2.1
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
""",
                known_errors=[
                    KnownError(
                        line_number=6,
                        error_type="missing_hpa",
                        description="High-traffic API with fixed replica count lacks horizontal pod autoscaler",
                        category=ErrorCategory.RESOURCE_MANAGEMENT,
                        severity=ErrorSeverity.MEDIUM,
                        fix_suggestion="Add HorizontalPodAutoscaler to handle traffic spikes automatically"
                    ),
                    KnownError(
                        line_number=6,
                        error_type="low_replica_count",
                        description="Only 3 replicas for high-traffic API may not provide sufficient availability",
                        category=ErrorCategory.RESOURCE_MANAGEMENT,
                        severity=ErrorSeverity.LOW,
                        fix_suggestion="Consider increasing minimum replicas or implementing HPA"
                    )
                ]
            ),
            
            TestCase(
                id="RES-005",
                title="Inefficient storage configuration",
                description="Persistent volume claim with inappropriate settings",
                file_path="storage/database-pvc.yaml",
                code_content="""apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: database-storage
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 10Ti
  storageClassName: standard
""",
                known_errors=[
                    KnownError(
                        line_number=7,
                        error_type="inappropriate_access_mode",
                        description="ReadWriteMany access mode is expensive and rarely needed for databases",
                        category=ErrorCategory.RESOURCE_MANAGEMENT,
                        severity=ErrorSeverity.MEDIUM,
                        fix_suggestion="Use ReadWriteOnce for single-instance databases"
                    ),
                    KnownError(
                        line_number=10,
                        error_type="excessive_storage_request",
                        description="10Ti storage request is extremely large and may be unnecessary",
                        category=ErrorCategory.RESOURCE_MANAGEMENT,
                        severity=ErrorSeverity.HIGH,
                        fix_suggestion="Start with reasonable size and use volume expansion if needed"
                    ),
                    KnownError(
                        line_number=11,
                        error_type="inappropriate_storage_class",
                        description="Standard storage class may not provide adequate performance for databases",
                        category=ErrorCategory.RESOURCE_MANAGEMENT,
                        severity=ErrorSeverity.LOW,
                        fix_suggestion="Consider using SSD-based storage class for better database performance"
                    )
                ]
            ),
            
            TestCase(
                id="RES-006",
                title="Resource contention risk",
                description="Multiple resource-intensive pods without node affinity",
                file_path="deployments/ml-training.yaml",
                code_content="""apiVersion: apps/v1
kind: Deployment
metadata:
  name: ml-training
spec:
  replicas: 4
  selector:
    matchLabels:
      app: ml-training
  template:
    metadata:
      labels:
        app: ml-training
    spec:
      containers:
      - name: trainer
        image: ml-trainer:gpu-v1.0
        resources:
          requests:
            memory: "16Gi"
            cpu: "8000m"
            nvidia.com/gpu: 1
          limits:
            memory: "32Gi"
            cpu: "16000m"
            nvidia.com/gpu: 1
""",
                known_errors=[
                    KnownError(
                        line_number=6,
                        error_type="missing_pod_affinity",
                        description="Resource-intensive GPU workload lacks node affinity/anti-affinity rules",
                        category=ErrorCategory.RESOURCE_MANAGEMENT,
                        severity=ErrorSeverity.MEDIUM,
                        fix_suggestion="Add node affinity to distribute GPU workloads across different nodes"
                    ),
                    KnownError(
                        line_number=17,
                        error_type="high_resource_contention_risk",
                        description="4 replicas requesting 8 CPU cores each may cause resource contention",
                        category=ErrorCategory.RESOURCE_MANAGEMENT,
                        severity=ErrorSeverity.MEDIUM,
                        fix_suggestion="Consider pod anti-affinity or reduce concurrent replicas"
                    )
                ]
            ),
            
            TestCase(
                id="RES-007",
                title="Inefficient job resource allocation",
                description="Kubernetes Job with improper resource configuration",
                file_path="jobs/data-processing.yaml",
                code_content="""apiVersion: batch/v1
kind: Job
metadata:
  name: data-processing
spec:
  parallelism: 20
  completions: 100
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: processor
        image: data-processor:v2.0
        command: ["python", "process_data.py"]
        resources:
          requests:
            memory: "4Gi"
            cpu: "2000m"
""",
                known_errors=[
                    KnownError(
                        line_number=6,
                        error_type="high_parallelism",
                        description="Parallelism of 20 with 2 CPU cores each may overwhelm cluster resources",
                        category=ErrorCategory.RESOURCE_MANAGEMENT,
                        severity=ErrorSeverity.HIGH,
                        fix_suggestion="Reduce parallelism or implement resource-aware scheduling"
                    ),
                    KnownError(
                        line_number=16,
                        error_type="missing_resource_limits",
                        description="Job containers lack resource limits, risking resource exhaustion",
                        category=ErrorCategory.RESOURCE_MANAGEMENT,
                        severity=ErrorSeverity.MEDIUM,
                        fix_suggestion="Add resource limits to prevent individual containers from consuming excess resources"
                    )
                ]
            ),
            
            TestCase(
                id="RES-008",
                title="Inappropriate resource requests for init containers",
                description="Init container with excessive resource allocation",
                file_path="deployments/app-with-init.yaml",
                code_content="""apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-with-init
spec:
  replicas: 3
  selector:
    matchLabels:
      app: app-with-init
  template:
    metadata:
      labels:
        app: app-with-init
    spec:
      initContainers:
      - name: db-migration
        image: migrate:v1.0
        command: ["migrate", "up"]
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
      containers:
      - name: app
        image: app:v1.0
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
""",
                known_errors=[
                    KnownError(
                        line_number=20,
                        error_type="excessive_init_container_resources",
                        description="Init container requests more resources than main application container",
                        category=ErrorCategory.RESOURCE_MANAGEMENT,
                        severity=ErrorSeverity.MEDIUM,
                        fix_suggestion="Right-size init container resources based on actual migration requirements"
                    ),
                    KnownError(
                        line_number=18,
                        error_type="database_migration_in_init",
                        description="Database migration in init container can cause deployment delays",
                        category=ErrorCategory.RESOURCE_MANAGEMENT,
                        severity=ErrorSeverity.LOW,
                        fix_suggestion="Consider running migrations as separate Job or using migration tools with retry logic"
                    )
                ]
            )
        ]
    
    @staticmethod
    def _get_networking_test_cases() -> List[TestCase]:
        """Networking-related test cases"""
        return [
            TestCase(
                id="NET-001",
                title="Service without proper health checks",
                description="Service routing to pods without readiness probes",
                file_path="services/api-service.yaml",
                code_content="""apiVersion: v1
kind: Service
metadata:
  name: api-service
spec:
  selector:
    app: api
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
      - name: api
        image: api:v1.0
        ports:
        - containerPort: 8080
""",
                known_errors=[
                    KnownError(
                        line_number=26,
                        error_type="missing_readiness_probe",
                        description="Container lacks readiness probe, service may route to unhealthy pods",
                        category=ErrorCategory.NETWORKING,
                        severity=ErrorSeverity.HIGH,
                        fix_suggestion="Add readiness probe to ensure service only routes to healthy pods"
                    ),
                    KnownError(
                        line_number=26,
                        error_type="missing_liveness_probe",
                        description="Container lacks liveness probe for automatic restart on failure",
                        category=ErrorCategory.NETWORKING,
                        severity=ErrorSeverity.MEDIUM,
                        fix_suggestion="Add liveness probe to restart unhealthy containers"
                    )
                ]
            ),
            
            TestCase(
                id="NET-002",
                title="Incorrect service port configuration",
                description="Service port mismatch with container port",
                file_path="services/web-service.yaml",
                code_content="""apiVersion: v1
kind: Service
metadata:
  name: web-service
spec:
  selector:
    app: web
  ports:
  - name: http
    port: 80
    targetPort: 3000
  - name: https
    port: 443
    targetPort: 8443
  type: LoadBalancer
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-deployment
spec:
  replicas: 2
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: web
        image: nginx:1.21
        ports:
        - containerPort: 80
        - containerPort: 443
""",
                known_errors=[
                    KnownError(
                        line_number=11,
                        error_type="port_mismatch",
                        description="Service targetPort 3000 doesn't match container port 80",
                        category=ErrorCategory.NETWORKING,
                        severity=ErrorSeverity.HIGH,
                        fix_suggestion="Ensure service targetPort matches container containerPort"
                    ),
                    KnownError(
                        line_number=14,
                        error_type="port_mismatch",
                        description="Service targetPort 8443 doesn't match container port 443",
                        category=ErrorCategory.NETWORKING,
                        severity=ErrorSeverity.HIGH,
                        fix_suggestion="Ensure HTTPS service targetPort matches container HTTPS port"
                    )
                ]
            ),
            
            TestCase(
                id="NET-003",
                title="DNS configuration issues",
                description="Pod with incorrect DNS configuration",
                file_path="deployments/dns-consumer.yaml",
                code_content="""apiVersion: apps/v1
kind: Deployment
metadata:
  name: dns-consumer
spec:
  replicas: 2
  selector:
    matchLabels:
      app: dns-consumer
  template:
    metadata:
      labels:
        app: dns-consumer
    spec:
      dnsPolicy: None
      dnsConfig:
        nameservers:
        - 8.8.8.8
        searches:
        - custom.local
      containers:
      - name: consumer
        image: dns-consumer:v1.0
""",
                known_errors=[
                    KnownError(
                        line_number=15,
                        error_type="inappropriate_dns_policy",
                        description="DNS policy 'None' with external nameserver bypasses Kubernetes DNS",
                        category=ErrorCategory.NETWORKING,
                        severity=ErrorSeverity.MEDIUM,
                        fix_suggestion="Use 'Default' or 'ClusterFirst' DNS policy for Kubernetes service discovery"
                    ),
                    KnownError(
                        line_number=18,
                        error_type="external_dns_dependency",
                        description="Pod depends on external DNS (8.8.8.8) which may not resolve cluster services",
                        category=ErrorCategory.NETWORKING,
                        severity=ErrorSeverity.MEDIUM,
                        fix_suggestion="Include cluster DNS servers or use ClusterFirst policy"
                    )
                ]
            ),
            
            TestCase(
                id="NET-004",
                title="Load balancer with session affinity issues",
                description="Service with inappropriate session affinity configuration",
                file_path="services/stateful-service.yaml",
                code_content="""apiVersion: v1
kind: Service
metadata:
  name: stateful-service
spec:
  selector:
    app: stateful-app
  ports:
  - port: 80
    targetPort: 8080
  type: LoadBalancer
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 86400
""",
                known_errors=[
                    KnownError(
                        line_number=12,
                        error_type="inappropriate_session_affinity",
                        description="ClientIP session affinity may cause uneven load distribution",
                        category=ErrorCategory.NETWORKING,
                        severity=ErrorSeverity.MEDIUM,
                        fix_suggestion="Consider using stateless design or external session storage instead"
                    ),
                    KnownError(
                        line_number=15,
                        error_type="excessive_session_timeout",
                        description="Session affinity timeout of 24 hours (86400s) is too long",
                        category=ErrorCategory.NETWORKING,
                        severity=ErrorSeverity.LOW,
                        fix_suggestion="Reduce session timeout to reasonable duration (e.g., 3600s)"
                    )
                ]
            ),
            
            TestCase(
                id="NET-005",
                title="Ingress path conflicts",
                description="Ingress with overlapping path configurations",
                file_path="ingress/conflicting-paths.yaml",
                code_content="""apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: conflicting-paths
spec:
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /api/v1
        pathType: Prefix
        backend:
          service:
            name: api-v1-service
            port:
              number: 80
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api-legacy-service
            port:
              number: 80
      - path: /api/v1/users
        pathType: Exact
        backend:
          service:
            name: user-service
            port:
              number: 80
""",
                known_errors=[
                    KnownError(
                        line_number=17,
                        error_type="path_conflict",
                        description="Path '/api' conflicts with more specific '/api/v1' - order matters",
                        category=ErrorCategory.NETWORKING,
                        severity=ErrorSeverity.HIGH,
                        fix_suggestion="Order paths from most specific to least specific or use different path patterns"
                    ),
                    KnownError(
                        line_number=23,
                        error_type="unreachable_path",
                        description="Exact path '/api/v1/users' may be unreachable due to prefix '/api/v1' matching first",
                        category=ErrorCategory.NETWORKING,
                        severity=ErrorSeverity.MEDIUM,
                        fix_suggestion="Reorder paths or use more specific path matching strategies"
                    )
                ]
            ),
            
            TestCase(
                id="NET-006",
                title="Missing network segmentation",
                description="Sensitive workload without network isolation",
                file_path="deployments/payment-service.yaml",
                code_content="""apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-service
  namespace: default
spec:
  replicas: 2
  selector:
    matchLabels:
      app: payment-service
  template:
    metadata:
      labels:
        app: payment-service
    spec:
      containers:
      - name: payment
        image: payment-service:v2.1
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_URL
          value: "postgresql://user:pass@db:5432/payments"
""",
                known_errors=[
                    KnownError(
                        line_number=5,
                        error_type="sensitive_workload_default_namespace",
                        description="Payment service in default namespace lacks proper isolation",
                        category=ErrorCategory.NETWORKING,
                        severity=ErrorSeverity.HIGH,
                        fix_suggestion="Move to dedicated namespace with network policies for PCI compliance"
                    ),
                    KnownError(
                        line_number=13,
                        error_type="missing_network_policy",
                        description="Payment workload lacks network policy for traffic isolation",
                        category=ErrorCategory.NETWORKING,
                        severity=ErrorSeverity.HIGH,
                        fix_suggestion="Implement network policies to restrict ingress/egress traffic"
                    )
                ]
            )
        ]
    
    @staticmethod
    def _get_configuration_test_cases() -> List[TestCase]:
        """Configuration-related test cases"""
        return [
            TestCase(
                id="CFG-001",
                title="Hardcoded configuration values",
                description="Configuration values hardcoded in deployment",
                file_path="deployments/app-config.yaml",
                code_content="""apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-config
spec:
  replicas: 3
  selector:
    matchLabels:
      app: config-app
  template:
    metadata:
      labels:
        app: config-app
    spec:
      containers:
      - name: app
        image: config-app:v1.0
        env:
        - name: DATABASE_HOST
          value: "prod-db-cluster.us-east-1.rds.amazonaws.com"
        - name: REDIS_URL
          value: "redis://prod-cache.abc123.cache.amazonaws.com:6379"
        - name: LOG_LEVEL
          value: "DEBUG"
        - name: MAX_CONNECTIONS
          value: "100"
""",
                known_errors=[
                    KnownError(
                        line_number=19,
                        error_type="hardcoded_external_dependency",
                        description="Database host hardcoded instead of using ConfigMap or service discovery",
                        category=ErrorCategory.CONFIGURATION,
                        severity=ErrorSeverity.MEDIUM,
                        fix_suggestion="Use ConfigMap for environment-specific configuration"
                    ),
                    KnownError(
                        line_number=21,
                        error_type="hardcoded_external_dependency",
                        description="Redis URL hardcoded with specific AWS endpoint",
                        category=ErrorCategory.CONFIGURATION,
                        severity=ErrorSeverity.MEDIUM,
                        fix_suggestion="Use ConfigMap or environment-specific configuration"
                    ),
                    KnownError(
                        line_number=23,
                        error_type="debug_in_production",
                        description="DEBUG log level in production deployment may impact performance",
                        category=ErrorCategory.CONFIGURATION,
                        severity=ErrorSeverity.LOW,
                        fix_suggestion="Use INFO or WARN log level for production"
                    )
                ]
            ),
            
            TestCase(
                id="CFG-002",
                title="Missing ConfigMap volume mount",
                description="Application expects config file but missing volume mount",
                file_path="deployments/config-file-app.yaml",
                code_content="""apiVersion: apps/v1
kind: Deployment
metadata:
  name: config-file-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: config-file-app
  template:
    metadata:
      labels:
        app: config-file-app
    spec:
      containers:
      - name: app
        image: config-file-app:v1.0
        command: ["./app", "--config", "/etc/app/config.yaml"]
        volumeMounts:
        - name: config-volume
          mountPath: /etc/app
      volumes:
      - name: config-volume
        emptyDir: {}
""",
                known_errors=[
                    KnownError(
                        line_number=23,
                        error_type="empty_dir_for_config",
                        description="Using emptyDir for configuration instead of ConfigMap",
                        category=ErrorCategory.CONFIGURATION,
                        severity=ErrorSeverity.HIGH,
                        fix_suggestion="Use ConfigMap volume for configuration files"
                    ),
                    KnownError(
                        line_number=17,
                        error_type="missing_config_file",
                        description="Application expects config file at /etc/app/config.yaml but no ConfigMap provided",
                        category=ErrorCategory.CONFIGURATION,
                        severity=ErrorSeverity.HIGH,
                        fix_suggestion="Create ConfigMap with required configuration file"
                    )
                ]
            ),
            
            TestCase(
                id="CFG-003",
                title="Inconsistent environment variables",
                description="Environment variables with inconsistent naming",
                file_path="deployments/multi-container.yaml",
                code_content="""apiVersion: apps/v1
kind: Deployment
metadata:
  name: multi-container-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: multi-container
  template:
    metadata:
      labels:
        app: multi-container
    spec:
      containers:
      - name: frontend
        image: frontend:v1.0
        env:
        - name: API_ENDPOINT
          value: "http://localhost:8080"
        - name: api_key
          value: "abc123"
      - name: backend
        image: backend:v1.0
        env:
        - name: DATABASE_URL
          value: "postgres://localhost:5432/db"
        - name: Debug
          value: "true"
        - name: PORT
          value: "8080"
""",
                known_errors=[
                    KnownError(
                        line_number=21,
                        error_type="inconsistent_env_naming",
                        description="Environment variable 'api_key' uses snake_case while others use UPPER_CASE",
                        category=ErrorCategory.CONFIGURATION,
                        severity=ErrorSeverity.LOW,
                        fix_suggestion="Use consistent naming convention (preferably UPPER_CASE for env vars)"
                    ),
                    KnownError(
                        line_number=27,
                        error_type="inconsistent_env_naming",
                        description="Environment variable 'Debug' uses PascalCase instead of UPPER_CASE",
                        category=ErrorCategory.CONFIGURATION,
                        severity=ErrorSeverity.LOW,
                        fix_suggestion="Rename to 'DEBUG' for consistency"
                    ),
                    KnownError(
                        line_number=19,
                        error_type="localhost_in_config",
                        description="Using localhost in container configuration may not work in Kubernetes",
                        category=ErrorCategory.CONFIGURATION,
                        severity=ErrorSeverity.MEDIUM,
                        fix_suggestion="Use service names or proper Kubernetes networking"
                    )
                ]
            ),
            
            TestCase(
                id="CFG-004",
                title="Missing configuration validation",
                description="ConfigMap with potentially invalid configuration",
                file_path="config/app-config.yaml",
                code_content="""apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  config.yaml: |
    server:
      port: "not-a-number"
      host: ""
      timeout: -5
    database:
      connections: 0
      retry_attempts: -1
    cache:
      ttl: "invalid-duration"
      size: "unlimited"
""",
                known_errors=[
                    KnownError(
                        line_number=8,
                        error_type="invalid_port_config",
                        description="Server port configured as non-numeric string 'not-a-number'",
                        category=ErrorCategory.CONFIGURATION,
                        severity=ErrorSeverity.HIGH,
                        fix_suggestion="Set valid numeric port (e.g., 8080)"
                    ),
                    KnownError(
                        line_number=10,
                        error_type="negative_timeout",
                        description="Negative timeout value (-5) is invalid",
                        category=ErrorCategory.CONFIGURATION,
                        severity=ErrorSeverity.MEDIUM,
                        fix_suggestion="Set positive timeout value"
                    ),
                    KnownError(
                        line_number=12,
                        error_type="zero_connections",
                        description="Database connections set to 0 will prevent database access",
                        category=ErrorCategory.CONFIGURATION,
                        severity=ErrorSeverity.HIGH,
                        fix_suggestion="Set appropriate number of database connections (e.g., 10-50)"
                    )
                ]
            ),
            
            TestCase(
                id="CFG-005",
                title="Overly permissive RBAC",
                description="Service account with excessive permissions",
                file_path="rbac/service-account.yaml",
                code_content="""apiVersion: v1
kind: ServiceAccount
metadata:
  name: app-service-account
  namespace: default
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: app-cluster-role
rules:
- apiGroups: ["*"]
  resources: ["*"]
  verbs: ["*"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: app-cluster-role-binding
subjects:
- kind: ServiceAccount
  name: app-service-account
  namespace: default
roleRef:
  kind: ClusterRole
  name: app-cluster-role
  apiGroup: rbac.authorization.k8s.io
""",
                known_errors=[
                    KnownError(
                        line_number=12,
                        error_type="wildcard_permissions",
                        description="ClusterRole grants wildcard permissions on all resources and verbs",
                        category=ErrorCategory.CONFIGURATION,
                        severity=ErrorSeverity.CRITICAL,
                        fix_suggestion="Grant only specific permissions needed by the application"
                    ),
                    KnownError(
                        line_number=16,
                        error_type="cluster_role_for_app",
                        description="Application using cluster-wide permissions instead of namespace-scoped Role",
                        category=ErrorCategory.CONFIGURATION,
                        severity=ErrorSeverity.HIGH,
                        fix_suggestion="Use namespace-scoped Role unless cluster access is truly needed"
                    )
                ]
            ),
            
            TestCase(
                id="CFG-006",
                title="Missing resource quotas and limits",
                description="Namespace without resource governance",
                file_path="namespaces/development.yaml",
                code_content="""apiVersion: v1
kind: Namespace
metadata:
  name: development
  labels:
    environment: dev
""",
                known_errors=[
                    KnownError(
                        line_number=1,
                        error_type="missing_resource_quota",
                        description="Development namespace lacks ResourceQuota for resource governance",
                        category=ErrorCategory.CONFIGURATION,
                        severity=ErrorSeverity.MEDIUM,
                        fix_suggestion="Add ResourceQuota to prevent resource exhaustion in development environment"
                    ),
                    KnownError(
                        line_number=1,
                        error_type="missing_limit_range",
                        description="Namespace lacks LimitRange for default resource constraints",
                        category=ErrorCategory.CONFIGURATION,
                        severity=ErrorSeverity.MEDIUM,
                        fix_suggestion="Add LimitRange to set default resource limits for pods"
                    )
                ]
            )
        ]
    
    @staticmethod
    def _get_performance_test_cases() -> List[TestCase]:
        """Performance-related test cases"""
        return [
            TestCase(
                id="PERF-001",
                title="Inefficient image pull configuration",
                description="Deployment with frequent unnecessary image pulls",
                file_path="deployments/frequent-updates.yaml",
                code_content="""apiVersion: apps/v1
kind: Deployment
metadata:
  name: frequent-updates
spec:
  replicas: 5
  selector:
    matchLabels:
      app: frequent-updates
  template:
    metadata:
      labels:
        app: frequent-updates
    spec:
      containers:
      - name: app
        image: app:latest
        imagePullPolicy: Always
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
""",
                known_errors=[
                    KnownError(
                        line_number=17,
                        error_type="always_pull_policy",
                        description="imagePullPolicy: Always causes unnecessary image pulls on every pod restart",
                        category=ErrorCategory.PERFORMANCE,
                        severity=ErrorSeverity.MEDIUM,
                        fix_suggestion="Use IfNotPresent policy or specific image tags instead of 'latest'"
                    ),
                    KnownError(
                        line_number=16,
                        error_type="latest_tag_performance",
                        description="Using 'latest' tag with Always pull policy impacts startup performance",
                        category=ErrorCategory.PERFORMANCE,
                        severity=ErrorSeverity.MEDIUM,
                        fix_suggestion="Use specific version tags for consistent performance"
                    )
                ]
            ),
            
            TestCase(
                id="PERF-002",
                title="Suboptimal probe configuration",
                description="Health check probes with inefficient settings",
                file_path="deployments/slow-probes.yaml",
                code_content="""apiVersion: apps/v1
kind: Deployment
metadata:
  name: slow-probes
spec:
  replicas: 3
  selector:
    matchLabels:
      app: slow-probes
  template:
    metadata:
      labels:
        app: slow-probes
    spec:
      containers:
      - name: app
        image: slow-app:v1.0
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 1
          timeoutSeconds: 30
          failureThreshold: 1
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 1
          timeoutSeconds: 30
""",
                known_errors=[
                    KnownError(
                        line_number=22,
                        error_type="frequent_probe_interval",
                        description="Liveness probe period of 1 second is too frequent and wastes resources",
                        category=ErrorCategory.PERFORMANCE,
                        severity=ErrorSeverity.MEDIUM,
                        fix_suggestion="Increase periodSeconds to 10-30 seconds for liveness probe"
                    ),
                    KnownError(
                        line_number=23,
                        error_type="excessive_probe_timeout",
                        description="Probe timeout of 30 seconds is excessive and delays failure detection",
                        category=ErrorCategory.PERFORMANCE,
                        severity=ErrorSeverity.LOW,
                        fix_suggestion="Reduce timeout to 5-10 seconds"
                    ),
                    KnownError(
                        line_number=24,
                        error_type="low_failure_threshold",
                        description="Failure threshold of 1 for liveness probe may cause premature restarts",
                        category=ErrorCategory.PERFORMANCE,
                        severity=ErrorSeverity.MEDIUM,
                        fix_suggestion="Increase failure threshold to 3-5 for liveness probe"
                    )
                ]
            ),
            
            TestCase(
                id="PERF-003",
                title="Inefficient storage configuration",
                description="Storage configuration that impacts performance",
                file_path="storage/slow-storage.yaml",
                code_content="""apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-storage
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  storageClassName: standard-hdd
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: database-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: database-app
  template:
    metadata:
      labels:
        app: database-app
    spec:
      containers:
      - name: database
        image: mysql:8.0
        volumeMounts:
        - name: data
          mountPath: /var/lib/mysql
        env:
        - name: MYSQL_ROOT_PASSWORD
          value: "rootpassword"
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: app-storage
""",
                known_errors=[
                    KnownError(
                        line_number=11,
                        error_type="slow_storage_class",
                        description="Using standard-hdd storage class for database will cause poor I/O performance",
                        category=ErrorCategory.PERFORMANCE,
                        severity=ErrorSeverity.HIGH,
                        fix_suggestion="Use SSD-based storage class (e.g., fast-ssd) for database workloads"
                    ),
                    KnownError(
                        line_number=9,
                        error_type="small_storage_size",
                        description="1Gi storage may be insufficient for database, causing frequent I/O issues",
                        category=ErrorCategory.PERFORMANCE,
                        severity=ErrorSeverity.MEDIUM,
                        fix_suggestion="Allocate appropriate storage size based on data requirements"
                    )
                ]
            ),
            
            TestCase(
                id="PERF-004",
                title="Missing performance optimization",
                description="Application without performance optimizations",
                file_path="deployments/unoptimized-app.yaml",
                code_content="""apiVersion: apps/v1
kind: Deployment
metadata:
  name: unoptimized-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: unoptimized-app
  template:
    metadata:
      labels:
        app: unoptimized-app
    spec:
      containers:
      - name: app
        image: heavy-app:v1.0
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        env:
        - name: JAVA_OPTS
          value: "-Xmx2g -XX:+UseSerialGC"
""",
                known_errors=[
                    KnownError(
                        line_number=25,
                        error_type="inappropriate_jvm_settings",
                        description="JVM heap size (2g) exceeds container memory limit (256Mi)",
                        category=ErrorCategory.PERFORMANCE,
                        severity=ErrorSeverity.HIGH,
                        fix_suggestion="Adjust JVM heap size to fit within container memory limits"
                    ),
                    KnownError(
                        line_number=25,
                        error_type="inefficient_gc",
                        description="Using SerialGC is inefficient for containerized applications",
                        category=ErrorCategory.PERFORMANCE,
                        severity=ErrorSeverity.MEDIUM,
                        fix_suggestion="Use G1GC or other modern garbage collectors for better performance"
                    ),
                    KnownError(
                        line_number=6,
                        error_type="single_replica_performance",
                        description="Single replica deployment creates performance bottleneck",
                        category=ErrorCategory.PERFORMANCE,
                        severity=ErrorSeverity.LOW,
                        fix_suggestion="Consider increasing replicas or implementing HPA for better performance"
                    )
                ]
            )
        ]
    
    @staticmethod
    def _get_reliability_test_cases() -> List[TestCase]:
        """Reliability-related test cases"""
        return [
            TestCase(
                id="REL-001",
                title="Missing disruption budget",
                description="Critical service without pod disruption budget",
                file_path="deployments/critical-service.yaml",
                code_content="""apiVersion: apps/v1
kind: Deployment
metadata:
  name: critical-service
  labels:
    tier: critical
spec:
  replicas: 2
  selector:
    matchLabels:
      app: critical-service
  template:
    metadata:
      labels:
        app: critical-service
    spec:
      containers:
      - name: service
        image: critical-service:v1.0
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
""",
                known_errors=[
                    KnownError(
                        line_number=1,
                        error_type="missing_pod_disruption_budget",
                        description="Critical service lacks PodDisruptionBudget for availability during updates",
                        category=ErrorCategory.RELIABILITY,
                        severity=ErrorSeverity.HIGH,
                        fix_suggestion="Add PodDisruptionBudget to ensure minimum available replicas during disruptions"
                    ),
                    KnownError(
                        line_number=8,
                        error_type="insufficient_replicas_for_ha",
                        description="Only 2 replicas for critical service may not provide adequate high availability",
                        category=ErrorCategory.RELIABILITY,
                        severity=ErrorSeverity.MEDIUM,
                        fix_suggestion="Consider 3+ replicas for better fault tolerance"
                    )
                ]
            ),
            
            TestCase(
                id="REL-002",
                title="Unsafe update strategy",
                description="Deployment with risky update configuration",
                file_path="deployments/risky-updates.yaml",
                code_content="""apiVersion: apps/v1
kind: Deployment
metadata:
  name: risky-updates
spec:
  replicas: 4
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 100%
      maxSurge: 0%
  selector:
    matchLabels:
      app: risky-updates
  template:
    metadata:
      labels:
        app: risky-updates
    spec:
      containers:
      - name: app
        image: app:v2.0
""",
                known_errors=[
                    KnownError(
                        line_number=10,
                        error_type="dangerous_max_unavailable",
                        description="maxUnavailable: 100% allows all pods to be unavailable during update",
                        category=ErrorCategory.RELIABILITY,
                        severity=ErrorSeverity.CRITICAL,
                        fix_suggestion="Set maxUnavailable to 25-50% to maintain service availability"
                    ),
                    KnownError(
                        line_number=11,
                        error_type="zero_max_surge",
                        description="maxSurge: 0% combined with 100% unavailable creates total service outage",
                        category=ErrorCategory.RELIABILITY,
                        severity=ErrorSeverity.CRITICAL,
                        fix_suggestion="Set maxSurge to 25-50% to allow new pods before terminating old ones"
                    )
                ]
            ),
            
            TestCase(
                id="REL-003",
                title="Single point of failure",
                description="Critical component with single point of failure",
                file_path="deployments/single-point-failure.yaml",
                code_content="""apiVersion: apps/v1
kind: Deployment
metadata:
  name: database-proxy
spec:
  replicas: 1
  selector:
    matchLabels:
      app: database-proxy
  template:
    metadata:
      labels:
        app: database-proxy
    spec:
      nodeSelector:
        node-type: database-node
      containers:
      - name: proxy
        image: db-proxy:v1.0
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: config
          mountPath: /etc/proxy
      volumes:
      - name: config
        hostPath:
          path: /opt/proxy-config
""",
                known_errors=[
                    KnownError(
                        line_number=6,
                        error_type="single_replica_spof",
                        description="Database proxy with single replica creates single point of failure",
                        category=ErrorCategory.RELIABILITY,
                        severity=ErrorSeverity.CRITICAL,
                        fix_suggestion="Increase replicas to at least 2 for high availability"
                    ),
                    KnownError(
                        line_number=15,
                        error_type="node_selector_constraint",
                        description="nodeSelector restricts deployment to specific node type, reducing availability",
                        category=ErrorCategory.RELIABILITY,
                        severity=ErrorSeverity.MEDIUM,
                        fix_suggestion="Use node affinity instead of hard node selector for better flexibility"
                    ),
                    KnownError(
                        line_number=25,
                        error_type="host_path_dependency",
                        description="hostPath volume creates dependency on specific node filesystem",
                        category=ErrorCategory.RELIABILITY,
                        severity=ErrorSeverity.HIGH,
                        fix_suggestion="Use ConfigMap or persistent volume for configuration"
                    )
                ]
            )
        ]
    
    @staticmethod
    def _get_observability_test_cases() -> List[TestCase]:
        """Observability-related test cases"""
        return [
            TestCase(
                id="OBS-001",
                title="Missing monitoring configuration",
                description="Service without proper monitoring setup",
                file_path="deployments/unmonitored-service.yaml",
                code_content="""apiVersion: apps/v1
kind: Deployment
metadata:
  name: unmonitored-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: unmonitored-service
  template:
    metadata:
      labels:
        app: unmonitored-service
    spec:
      containers:
      - name: service
        image: service:v1.0
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
""",
                known_errors=[
                    KnownError(
                        line_number=12,
                        error_type="missing_monitoring_labels",
                        description="Pod lacks monitoring labels for service discovery (e.g., prometheus annotations)",
                        category=ErrorCategory.OBSERVABILITY,
                        severity=ErrorSeverity.MEDIUM,
                        fix_suggestion="Add monitoring labels/annotations for metrics collection"
                    ),
                    KnownError(
                        line_number=17,
                        error_type="missing_metrics_port",
                        description="No dedicated metrics port exposed for monitoring",
                        category=ErrorCategory.OBSERVABILITY,
                        severity=ErrorSeverity.MEDIUM,
                        fix_suggestion="Expose metrics port (e.g., 9090) for Prometheus scraping"
                    )
                ]
            ),
            
            TestCase(
                id="OBS-002",
                title="Inadequate logging configuration",
                description="Application with poor logging setup",
                file_path="deployments/poor-logging.yaml",
                code_content="""apiVersion: apps/v1
kind: Deployment
metadata:
  name: poor-logging
spec:
  replicas: 2
  selector:
    matchLabels:
      app: poor-logging
  template:
    metadata:
      labels:
        app: poor-logging
    spec:
      containers:
      - name: app
        image: app:v1.0
        env:
        - name: LOG_LEVEL
          value: "TRACE"
        - name: LOG_OUTPUT
          value: "/var/log/app.log"
        volumeMounts:
        - name: logs
          mountPath: /var/log
      volumes:
      - name: logs
        emptyDir: {}
""",
                known_errors=[
                    KnownError(
                        line_number=19,
                        error_type="verbose_logging_in_production",
                        description="TRACE log level in production will generate excessive logs",
                        category=ErrorCategory.OBSERVABILITY,
                        severity=ErrorSeverity.MEDIUM,
                        fix_suggestion="Use INFO or WARN level for production logging"
                    ),
                    KnownError(
                        line_number=21,
                        error_type="file_logging_in_container",
                        description="Logging to file instead of stdout/stderr prevents log aggregation",
                        category=ErrorCategory.OBSERVABILITY,
                        severity=ErrorSeverity.HIGH,
                        fix_suggestion="Configure application to log to stdout/stderr for Kubernetes log collection"
                    ),
                    KnownError(
                        line_number=26,
                        error_type="ephemeral_log_storage",
                        description="Using emptyDir for logs means logs are lost when pod restarts",
                        category=ErrorCategory.OBSERVABILITY,
                        severity=ErrorSeverity.MEDIUM,
                        fix_suggestion="Remove file logging or use persistent volume if file logs are necessary"
                    )
                ]
            )
        ]
    
    @staticmethod
    def _get_rbac_test_cases() -> List[TestCase]:
        """RBAC-related test cases"""
        return [
            TestCase(
                id="RBAC-001",
                title="Excessive RBAC permissions",
                description="Service account with more permissions than needed",
                file_path="rbac/excessive-permissions.yaml",
                code_content="""apiVersion: v1
kind: ServiceAccount
metadata:
  name: app-sa
  namespace: default
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: default
  name: app-role
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps", "secrets"]
  verbs: ["get", "list", "create", "update", "patch", "delete"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "create", "update", "patch", "delete"]
- apiGroups: ["extensions"]
  resources: ["ingresses"]
  verbs: ["*"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: app-role-binding
  namespace: default
subjects:
- kind: ServiceAccount
  name: app-sa
  namespace: default
roleRef:
  kind: Role
  name: app-role
  apiGroup: rbac.authorization.k8s.io
""",
                known_errors=[
                    KnownError(
                        line_number=15,
                        error_type="excessive_secret_permissions",
                        description="Application has delete permissions on secrets which is rarely needed",
                        category=ErrorCategory.RBAC,
                        severity=ErrorSeverity.HIGH,
                        fix_suggestion="Remove delete permissions on secrets unless specifically required"
                    ),
                    KnownError(
                        line_number=18,
                        error_type="deployment_modification_permissions",
                        description="Application can modify deployments which may not be necessary",
                        category=ErrorCategory.RBAC,
                        severity=ErrorSeverity.MEDIUM,
                        fix_suggestion="Remove deployment modification permissions unless app manages other deployments"
                    ),
                    KnownError(
                        line_number=21,
                        error_type="wildcard_verbs",
                        description="Wildcard verbs (*) on ingresses grants all possible permissions",
                        category=ErrorCategory.RBAC,
                        severity=ErrorSeverity.HIGH,
                        fix_suggestion="Specify only needed verbs instead of using wildcard"
                    )
                ]
            )
        ]

    @classmethod
    def get_test_case_by_id(cls, test_id: str) -> TestCase:
        """Get a specific test case by ID"""
        all_cases = cls.get_all_test_cases()
        for case in all_cases:
            if case.id == test_id:
                return case
        raise ValueError(f"Test case {test_id} not found")
    
    @classmethod
    def get_test_cases_by_category(cls, category: ErrorCategory) -> List[TestCase]:
        """Get all test cases that contain errors of a specific category"""
        all_cases = cls.get_all_test_cases()
        matching_cases = []
        for case in all_cases:
            if any(error.category == category for error in case.known_errors):
                matching_cases.append(case)
        return matching_cases
    
    @classmethod
    def get_statistics(cls) -> Dict[str, Any]:
        """Get statistics about the test cases"""
        all_cases = cls.get_all_test_cases()
        total_cases = len(all_cases)
        total_errors = sum(len(case.known_errors) for case in all_cases)
        
        category_counts = {}
        severity_counts = {}
        
        for case in all_cases:
            for error in case.known_errors:
                category_counts[error.category.value] = category_counts.get(error.category.value, 0) + 1
                severity_counts[error.severity.value] = severity_counts.get(error.severity.value, 0) + 1
        
        return {
            "total_test_cases": total_cases,
            "total_known_errors": total_errors,
            "errors_by_category": category_counts,
            "errors_by_severity": severity_counts,
            "average_errors_per_case": round(total_errors / total_cases, 2)
        }