# Deployment Guide

## 🚀 Deployment Overview

This guide provides comprehensive instructions for deploying the CinBoard AI platform across different environments. The platform uses a microservices architecture with Docker containerization and supports both local development and production deployments.

### Deployment Architecture
- **Containerization**: Docker with Docker Compose for local development
- **Orchestration**: Kubernetes for production scaling
- **Database**: PostgreSQL with Redis caching
- **Storage**: AWS S3 for media files
- **Monitoring**: Prometheus and Grafana
- **CI/CD**: GitHub Actions

## 🛠️ Prerequisites

### System Requirements
- **Operating System**: Linux (Ubuntu 20.04+), macOS, or Windows with WSL2
- **Docker**: Version 20.10+
- **Docker Compose**: Version 2.0+
- **Python**: Version 3.11+ (for local development)
- **Node.js**: Version 18+ (for frontend development)
- **Git**: Version 2.30+

### Required Services
- **PostgreSQL**: Version 14+
- **Redis**: Version 6+
- **AWS S3**: For media storage
- **External AI APIs**: Google Translate, HuggingFace, Whisk AI, Veo4, Eleven Labs

## 🔧 Environment Configuration

### Environment Variables

#### Core Service Configuration
```env
# Service Configuration
SERVICE_NAME=input-processing-service
SERVICE_VERSION=1.0.0
SERVICE_PORT=8002
DEBUG=false

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/input_processing
REDIS_URL=redis://localhost:6379/0

# Security
JWT_SECRET=your_jwt_secret_key_here
ENCRYPTION_KEY=your_encryption_key_here
```

#### AI Service API Keys
```env
# Translation Services - MVP 2-layer system
GOOGLE_TRANSLATE_API_KEY=your_google_translate_api_key
HUGGINGFACE_API_KEY=your_huggingface_api_key
NLLB_ENDPOINT=https://api-inference.huggingface.co/models/facebook/nllb-200-distilled-600M

# TODO (Production Phase): Re-enable IndicTrans2
# INDIC_TRANS2_ENDPOINT=https://api-inference.huggingface.co/models/ai4bharat/indictrans2-indic-en-1B

# GenAI Workflow Services
WHISK_API_KEY=your_whisk_api_key
VEO4_API_KEY=your_veo4_api_key
ELEVEN_LABS_API_KEY=your_eleven_labs_api_key
```

#### AWS Configuration
```env
# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=cinboard-ai-media
S3_BUCKET_REGION=us-east-1
```

#### Monitoring Configuration
```env
# Prometheus & Grafana
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
METRICS_ENABLED=true
LOG_LEVEL=INFO
LOG_FORMAT=json
```

#### Rate Limiting & Caching
```env
# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_PER_HOUR=1000

# Cache TTL Configuration
CACHE_TTL_TRANSLATION=3600
CACHE_TTL_LANGUAGE_DETECTION=1800
CACHE_TTL_VALIDATION=300
CACHE_TTL_CHARACTER=7200
CACHE_TTL_KEYFRAME=1800
CACHE_TTL_VIDEO_CLIP=3600
CACHE_TTL_VOICEOVER=1800
```

## 🐳 Local Development Setup

### 1. Clone Repository
```bash
git clone https://github.com/cinboard-ai/platform.git
cd platform
```

### 2. Input Processing Service Setup ✅ **IMPLEMENTED**

#### Using Docker Compose (Recommended)
```bash
cd input-processing-service

# Copy environment file
cp env.example .env

# Edit environment variables
nano .env

# Start services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f input-processing-service
```

#### Manual Setup
```bash
cd input-processing-service

# Install dependencies
pip install -r requirements.txt

# Set up database
createdb input_processing
psql input_processing < init.sql

# Start Redis
redis-server

# Run service
uvicorn main:app --reload --port 8002
```

### 3. Verify Installation
```bash
# Health check
curl http://localhost:8002/health

# API documentation
open http://localhost:8002/docs

# Test API endpoint
curl -X POST "http://localhost:8002/api/v1/input/process" \
  -H "Content-Type: application/json" \
  -d '{"text": "నాకు ఎగరాలి అని ఉంది", "user_id": 1, "session_id": "test"}'
```

## 🔄 Planned Services Setup

### 4. Scene Analysis Service 🔄 **PLANNED**

#### Docker Setup
```bash
cd scene-analysis-service

# Create Dockerfile
cat > Dockerfile << EOF
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8020

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8020"]
EOF

# Create docker-compose.yml
cat > docker-compose.yml << EOF
version: '3.8'
services:
  scene-analysis-service:
    build: .
    ports:
      - "8020:8020"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/input_processing
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    restart: unless-stopped
EOF

# Start service
docker-compose up -d
```

