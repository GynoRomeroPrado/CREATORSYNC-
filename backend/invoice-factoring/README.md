# Invoice Factoring - Backend

Sistema de factorización de facturas para adelantos de pago a creadores.

## Características

- **Risk Assessment**: ML-based credit scoring de marcas
- **Invoice Evaluation**: Evaluación automática de facturas
- **Fast Funding**: Adelantos de 80-95% en 24-48h
- **Collections**: Sistema automatizado de cobranza
- **Payment Processing**: Integración con Stripe y ACH
- **KYC/AML**: Verificación de identidad (Jumio/Onfido)

## Stack Tecnológico

- **Framework**: Python FastAPI
- **ML**: scikit-learn, XGBoost (risk scoring)
- **Payments**: Stripe, Plaid
- **Database**: PostgreSQL
- **Cache**: Redis

## Instalación

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# Iniciar servidor
uvicorn app.main:app --reload --port 8004
```

## API Documentation

http://localhost:8004/docs

## Cómo Funciona

### 1. Creador Submits Invoice

```bash
POST /api/v1/invoices/submit
{
  "creator_id": 1,
  "invoice_number": "INV-001",
  "invoice_amount": 5000,
  "brand_name": "Example Brand",
  "invoice_date": "2024-11-01",
  "due_date": "2024-12-01",
  "invoice_pdf_url": "https://..."
}
```

### 2. Automatic Risk Assessment

El sistema evalúa:
- **Brand Risk Score** (0-100): Historial de pagos
- **Invoice Details**: Monto, plazo, documentación
- **Payment History**: Track record de la marca
- **Default Rate**: Ratio de incumplimientos

Resultado:
- Risk Score: 85 (Low Risk)
- Recommended Advance Rate: 93%
- Factor Fee: 3%

### 3. Approval & Funding

```bash
POST /api/v1/invoices/{id}/approve

# Sistema calcula:
# Invoice Amount: $5,000
# Advance Rate: 93% = $4,650
# Factor Fee: 3% = $150
# Net Advance: $4,500
```

Creador recibe **$4,500 en 24-48h**.

### 4. Collections

Cuando la factura vence:
- Sistema cobra $5,000 a la marca
- CreatorSync recupera inversión + fee
- Si hay retraso: automated reminders
- Si 60+ días: escalation to legal

## Endpoints Principales

### Get Factoring Quote

```bash
POST /api/v1/offers/quote
{
  "invoice_amount": 5000,
  "brand_name": "Example Brand",
  "due_date": "2024-12-01"
}

Response:
{
  "eligible": true,
  "risk_score": 85,
  "risk_level": "low",
  "advance_rate": 0.93,
  "advance_amount": 4650,
  "factor_fee": 150,
  "net_advance": 4500,
  "estimated_funding_time": "24-48 hours",
  "roi_annual": 18.25
}
```

### List Invoices

```bash
GET /api/v1/invoices/creator/1?status=funded
```

### Get Risk Profile

```bash
GET /api/v1/risk/brand/Example%20Brand

Response:
{
  "brand_name": "Example Brand",
  "risk_score": 85,
  "risk_level": "low",
  "total_invoices": 12,
  "paid_on_time": 11,
  "paid_late": 1,
  "defaulted": 0,
  "average_days_to_pay": 28.5
}
```

### Dashboard

```bash
GET /api/v1/dashboard/creator/1

Response:
{
  "total_available_funding": 250000,
  "active_invoices": 3,
  "total_advanced_ytd": 45000,
  "total_fees_ytd": 1350,
  "average_funding_time": "36.5 hours",
  "recent_invoices": [...]
}
```

## Risk Scoring Algorithm

### Brand Risk Score (0-100)

```python
score = 100

# Payment History (40% weight)
on_time_rate = paid_on_time / total_invoices
score -= (1 - on_time_rate) * 40

# Default Rate (30% weight)
default_rate = defaulted / total_invoices
score -= default_rate * 30

# Average Days to Pay (20% weight)
if avg_days_to_pay > 0:
    late_penalty = min(avg_days_to_pay / 30, 1.0) * 20
    score -= late_penalty

# Invoice Volume (10% weight)
if total_invoices < 5:
    score -= 10 * (1 - total_invoices / 5)
