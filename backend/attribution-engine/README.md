# Attribution Engine - Backend

Motor de atribución de ingresos para CreatorSync.

## Características

- **Tracking multi-plataforma**: YouTube, TikTok, Instagram, Twitch, Patreon
- **Correlación automática**: Views/engagement → ingresos
- **Análisis predictivo**: Forecasting con Prophet (3-6 meses)
- **Reconciliación automática**: Match de pagos con contenido específico
- **API REST completa**: FastAPI con documentación automática

## Stack Tecnológico

- **Framework**: FastAPI
- **Database**: PostgreSQL
- **Cache**: Redis
- **Queue**: Apache Kafka
- **Search**: Elasticsearch
- **ML**: XGBoost (attribution), Prophet (forecasting)
- **Async Tasks**: Celery

## Instalación

### Requisitos

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Kafka 3+

### Setup

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Copiar configuración
cp .env.example .env

# Editar .env con tus API keys

# Ejecutar migraciones
alembic upgrade head

# Iniciar servidor
uvicorn app.main:app --reload
```

## Uso

### API Documentation

Una vez que el servidor esté corriendo, visita:

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

### Ejemplos de API

#### Crear un creador

```bash
curl -X POST "http://localhost:8001/api/v1/creators/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "creator@example.com",
    "full_name": "John Creator"
  }'
```

#### Sincronizar datos de YouTube

```bash
curl -X POST "http://localhost:8001/api/v1/sync/creator/1" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "youtube",
    "sync_content": true,
    "sync_income": true
  }'
```

#### Ejecutar atribución

```bash
curl -X POST "http://localhost:8001/api/v1/attributions/run/1"
```

#### Generar forecast

```bash
curl -X POST "http://localhost:8001/api/v1/forecast/creator/1" \
  -H "Content-Type: application/json" \
  -d '{
    "horizon_days": 90,
    "platform": "youtube"
  }'
```

## Celery Workers

Para procesar tareas en background:

```bash
# Worker principal
celery -A app.celery_app worker --loglevel=info

# Beat scheduler (para tareas periódicas)
celery -A app.celery_app beat --loglevel=info

# Flower (monitoreo de tareas)
celery -A app.celery_app flower
```

## Database Migrations

```bash
# Crear nueva migración
alembic revision --autogenerate -m "descripción del cambio"

# Aplicar migraciones
alembic upgrade head

# Revertir migración
alembic downgrade -1
```

## Testing

```bash
# Ejecutar tests
pytest

# Con coverage
pytest --cov=app --cov-report=html
```

## Estructura del Proyecto

```
attribution-engine/
├── app/
│   ├── api/              # Endpoints REST
│   ├── core/             # Configuración
│   ├── db/               # Modelos y database
│   ├── integrations/     # Integraciones con plataformas
│   ├── ml/               # Modelos de ML
│   ├── services/         # Lógica de negocio
│   └── tasks/            # Tareas de Celery
├── tests/                # Tests
├── alembic/              # Migraciones
├── ml-models/            # Modelos entrenados
└── Dockerfile            # Container config
```

## Integraciones de Plataformas

### YouTube

Requiere YouTube Data API v3 key. Obtén una en:
https://console.cloud.google.com/

### TikTok

Requiere TikTok Developer account y OAuth tokens:
https://developers.tiktok.com/

### Configuración de API Keys

Todas las API keys se configuran en el archivo `.env`:

```env
YOUTUBE_API_KEY=tu_key_aqui
TIKTOK_CLIENT_KEY=tu_key_aqui
TIKTOK_CLIENT_SECRET=tu_secret_aqui
```

## Machine Learning

### Attribution Model

El modelo de atribución usa XGBoost para predecir qué contenido generó qué ingresos.

Features utilizados:
- Diferencia temporal entre contenido e ingreso
- Views, likes, comments
- Engagement rate
- Watch time
- Tipo de contenido

### Forecasting Model

Usa Facebook Prophet para predecir ingresos futuros basándose en:
- Histórico de ingresos
- Estacionalidad (semanal, anual)
- Tendencias

## Contribuir

1. Fork el repositorio
2. Crea una branch (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Añadir nueva funcionalidad'`)
4. Push a la branch (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request

## License

MIT