### 5. Character Generation Service ⚠️ **NEW REQUIREMENT**

#### Environment Configuration
```env
# Character Generation Service
SERVICE_NAME=character-generation-service
SERVICE_PORT=8030
WHISK_API_KEY=your_whisk_api_key
S3_BUCKET_NAME=cinboard-ai-characters
```

#### Docker Setup
```bash
cd character-generation-service

# Create Dockerfile
cat > Dockerfile << EOF
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8030

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8030"]
EOF
```

### 6. Keyframe Generation Service ⚠️ **NEW REQUIREMENT**

#### Environment Configuration
```env
# Keyframe Generation Service
SERVICE_NAME=keyframe-generation-service
SERVICE_PORT=8040
IMAGE_GENERATION_API_KEY=your_image_api_key
S3_BUCKET_NAME=cinboard-ai-keyframes
```

### 7. Video Generation Service 🔄 **PLANNED**

#### Environment Configuration
```env
# Video Generation Service
SERVICE_NAME=video-generation-service
SERVICE_PORT=8050
VEO4_API_KEY=your_veo4_api_key
S3_BUCKET_NAME=cinboard-ai-videos
```

### 8. Voiceover Generation Service ⚠️ **NEW REQUIREMENT**

#### Environment Configuration
```env
# Voiceover Generation Service
SERVICE_NAME=voiceover-generation-service
SERVICE_PORT=8060
ELEVEN_LABS_API_KEY=your_eleven_labs_api_key
S3_BUCKET_NAME=cinboard-ai-voiceovers
```

### 9. Video Composition Service ⚠️ **NEW REQUIREMENT**

#### Environment Configuration
```env
# Video Composition Service
SERVICE_NAME=video-composition-service
SERVICE_PORT=8070
FFMPEG_PATH=/usr/bin/ffmpeg
S3_BUCKET_NAME=cinboard-ai-final-videos
```

## 🏗️ Production Deployment

### Kubernetes Deployment

#### 1. Namespace Configuration
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: cinboard-ai
  labels:
    name: cinboard-ai
```

#### 2. ConfigMap for Environment Variables
```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cinboard-ai-config
  namespace: cinboard-ai
data:
  DATABASE_URL: "postgresql://user:password@postgres:5432/input_processing"
  REDIS_URL: "redis://redis:6379/0"
  LOG_LEVEL: "INFO"
  METRICS_ENABLED: "true"
```

#### 3. Secret for API Keys
```yaml
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: cinboard-ai-secrets
  namespace: cinboard-ai
type: Opaque
data:
  GOOGLE_TRANSLATE_API_KEY: <base64-encoded-key>
  HUGGINGFACE_API_KEY: <base64-encoded-key>
  WHISK_API_KEY: <base64-encoded-key>
  VEO4_API_KEY: <base64-encoded-key>
  ELEVEN_LABS_API_KEY: <base64-encoded-key>
  JWT_SECRET: <base64-encoded-secret>
```

#### 4. Input Processing Service Deployment
```yaml
# k8s/input-processing-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: input-processing-service
  namespace: cinboard-ai
spec:
  replicas: 3
  selector:
    matchLabels:
      app: input-processing-service
  template:
    metadata:
      labels:
        app: input-processing-service
    spec:
      containers:
      - name: input-processing-service
        image: cinboard-ai/input-processing-service:latest
        ports:
        - containerPort: 8002
        envFrom:
        - configMapRef:
            name: cinboard-ai-config
        - secretRef:
            name: cinboard-ai-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8002
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8002
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: input-processing-service
  namespace: cinboard-ai
spec:
  selector:
    app: input-processing-service
  ports:
  - port: 8002
    targetPort: 8002
  type: ClusterIP
```

#### 5. Database Deployment
```yaml
# k8s/postgres.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: cinboard-ai
spec:
  serviceName: postgres
  replicas: 1
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
        image: postgres:15
        env:
        - name: POSTGRES_DB
          value: input_processing
        - name: POSTGRES_USER
          value: user
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: cinboard-ai
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
  type: ClusterIP
```

#### 6. Redis Deployment
```yaml
# k8s/redis.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: cinboard-ai
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: cinboard-ai
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
  type: ClusterIP
