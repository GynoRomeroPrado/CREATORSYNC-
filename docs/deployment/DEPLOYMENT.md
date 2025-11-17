# CreatorSync - Guía de Deployment

## Requisitos Previos

### Software
- Docker 24.0+
- Docker Compose 2.20+
- Node.js 20+
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Apache Kafka 3+

### Servicios Cloud (Producción)
- AWS/GCP/Azure account
- Domain name con DNS configurado
- SSL certificates
- Email service (SendGrid/AWS SES)

## Desarrollo Local

### 1. Clonar Repositorio

```bash
git clone https://github.com/your-org/creatorsync.git
cd creatorsync
```

### 2. Configurar Variables de Entorno

```bash
# Backend
cd backend/attribution-engine
cp .env.example .env
# Editar .env con tus API keys

# Frontend
cd ../../frontend/web-app
cp .env.example .env
```

### 3. Iniciar Infraestructura

```bash
# Desde el root del proyecto
docker-compose up -d postgres redis kafka elasticsearch
```

### 4. Iniciar Backend

```bash
cd backend/attribution-engine

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar migraciones
alembic upgrade head

# Iniciar servidor
uvicorn app.main:app --reload --port 8001
```

### 5. Iniciar Celery Workers

```bash
# En otra terminal
cd backend/attribution-engine
source venv/bin/activate

# Worker
celery -A app.celery_app worker --loglevel=info

# Beat scheduler (en otra terminal)
celery -A app.celery_app beat --loglevel=info
```

### 6. Iniciar Frontend

```bash
cd frontend/web-app

# Instalar dependencias
npm install

# Iniciar dev server
npm run dev
```

### 7. Acceder a la Aplicación

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs

## Deployment con Docker Compose

### Producción Simple (Single Server)

```bash
# Build y start todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f

# Restart servicios
docker-compose restart

# Stop
docker-compose down
```

### Configuración de Producción

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  postgres:
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - /var/lib/postgresql/data:/var/lib/postgresql/data

  attribution-api:
    image: creatorsync/attribution-api:latest
    environment:
      DATABASE_URL: ${DATABASE_URL}
      SECRET_KEY: ${SECRET_KEY}
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

## Deployment en Kubernetes

### 1. Crear Namespace

```bash
kubectl create namespace creatorsync
```

### 2. Configurar Secrets

```bash
kubectl create secret generic creatorsync-secrets \
  --from-literal=database-url=postgresql://... \
  --from-literal=secret-key=... \
  --from-literal=youtube-api-key=... \
  -n creatorsync
```

### 3. Deploy PostgreSQL

```bash
kubectl apply -f k8s/postgres.yaml -n creatorsync
```

### 4. Deploy Redis

```bash
kubectl apply -f k8s/redis.yaml -n creatorsync
```

### 5. Deploy Attribution Engine

```bash
kubectl apply -f k8s/attribution-api.yaml -n creatorsync
kubectl apply -f k8s/attribution-worker.yaml -n creatorsync
```

### 6. Deploy Frontend

```bash
kubectl apply -f k8s/web-app.yaml -n creatorsync
```

### 7. Configurar Ingress

```bash
kubectl apply -f k8s/ingress.yaml -n creatorsync
```

## Configuración de CI/CD

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy

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
          cd backend/attribution-engine
          pip install -r requirements.txt
          pytest

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Docker image
        run: |
          docker build -t creatorsync/attribution-api:${{ github.sha }} \
            backend/attribution-engine
      - name: Push to registry
        run: docker push creatorsync/attribution-api:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/attribution-api \
            attribution-api=creatorsync/attribution-api:${{ github.sha }} \
            -n creatorsync
```

## Base de Datos

### Backups Automáticos

```bash
# Backup script (backup.sh)
#!/bin/bash
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

pg_dump -h localhost -U creatorsync creatorsync | \
  gzip > $BACKUP_DIR/creatorsync_$TIMESTAMP.sql.gz

# Mantener solo últimos 30 días
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
```

```bash
# Agregar a crontab
0 2 * * * /path/to/backup.sh
```

### Restore

```bash
gunzip < backup.sql.gz | psql -h localhost -U creatorsync creatorsync
```

## Monitoreo

### Prometheus + Grafana

```bash
# Deploy Prometheus
kubectl apply -f k8s/monitoring/prometheus.yaml

# Deploy Grafana
kubectl apply -f k8s/monitoring/grafana.yaml

# Acceder a Grafana
kubectl port-forward svc/grafana 3000:3000 -n creatorsync
```

### Sentry (Error Tracking)

```python
# En app/main.py
import sentry_sdk

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    environment=settings.ENVIRONMENT
)
```

## SSL/TLS

### Let's Encrypt con cert-manager

```bash
# Instalar cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Configurar ClusterIssuer
kubectl apply -f k8s/cert-issuer.yaml
```

## Escalado

### Horizontal Pod Autoscaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: attribution-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: attribution-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Troubleshooting

### Ver Logs de un Pod

```bash
kubectl logs -f deployment/attribution-api -n creatorsync
```

### Conectar a Base de Datos

```bash
kubectl port-forward svc/postgres 5432:5432 -n creatorsync
psql -h localhost -U creatorsync creatorsync
```

### Restart Deployment

```bash
kubectl rollout restart deployment/attribution-api -n creatorsync
```

### Ver Estado del Cluster

```bash
kubectl get all -n creatorsync
```

## Performance Optimization

### Database Tuning

```sql
-- Crear índices para queries frecuentes
CREATE INDEX CONCURRENTLY idx_content_creator_published
  ON content(creator_id, published_at DESC);

CREATE INDEX CONCURRENTLY idx_income_creator_date
  ON income(creator_id, income_date DESC);

-- Vacuum regular
VACUUM ANALYZE;
```

### Redis Optimization

```bash
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
```

## Security Checklist

- [ ] Cambiar todos los passwords por defecto
- [ ] Configurar firewall (solo puertos necesarios)
- [ ] Habilitar SSL/TLS en todos los servicios
- [ ] Configurar rate limiting
- [ ] Implementar API authentication
- [ ] Encriptar secrets en Kubernetes
- [ ] Configurar network policies
- [ ] Habilitar audit logging
- [ ] Configurar backups automáticos
- [ ] Implementar disaster recovery plan

## Recursos

### Documentación
- [FastAPI](https://fastapi.tiangolo.com/)
- [Next.js](https://nextjs.org/docs)
- [Kubernetes](https://kubernetes.io/docs/)
- [PostgreSQL](https://www.postgresql.org/docs/)

### Soporte
- GitHub Issues: https://github.com/your-org/creatorsync/issues
- Email: support@creatorsync.com
- Slack: creatorsync.slack.com
