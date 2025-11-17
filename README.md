# CreatorSync - Sistema Operativo Financiero para Creadores

> Gestión financiera all-in-one para creadores: atribución de ingresos multi-plataforma, optimización fiscal, CRM de marcas, factorización de facturas.

## 🎯 Overview

CreatorSync es una plataforma integral que ayuda a creadores de contenido a gestionar todos los aspectos financieros de su negocio en un solo lugar.

### Mercado Objetivo

- **Economía creadora**: $104-500B
- **64M+** creadores en YouTube
- **165M+** creadores totales
- **28%** de Gen Z son creadores

## 🚀 Características Principales

### 1. Motor de Atribución de Ingresos
- Tracking multi-plataforma (YouTube, TikTok, Instagram, Twitch, Patreon)
- Correlación views/engagement → ingresos
- Análisis predictivo (forecasting 3-6 meses)
- Dashboard unificado en tiempo real

### 2. Optimización Fiscal
- Categorización automática de gastos con OCR
- Deducciones específicas para creadores
- Cálculo automático de impuestos trimestrales
- Generación de formularios (1099s, Schedule C)

### 3. CRM de Brand Deals
- Pipeline management completo
- Generador de media kits automático
- Contract management con e-signatures
- Performance reporting para brands
- Relationship scoring con ML

### 4. Factorización de Facturas
- Risk assessment con ML
- Adelanto de 80-95% del valor de facturas
- Transferencia en 24-48h
- Sistema de collections automatizado

## 🏗️ Arquitectura

### Tech Stack

#### Backend
- **Attribution Engine**: Python + FastAPI + Celery
- **Tax Optimizer**: Python + Temporal
- **Brand CRM**: Node.js + GraphQL
- **Invoice Factoring**: Python + FastAPI

#### Infrastructure
- **Message Queue**: Apache Kafka
- **Databases**: PostgreSQL + Redis + Elasticsearch
- **ML/AI**: XGBoost (attribution), Prophet (forecasting), scikit-learn (risk)

#### Frontend
- **Web App**: React + TypeScript
- **UI Framework**: Tailwind CSS + shadcn/ui
- **State Management**: React Query + Zustand

### Estructura del Proyecto

```
creatorsync/
├── backend/
│   ├── attribution-engine/     # Sistema de atribución (Python FastAPI)
│   ├── tax-optimizer/          # Sistema fiscal (Python)
│   ├── brand-crm/              # CRM (Node.js GraphQL)
│   ├── invoice-factoring/      # Factoring (Python)
│   └── shared/                 # Código compartido
├── frontend/
│   ├── web-app/                # React + TypeScript
│   └── shared-ui/              # Componentes compartidos
├── infrastructure/
│   ├── kafka/                  # Apache Kafka config
│   ├── postgres/               # Database schemas
│   ├── elasticsearch/          # Search config
│   └── docker/                 # Docker configs
├── ml-models/
│   ├── attribution/            # XGBoost models
│   ├── forecasting/            # Prophet models
│   └── risk-assessment/        # Risk scoring
└── docs/
    ├── api/                    # API documentation
    ├── architecture/           # System architecture
    └── deployment/             # Deployment guides
```

## 🚦 Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 20+
- PostgreSQL 15+
- Redis 7+
- Kafka 3+

### Quick Start (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-org/creatorsync.git
cd creatorsync

# Run automated setup script
chmod +x setup.sh
./setup.sh
```

The setup script will:
- Check prerequisites (Docker, Python, Node.js)
- Create environment files from templates
- Start all infrastructure services (PostgreSQL, Redis, Kafka, Elasticsearch)
- Build and start all 4 backend services
- Start the frontend application

### Manual Installation

```bash
# Start infrastructure services
docker-compose up -d postgres redis zookeeper kafka elasticsearch

# Backend setup (for each module)
cd backend/attribution-engine  # or tax-optimizer, brand-crm, invoice-factoring
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend setup
cd frontend/web-app
npm install
npm run dev
```

### Access the Application

After setup, services will be available at:

- **Attribution Engine API**: http://localhost:8001/docs
- **Tax Optimizer API**: http://localhost:8002/docs
- **Brand CRM GraphQL**: http://localhost:8003/graphql
- **Invoice Factoring API**: http://localhost:8004/docs
- **Frontend Web App**: http://localhost:3000

For detailed API examples, see [API_EXAMPLES.md](docs/api/API_EXAMPLES.md)

## 📊 Roadmap

- [x] Arquitectura base del proyecto
- [x] **Phase 1**: Motor de Atribución de Ingresos
  - [x] API integrations (YouTube, TikTok, Instagram, Twitch, Patreon)
  - [x] Income correlation engine (XGBoost ML)
  - [x] Predictive analytics (Prophet forecasting)
  - [x] Unified dashboard
- [x] **Phase 2**: Sistema de Optimización Fiscal
  - [x] OCR de recibos (Tesseract)
  - [x] Categorización automática con ML
  - [x] Cálculo de deducciones
  - [x] Generación de formularios (1099-NEC, Schedule C, W-9)
- [x] **Phase 3**: CRM de Brand Deals
  - [x] Pipeline management (Kanban)
  - [x] Brand database con relationship scoring
  - [x] Generador de media kits automático
  - [x] Contract tracking con DocuSign
- [x] **Phase 4**: Factorización de Facturas
  - [x] ML-based risk assessment
  - [x] Invoice submission & approval workflow
  - [x] 80-95% advance calculation
  - [x] Payment processing integration (Stripe)
  - [x] Automated collections system
  - [x] Brand risk profiling
- [x] **Infrastructure & DevOps**
  - [x] Docker Compose multi-service setup
  - [x] Automated setup scripts
  - [x] API documentation & examples
  - [x] Contributing guidelines

## ✨ Project Status

**🎉 Version 1.0.0 - Complete**

All 4 core modules are fully implemented and operational:
- ✅ 94+ files created
- ✅ ~10,000 lines of code
- ✅ Complete API documentation
- ✅ Automated setup & deployment
- ✅ Production-ready infrastructure

## 📝 License

MIT License - see LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Please read CONTRIBUTING.md for details.

## 📧 Contact

For questions or support, reach out to team@creatorsync.com