```

### AWS Deployment

#### 1. EKS Cluster Setup
```bash
# Create EKS cluster
eksctl create cluster \
  --name cinboard-ai-cluster \
  --version 1.28 \
  --region us-east-1 \
  --nodegroup-name workers \
  --node-type t3.medium \
  --nodes 3 \
  --nodes-min 1 \
  --nodes-max 5 \
  --managed
```

#### 2. RDS PostgreSQL Setup
```bash
# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier cinboard-ai-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15.4 \
  --master-username user \
  --master-user-password your_password \
  --allocated-storage 20 \
  --vpc-security-group-ids sg-12345678 \
  --db-subnet-group-name cinboard-ai-subnet-group
```

#### 3. ElastiCache Redis Setup
```bash
# Create ElastiCache cluster
aws elasticache create-cache-cluster \
  --cache-cluster-id cinboard-ai-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1 \
  --vpc-security-group-ids sg-12345678
```

#### 4. S3 Bucket Setup
```bash
# Create S3 bucket
aws s3 mb s3://cinboard-ai-media --region us-east-1

# Create bucket policies
aws s3api put-bucket-policy \
  --bucket cinboard-ai-media \
  --policy file://s3-bucket-policy.json
```

## 📊 Monitoring and Observability

### Prometheus Configuration
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'input-processing-service'
    static_configs:
      - targets: ['input-processing-service:8002']
    metrics_path: /metrics
    scrape_interval: 5s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

### Grafana Dashboards
```json
{
  "dashboard": {
    "title": "CinBoard AI Platform Metrics",
    "panels": [
      {
        "title": "API Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{service}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      }
    ]
  }
}
```

## 🔒 Security Configuration

### SSL/TLS Setup
```bash
# Generate SSL certificates
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Configure nginx with SSL
server {
    listen 443 ssl;
    server_name api.cinboard.ai;
    
    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;
    
    location / {
        proxy_pass http://input-processing-service:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Network Security
```yaml
# k8s/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: cinboard-ai-network-policy
  namespace: cinboard-ai
spec:
  podSelector:
    matchLabels:
      app: input-processing-service
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: cinboard-ai
    ports:
    - protocol: TCP
      port: 8002
```

## 🚀 CI/CD Pipeline

### GitHub Actions Workflow
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Run tests
      run: |
        cd input-processing-service
        pip install -r requirements.txt
        pytest tests/

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Build Docker image
      run: |
        cd input-processing-service
        docker build -t cinboard-ai/input-processing-service:${{ github.sha }} .
        docker push cinboard-ai/input-processing-service:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
    - name: Deploy to Kubernetes
      run: |
        kubectl set image deployment/input-processing-service \
          input-processing-service=cinboard-ai/input-processing-service:${{ github.sha }} \
          -n cinboard-ai
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Database Connection Issues
```bash
# Check database connectivity
kubectl exec -it postgres-0 -- psql -U user -d input_processing -c "SELECT 1;"

# Check service endpoints
kubectl get endpoints postgres -n cinboard-ai
```

#### 2. Redis Connection Issues
```bash
# Check Redis connectivity
kubectl exec -it redis-xxx -- redis-cli ping

# Check Redis memory usage
kubectl exec -it redis-xxx -- redis-cli info memory
```

#### 3. API Service Issues
```bash
# Check service logs
kubectl logs -f deployment/input-processing-service -n cinboard-ai

# Check service health
kubectl get pods -l app=input-processing-service -n cinboard-ai
```

### Performance Optimization

#### 1. Database Optimization
```sql
-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM input_records WHERE user_id = 1;

-- Check index usage
SELECT schemaname, tablename, attname, n_distinct, correlation 
FROM pg_stats WHERE tablename = 'input_records';
```

#### 2. Redis Optimization
```bash
# Monitor Redis performance
redis-cli --latency-history -i 1

# Check memory usage
redis-cli info memory | grep used_memory_human
```

## 📋 Deployment Checklist

### Pre-Deployment
- [ ] Environment variables configured
- [ ] API keys obtained and validated
- [ ] Database schema initialized
- [ ] SSL certificates generated
- [ ] Monitoring configured
- [ ] Security policies applied

### Deployment
- [ ] Services deployed successfully
- [ ] Health checks passing
- [ ] Database connectivity verified
- [ ] Redis connectivity verified
- [ ] API endpoints responding
- [ ] Monitoring dashboards active

### Post-Deployment
- [ ] Load testing completed
- [ ] Performance metrics baseline established
- [ ] Backup procedures tested
- [ ] Disaster recovery plan validated
- [ ] Documentation updated

---

This deployment guide provides comprehensive instructions for setting up the CinBoard AI platform across different environments, from local development to production deployment.
