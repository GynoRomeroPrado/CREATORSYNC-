# Brand CRM - Backend

Sistema CRM especializado para gestión de brand partnerships y deals de creadores.

## Características

- **Pipeline Management**: Kanban visual de deals (Outreach → Payment)
- **Brand Database**: Base de datos de marcas con relationship scoring
- **Deal Tracking**: Gestión completa del ciclo de vida de deals
- **Contract Management**: Integración con DocuSign para e-signatures
- **Media Kit Generator**: Generación automática de media kits con stats actualizados
- **Deliverable Tracking**: Seguimiento de entregables por deal
- **Performance Reporting**: Reports para brands

## Stack Tecnológico

- **Framework**: Node.js + Express
- **API**: GraphQL (Apollo Server + Type-GraphQL)
- **Database**: PostgreSQL + TypeORM
- **Cache**: Redis
- **E-signatures**: DocuSign API
- **Email**: Nodemailer

## Instalación

```bash
# Instalar dependencias
npm install

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# Iniciar en desarrollo
npm run dev

# Build para producción
npm run build
npm start
```

## GraphQL API

### Endpoints

- **GraphQL Playground**: http://localhost:8003/graphql
- **Health Check**: http://localhost:8003/health

### Ejemplos de Queries

#### Listar Brands

```graphql
query {
  brands(creatorId: 1) {
    id
    name
    industry
    relationshipScore
    deals {
      id
      title
      dealValue
      stage
    }
  }
}
```

#### Ver Pipeline de Deals

```graphql
query {
  dealPipeline(creatorId: 1) {
    outreach {
      id
      title
      dealValue
      brand {
        name
      }
    }
    negotiation {
      id
      title
    }
    contract {
      id
      title
    }
    totalValue
    dealCount
  }
}
```

#### Crear Deal

```graphql
mutation {
  createDeal(
    creatorId: 1
    brandId: 5
    title: "Product Launch Campaign"
    dealValue: 5000
    description: "3 videos + 5 stories"
  ) {
    id
    title
    stage
    probability
  }
}
```

#### Generar Media Kit

```graphql
mutation {
  generateMediaKit(creatorId: 1) {
    id
    title
    platformStats {
      platform
      followers
      avgViews
      engagementRate
    }
    rateCards {
      contentType
      price
      currency
    }
    pdfUrl
  }
}
```

#### Actualizar Stage de Deal

```graphql
mutation {
  updateDealStage(id: 10, stage: NEGOTIATION) {
    id
    stage
    probability
  }
}
```

## Stages de Deals

1. **Outreach** (25% probability)
   - Initial contact con brand
   - Envío de media kit

2. **Negotiation** (50%)
   - Discusión de términos
   - Pricing y deliverables

3. **Contract** (75%)
   - Review de contrato
   - E-signature con DocuSign

4. **Delivery** (90%)
   - Creación de contenido
   - Approval de deliverables

5. **Payment** (95%)
   - Invoice sent
   - Awaiting payment

6. **Completed** (100%)
   - Payment received
   - Deal closed

7. **Lost** (0%)
   - Deal no cerró

## Media Kit Generator

El generador automático de media kits:

1. Fetch stats del Attribution Engine
2. Calcula engagement rates
3. Genera rate cards basado en followers/engagement
4. Incluye case studies de deals anteriores
5. Export a PDF profesional

### Estructura de Media Kit

```typescript
{
  title: "Creator Name - Media Kit",
  bio: "Professional creator bio",
  platformStats: [
    {
      platform: "YouTube",
      followers: 50000,
      avgViews: 10000,
      engagementRate: 5.2
    }
  ],
  caseStudies: [
    {
      brand: "Example Brand",
      campaign: "Product Launch",
      views: 100000,
      engagement: 8500,
      result: "45% increase in brand awareness"
    }
  ],
  rateCards: [
    {
      contentType: "YouTube - Dedicated Video",
      price: 2500,
      currency: "USD"
    }
  ]
}
```

## DocuSign Integration

### Setup

1. Create DocuSign Developer account
2. Get Integration Key
3. Generate RSA keypair
4. Configure .env with credentials

### Envío de Contratos

```graphql
mutation {
  sendContractForSignature(
    dealId: 10
    recipientEmail: "brand@example.com"
    recipientName: "Brand Manager"
  ) {
    envelopeId
    status
  }
}
```

## Relationship Scoring

El sistema calcula un relationship score (0-100) basado en:

- Número de deals completados
- Total revenue generado
- Tiempo de response
- Payment punctuality
- Renewal rate

## Database Schema

### Brands

- id, name, website, industry
- contact_email, contact_person
- relationship_score
- metadata (JSONB)

### Deals

- id, creator_id, brand_id
- title, description, deal_value
- stage, status, probability
- contract_url, signed_contract_url
- docusign_envelope_id

### Deliverables

- id, deal_id
- title, description, type
- status, due_date
- content_url, platform_content_id

### Media Kits

- id, creator_id
- title, bio
- platform_stats (JSONB)
- case_studies (JSONB)
- rate_cards (JSONB)
- pdf_url

## Testing

```bash
npm test
```

## Deployment

```bash
# Build
npm run build

# Start production server
NODE_ENV=production npm start
```

## License

MIT