```

### Advance Rate Calculation

| Risk Level | Risk Score | Advance Rate |
|-----------|------------|--------------|
| Low | 85-100 | 90-95% |
| Medium | 70-84 | 85-90% |
| High | 60-69 | 80-85% |
| Very High | <60 | Not eligible |

### Factor Fee

```
Base Rate: 3% per 30 days
Periods = days_until_due / 30
Total Fee = invoice_amount * 0.03 * periods
```

**Example:**
- Invoice: $10,000
- Due in: 60 days
- Periods: 2
- Fee: $10,000 * 0.03 * 2 = $600 (6%)

## Collections Workflow

### Pre-Due Reminders
- 7 days before: Friendly reminder
- 3 days before: Payment confirmation
- 1 day before: Final notice

### Post-Due Collections
- Day 1: First overdue notice
- Day 7: Second notice (late fees may apply)
- Day 14: Third notice (urgent)
- Day 30: Final notice + late fees
- Day 60: Escalate to legal

### Email Templates

**First Reminder:**
```
Subject: Payment Reminder - Invoice #INV-001

Dear Example Brand,

Invoice #INV-001 for $5,000 was due on 2024-12-01
and is now 5 days overdue.

Please process payment at your earliest convenience.
```

**Final Notice:**
```
Subject: FINAL NOTICE - Invoice #INV-001

Invoice #INV-001 is now 45 days overdue.

Original Amount: $5,000
Late Fees: $75
Total Due: $5,075

Payment must be received within 7 days to avoid legal action.
```

## Payment Processing

### Stripe Integration

```python
# Create Stripe payment
import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

payment_intent = stripe.PaymentIntent.create(
    amount=int(net_advance * 100),  # cents
    currency="usd",
    transfer_data={
        "destination": creator_stripe_account_id
    }
)
```

### ACH Transfer

```python
# Direct bank transfer
plaid_client.create_transfer(
    amount=net_advance,
    account_id=creator_account_id,
    description=f"Invoice factoring - {invoice_number}"
)
```

## KYC/AML Verification

### Required Documents
1. Government ID (passport, driver's license)
2. Proof of address (utility bill, bank statement)
3. Bank account verification (Plaid)

### Verification Flow

```bash
POST /api/v1/kyc/submit
{
  "creator_id": 1,
  "id_document_type": "passport",
  "id_document_url": "https://...",
  "proof_of_address_url": "https://..."
}
```

Jumio/Onfido reviews within 1-24 hours.

## Investor Pool

Factoring is funded by investor pool:

```python
class InvestorPool:
    total_capital: $1,000,000
    available_capital: $750,000
    deployed_capital: $250,000

    # Performance
    total_invested: $5,000,000
    total_returned: $5,750,000
    total_profit: $750,000
    roi_percentage: 15%
```

Investors earn:
- Target Return: 18-24% annual
- Risk-adjusted based on invoice quality
- Diversified across multiple invoices

## Database Schema

### invoices
- id, creator_id, invoice_number
- invoice_amount, currency
- brand_name, brand_id
- invoice_date, due_date
- status (pending, approved, funded, collecting, paid)
- risk_score, risk_level
- advance_rate, advance_amount, factor_fee
- funded_at, collected_at

### brand_risk_profiles
- id, brand_name
- risk_score, risk_level
- total_invoices, paid_on_time, paid_late, defaulted
- average_days_to_pay

### payments
- id, invoice_id, creator_id
- amount, currency, status
- payment_method, transaction_id
- stripe_payment_id

### collection_attempts
- id, invoice_id
- attempt_number, method
- sent_to, message_content
- attempted_at

## Testing

```bash
pytest
```

## Deployment

```bash
# Build
docker build -t invoice-factoring .

# Run
docker run -p 8004:8004 invoice-factoring
```

## Compliance

- ✅ KYC/AML regulations (Bank Secrecy Act)
- ✅ Fair Debt Collection Practices Act (FDCPA)
- ✅ Truth in Lending Act (TILA)
- ✅ Payment Card Industry Data Security Standard (PCI DSS)
- ✅ General Data Protection Regulation (GDPR)

## Financial Model

### Revenue
- Factor fees: 3-5% per 30 days
- Late fees: 1.5% per month
- Origination fees: $50-100 per invoice

### Costs
- Capital cost: 8-12% APR
- Default provision: 2-5%
- Operations: 1-2%
- Collections: 0.5-1%

### Net Margin
Target: 6-10% per invoice

## License

MIT
