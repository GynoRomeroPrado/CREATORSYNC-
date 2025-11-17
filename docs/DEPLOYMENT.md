# CreatorSync - Production Deployment Guide

This guide covers deploying CreatorSync to production environments using various platforms.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Configuration](#environment-configuration)
3. [Database Setup](#database-setup)
4. [Docker Deployment](#docker-deployment)
5. [Kubernetes Deployment](#kubernetes-deployment)
6. [AWS Deployment](#aws-deployment)
7. [Monitoring & Logging](#monitoring--logging)
8. [Security Hardening](#security-hardening)
9. [Backup & Recovery](#backup--recovery)
10. [Scaling Strategies](#scaling-strategies)

---

## Prerequisites

### Required Services

- **Database**: PostgreSQL 15+ (AWS RDS, Google Cloud SQL, or self-hosted)
- **Cache**: Redis 7+ (AWS ElastiCache, Google Memorystore, or self-hosted)
- **Message Queue**: Apache Kafka 3+ (AWS MSK, Confluent Cloud, or self-hosted)
- **Search**: Elasticsearch 8+ (AWS OpenSearch, Elastic Cloud, or self-hosted)
- **Container Registry**: Docker Hub, AWS ECR, or Google Container Registry
- **Domain**: Registered domain with SSL certificate

### Required Tools

```bash
# Install required CLI tools
docker >= 24.0
docker-compose >= 2.20
kubectl >= 1.28  # For Kubernetes deployment
aws-cli >= 2.0   # For AWS deployment
terraform >= 1.5 # Optional: Infrastructure as Code
```

---

## Environment Configuration

### 1. Create Production Environment Files

For each service, create `.env` files from `.env.example`:

```bash
# Attribution Engine
cp backend/attribution-engine/.env.example backend/attribution-engine/.env.production

# Tax Optimizer
cp backend/tax-optimizer/.env.example backend/tax-optimizer/.env.production

# Brand CRM
cp backend/brand-crm/.env.example backend/brand-crm/.env.production

# Invoice Factoring
cp backend/invoice-factoring/.env.example backend/invoice-factoring/.env.production

# Frontend
cp frontend/web-app/.env.example frontend/web-app/.env.production
```

### 2. Configure Production Variables

#### Attribution Engine `.env.production`

```bash
# Database - Use managed PostgreSQL (RDS, Cloud SQL)
DATABASE_URL=postgresql://user:password@prod-db.example.com:5432/creatorsync

# Redis - Use managed Redis (ElastiCache, Memorystore)
REDIS_URL=redis://prod-redis.example.com:6379/0

# Kafka - Use managed Kafka (MSK, Confluent Cloud)
KAFKA_BOOTSTRAP_SERVERS=kafka-1.prod.example.com:9092,kafka-2.prod.example.com:9092

# Elasticsearch
ELASTICSEARCH_URL=https://prod-elasticsearch.example.com:9200

# Platform API Keys (from secure secrets manager)
YOUTUBE_API_KEY=${YOUTUBE_API_KEY}
TIKTOK_CLIENT_KEY=${TIKTOK_CLIENT_KEY}
TIKTOK_CLIENT_SECRET=${TIKTOK_CLIENT_SECRET}

# Security
SECRET_KEY=${STRONG_RANDOM_SECRET_KEY}
DEBUG=False
APP_ENV=production

# CORS - Your production domains
CORS_ORIGINS=https://app.creatorsync.com,https://www.creatorsync.com

# Monitoring
SENTRY_DSN=${SENTRY_DSN}
```

### 3. Use Secrets Manager

**AWS Secrets Manager Example:**

```bash
# Store secrets in AWS Secrets Manager
aws secretsmanager create-secret \
  --name creatorsync/production/youtube-api-key \
  --secret-string "your-youtube-api-key"

aws secretsmanager create-secret \
  --name creatorsync/production/database-url \
  --secret-string "postgresql://user:password@host:5432/db"
```

**In application, retrieve secrets:**

```python
import boto3
import json

def get_secret(secret_name):
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    return response['SecretString']

# Use in code
YOUTUBE_API_KEY = get_secret('creatorsync/production/youtube-api-key')
```

---

## Database Setup

### 1. Create Production Database

```bash
# Using AWS RDS (PostgreSQL)
aws rds create-db-instance \
  --db-instance-identifier creatorsync-prod \
  --db-instance-class db.r6g.xlarge \
  --engine postgres \
  --engine-version 15.4 \
  --master-username creatorsync \
  --master-user-password ${DB_PASSWORD} \
  --allocated-storage 100 \
  --storage-type gp3 \
  --backup-retention-period 30 \
  --preferred-backup-window "03:00-04:00" \
  --multi-az \
  --publicly-accessible false \
  --vpc-security-group-ids sg-xxxxxxxx
```

### 2. Run Database Migrations

```bash
# Attribution Engine migrations
cd backend/attribution-engine
alembic upgrade head

# Tax Optimizer migrations
cd backend/tax-optimizer
alembic upgrade head

# Invoice Factoring migrations
cd backend/invoice-factoring
alembic upgrade head

# Brand CRM migrations
cd backend/brand-crm
npm run typeorm migration:run
```

### 3. Create Database Indexes

```sql
-- Performance indexes for high-traffic queries
CREATE INDEX CONCURRENTLY idx_income_creator_date
ON income(creator_id, income_date DESC);

CREATE INDEX CONCURRENTLY idx_content_creator_platform
ON content(creator_id, platform, published_at DESC);

CREATE INDEX CONCURRENTLY idx_deals_creator_stage
ON deals(creator_id, stage, created_at DESC);

CREATE INDEX CONCURRENTLY idx_invoices_creator_status
ON invoices(creator_id, status, created_at DESC);
```

---

## Docker Deployment

### 1. Build Production Images

```bash
# Build all images with production tag
docker build -t creatorsync/attribution:1.0.0 backend/attribution-engine/
docker build -t creatorsync/tax-optimizer:1.0.0 backend/tax-optimizer/
docker build -t creatorsync/brand-crm:1.0.0 backend/brand-crm/
docker build -t creatorsync/invoice-factoring:1.0.0 backend/invoice-factoring/
docker build -t creatorsync/frontend:1.0.0 frontend/web-app/
```

### 2. Push to Container Registry

```bash
# Tag for registry
docker tag creatorsync/attribution:1.0.0 your-registry.com/creatorsync/attribution:1.0.0

# Push to registry
docker push your-registry.com/creatorsync/attribution:1.0.0
# Repeat for all services
```

### 3. Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  attribution-api:
    image: your-registry.com/creatorsync/attribution:1.0.0
    restart: always
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G

  # ... other services
```

### 4. Deploy with Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.prod.yml creatorsync

# Scale services
docker service scale creatorsync_attribution-api=5
```

---

## Kubernetes Deployment

### 1. Create Kubernetes Manifests

**Deployment example** (`k8s/attribution-deployment.yaml`):

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: attribution-api
  namespace: creatorsync
spec:
  replicas: 3
  selector:
    matchLabels:
      app: attribution-api
  template:
    metadata:
      labels:
        app: attribution-api
        version: v1.0.0
    spec:
      containers:
      - name: attribution-api
        image: your-registry.com/creatorsync/attribution:1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: creatorsync-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: creatorsync-secrets
              key: redis-url
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: attribution-api
  namespace: creatorsync
spec:
  selector:
    app: attribution-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
```

### 2. Create Ingress for HTTPS

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: creatorsync-ingress
  namespace: creatorsync
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - api.creatorsync.com
    secretName: creatorsync-tls
  rules:
  - host: api.creatorsync.com
    http:
      paths:
      - path: /api/v1/attribution
        pathType: Prefix
        backend:
          service:
            name: attribution-api
            port:
              number: 80
```

### 3. Deploy to Kubernetes

```bash
# Create namespace
kubectl create namespace creatorsync

# Create secrets
kubectl create secret generic creatorsync-secrets \
  --from-literal=database-url="${DATABASE_URL}" \
  --from-literal=redis-url="${REDIS_URL}" \
  --namespace=creatorsync

# Apply manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n creatorsync
kubectl logs -f deployment/attribution-api -n creatorsync
```

---

## AWS Deployment

### Architecture Overview

```
Internet
    ↓
CloudFront (CDN)
    ↓
Application Load Balancer
    ↓
ECS/Fargate (Containers)
    ↓
RDS PostgreSQL + ElastiCache Redis + MSK Kafka
```

### 1. Infrastructure with Terraform

Create `terraform/main.tf`:

```hcl
provider "aws" {
  region = "us-east-1"
}

# VPC
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.0"

  name = "creatorsync-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["us-east-1a", "us-east-1b", "us-east-1c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway = true
  enable_vpn_gateway = false
}

# RDS PostgreSQL
resource "aws_db_instance" "main" {
  identifier        = "creatorsync-db"
  engine            = "postgres"
  engine_version    = "15.4"
  instance_class    = "db.r6g.xlarge"
  allocated_storage = 100
  storage_type      = "gp3"

  db_name  = "creatorsync"
  username = "creatorsync"
  password = var.db_password

  multi_az             = true
  publicly_accessible  = false
  storage_encrypted    = true

  backup_retention_period = 30
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
}

# ElastiCache Redis
resource "aws_elasticache_cluster" "main" {
  cluster_id           = "creatorsync-redis"
  engine               = "redis"
  engine_version       = "7.0"
  node_type            = "cache.r6g.large"
  num_cache_nodes      = 2
  parameter_group_name = "default.redis7"
  port                 = 6379

  subnet_group_name    = aws_elasticache_subnet_group.main.name
  security_group_ids   = [aws_security_group.redis.id]
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "creatorsync-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# ECS Task Definition
resource "aws_ecs_task_definition" "attribution_api" {
  family                   = "attribution-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "1024"
  memory                   = "2048"
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "attribution-api"
      image     = "${var.ecr_repository_url}/attribution:1.0.0"
      essential = true

      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "APP_ENV"
          value = "production"
        }
      ]

      secrets = [
        {
          name      = "DATABASE_URL"
          valueFrom = aws_secretsmanager_secret.database_url.arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/attribution-api"
          "awslogs-region"        = "us-east-1"
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])
}

# ECS Service
resource "aws_ecs_service" "attribution_api" {
  name            = "attribution-api"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.attribution_api.arn
  desired_count   = 3
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = module.vpc.private_subnets
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.attribution_api.arn
    container_name   = "attribution-api"
    container_port   = 8000
  }
}
```

### 2. Deploy with Terraform

```bash
cd terraform/

# Initialize
terraform init

# Plan
terraform plan -out=tfplan

# Apply
terraform apply tfplan
```

### 3. Configure Auto-Scaling

```bash
# ECS Auto Scaling
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/creatorsync-cluster/attribution-api \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10

aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --resource-id service/creatorsync-cluster/attribution-api \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name cpu-scaling-policy \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    }
  }'
```

---

## Monitoring & Logging

### 1. Application Monitoring with Sentry

```python
# In app initialization
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    environment="production",
    traces_sample_rate=0.1,
    integrations=[FastApiIntegration()]
)
```

### 2. Metrics with Prometheus

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'attribution-api'
    static_configs:
      - targets: ['attribution-api:8000']
    metrics_path: '/metrics'
```

### 3. Logging with ELK Stack

```yaml
# filebeat.yml
filebeat.inputs:
  - type: container
    paths:
      - '/var/lib/docker/containers/*/*.log'

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "creatorsync-%{+yyyy.MM.dd}"
```

### 4. Dashboards with Grafana

Create dashboards for:
- Request rate & latency
- Error rates
- Database performance
- Cache hit rates
- ML model inference time

---

## Security Hardening

### 1. Network Security

```bash
# Security groups - Allow only necessary ports
aws ec2 create-security-group \
  --group-name creatorsync-api \
  --description "CreatorSync API servers"

# Allow HTTPS only
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxx \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0
```

### 2. SSL/TLS Configuration

```nginx
# nginx.conf
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers HIGH:!aNULL:!MD5;
ssl_prefer_server_ciphers on;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

### 3. API Rate Limiting

```python
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

@app.on_event("startup")
async def startup():
    redis_conn = await aioredis.from_url("redis://localhost")
    await FastAPILimiter.init(redis_conn)

@app.get("/api/v1/creators", dependencies=[Depends(RateLimiter(times=100, seconds=60))])
async def get_creators():
    pass
```

### 4. Database Encryption

```sql
-- Enable encryption at rest
ALTER DATABASE creatorsync SET DEFAULT_TABLESPACE = pg_default;

-- Encrypt sensitive columns
CREATE EXTENSION IF NOT EXISTS pgcrypto;

UPDATE creators
SET email = pgp_sym_encrypt(email, 'encryption-key');
```

---

## Backup & Recovery

### 1. Database Backups

```bash
# Automated RDS snapshots (already configured)
# Manual snapshot
aws rds create-db-snapshot \
  --db-instance-identifier creatorsync-prod \
  --db-snapshot-identifier creatorsync-manual-$(date +%Y%m%d)

# Point-in-time recovery
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier creatorsync-prod \
  --target-db-instance-identifier creatorsync-restored \
  --restore-time 2024-01-15T10:00:00Z
```

### 2. Redis Persistence

```conf
# redis.conf
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec
```

### 3. Disaster Recovery Plan

1. **RTO (Recovery Time Objective)**: 2 hours
2. **RPO (Recovery Point Objective)**: 15 minutes
3. **Failover procedure**: Documented in wiki
4. **Backup verification**: Weekly automated tests

---

## Scaling Strategies

### Horizontal Scaling

```bash
# Scale API services
kubectl scale deployment attribution-api --replicas=10

# Scale database read replicas
aws rds create-db-instance-read-replica \
  --db-instance-identifier creatorsync-replica-1 \
  --source-db-instance-identifier creatorsync-prod
```

### Vertical Scaling

```bash
# Upgrade instance class
aws rds modify-db-instance \
  --db-instance-identifier creatorsync-prod \
  --db-instance-class db.r6g.2xlarge \
  --apply-immediately
```

### Caching Strategy

- **L1**: In-memory cache (TTL: 5 min)
- **L2**: Redis cache (TTL: 1 hour)
- **L3**: Database query cache

### CDN Configuration

```javascript
// CloudFront distribution
{
  "Origins": [{
    "DomainName": "api.creatorsync.com",
    "CustomOriginConfig": {
      "HTTPSPort": 443,
      "OriginProtocolPolicy": "https-only"
    }
  }],
  "CacheBehaviors": [{
    "PathPattern": "/static/*",
    "MinTTL": 86400,
    "DefaultTTL": 31536000
  }]
}
```

---

## Health Checks

All services must implement:

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "checks": {
            "database": await check_database(),
            "redis": await check_redis(),
            "kafka": await check_kafka()
        }
    }
```

---

## Maintenance Mode

```bash
# Enable maintenance mode
kubectl apply -f k8s/maintenance-page.yaml

# Route traffic to maintenance page
kubectl patch ingress creatorsync-ingress \
  --type=json \
  -p='[{"op": "replace", "path": "/spec/rules/0/http/paths/0/backend/service/name", "value": "maintenance"}]'
```

---

## Rollback Procedure

```bash
# Kubernetes rollback
kubectl rollout undo deployment/attribution-api

# ECS rollback
aws ecs update-service \
  --cluster creatorsync-cluster \
  --service attribution-api \
  --task-definition attribution-api:previous-version
```

---

## Checklist Before Production

- [ ] All secrets moved to secrets manager
- [ ] Database backups configured and tested
- [ ] SSL certificates installed
- [ ] Monitoring & alerting configured
- [ ] Auto-scaling policies set
- [ ] Load testing completed
- [ ] Security audit passed
- [ ] Disaster recovery plan documented
- [ ] Rate limiting configured
- [ ] CORS configured for production domains
- [ ] CI/CD pipeline tested
- [ ] Rollback procedure tested
- [ ] Health checks working
- [ ] Logging aggregation working
- [ ] Documentation updated

---

## Support

For deployment issues:
- Email: devops@creatorsync.com
- Slack: #creatorsync-infrastructure
- On-call: PagerDuty rotation
