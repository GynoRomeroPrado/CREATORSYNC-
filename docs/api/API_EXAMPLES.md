# CreatorSync API Examples

Complete examples for using all CreatorSync APIs.

## Table of Contents

1. [Attribution Engine](#attribution-engine)
2. [Tax Optimizer](#tax-optimizer)
3. [Brand CRM](#brand-crm)
4. [Invoice Factoring](#invoice-factoring)

---

## Attribution Engine

Base URL: `http://localhost:8001`

### 1. Create a Creator

```bash
curl -X POST "http://localhost:8001/api/v1/creators/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "creator@example.com",
    "full_name": "Jane Creator"
  }'
```

Response:
```json
{
  "id": 1,
  "email": "creator@example.com",
  "full_name": "Jane Creator",
  "created_at": "2024-11-17T10:00:00Z",
  "is_active": true
}
```

### 2. Sync Platform Data

```bash
curl -X POST "http://localhost:8001/api/v1/sync/creator/1" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "youtube",
    "sync_content": true,
    "sync_income": true
  }'
```

### 3. Run Attribution Analysis

```bash
curl -X POST "http://localhost:8001/api/v1/attributions/run/1"
```

### 4. Generate Income Forecast

```bash
curl -X POST "http://localhost:8001/api/v1/forecast/creator/1" \
  -H "Content-Type: application/json" \
  -d '{
    "horizon_days": 90,
    "platform": "youtube"
  }'
```

Response:
```json
{
  "creator_id": 1,
  "forecast_data": [
    {
      "date": "2024-12-01",
      "predicted_income": 5420.50,
      "confidence_lower": 4200.00,
      "confidence_upper": 6800.00
    }
  ],
  "total_predicted_income": 162615.00,
  "model_version": "v1.0",
  "generated_at": "2024-11-17T10:00:00Z"
}
```

### 5. Get Dashboard Overview

```bash
curl "http://localhost:8001/api/v1/dashboard/creator/1"
```

---

## Tax Optimizer

Base URL: `http://localhost:8002`

### 1. Upload Receipt with OCR

```bash
curl -X POST "http://localhost:8002/api/v1/expenses/upload-receipt" \
  -F "creator_id=1" \
  -F "expense_date=2024-11-01" \
  -F "file=@receipt.jpg"
```

Response:
```json
{
  "expense_id": 1,
  "filename": "receipt.jpg",
  "ocr_text": "AMAZON.COM\nOrder Total: $1,299.00\nDate: 11/01/2024",
  "extracted_data": {
    "total_amount": 1299.00,
    "date": "11/01/2024",
    "vendor": "AMAZON.COM"
  },
  "suggested_category": "equipment",
  "category_confidence": 0.92
}
```

### 2. Create Expense Manually

```bash
curl -X POST "http://localhost:8002/api/v1/expenses/?creator_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 49.99,
    "currency": "USD",
    "category": "software",
    "description": "Adobe Creative Cloud subscription",
    "vendor": "Adobe",
    "expense_date": "2024-11-01"
  }'
```

### 3. Calculate Deductions

```bash
curl -X POST "http://localhost:8002/api/v1/deductions/calculate/1?tax_year=2024"
```

Response:
```json
{
  "tax_year": 2024,
  "total_deductions": 15750.00,
  "by_category": {
    "equipment": {"total": 5000.00, "count": 3},
    "software": {"total": 2400.00, "count": 12},
    "travel": {"total": 3500.00, "count": 5}
  },
  "standard_deduction": 13850.00,
  "recommendation": "itemize"
}
```

### 4. Generate Quarterly Tax Estimate

```bash
curl -X POST "http://localhost:8002/api/v1/quarterly/estimate/1?year=2024&quarter=4"
```

### 5. Generate Schedule C

```bash
curl -X POST "http://localhost:8002/api/v1/forms/schedule-c/1?tax_year=2024" \
  -H "Content-Type: application/json" \
  -d '{
    "business_info": {
      "description": "Content Creator - Digital Media"
    },
    "income_data": {
      "gross_receipts": 120000.00
    },
    "expense_data": {
      "equipment": 5000.00,
      "software": 2400.00,
      "home_office": 3600.00,
      "travel": 3500.00
    }
  }'
```

### 6. Get Tax Dashboard

```bash
curl "http://localhost:8002/api/v1/dashboard/creator/1?tax_year=2024"
```

---

## Brand CRM

Base URL: `http://localhost:8003/graphql`

### 1. Create a Brand

```graphql
mutation {
  createBrand(
    name: "Example Brand"
    website: "https://examplebrand.com"
    industry: "Technology"
    contactEmail: "partnerships@examplebrand.com"
    contactPerson: "John Marketing"
  ) {
    id
    name
    relationshipScore
  }
}
```

### 2. Create a Deal

```graphql
mutation {
  createDeal(
    creatorId: 1
    brandId: 1
    title: "Q4 Product Launch Campaign"
    dealValue: 15000
    description: "3 YouTube videos + 5 Instagram posts"
  ) {
    id
    title
    stage
    probability
    dealValue
  }
}
```

### 3. View Deal Pipeline

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
      dealValue
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

### 4. Update Deal Stage

```graphql
mutation {
  updateDealStage(id: 1, stage: NEGOTIATION) {
    id
    stage
    probability
  }
}
```

### 5. Generate Media Kit

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
      description
    }
    pdfUrl
  }
}
```

### 6. List All Brands

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
      stage
      dealValue
    }
  }
}
```

---

## Invoice Factoring

Base URL: `http://localhost:8004`

### 1. Get Factoring Quote

```bash
curl -X POST "http://localhost:8004/api/v1/offers/quote?creator_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "invoice_amount": 10000,
    "brand_name": "Example Brand",
    "due_date": "2024-12-31",
    "contract_url": "https://storage.example.com/contract.pdf",
    "deal_id": 1
  }'
```

Response:
```json
{
  "eligible": true,
  "risk_score": 85,
  "risk_level": "low",
  "advance_rate": 0.93,
  "advance_amount": 9300.00,
  "factor_fee": 300.00,
  "factor_rate": 3.0,
  "net_advance": 9000.00,
  "estimated_funding_time": "24-48 hours",
  "roi_annual": 18.25,
  "brand_risk_score": 85,
  "brand_payment_history": "11/12 on time"
}
```

### 2. Submit Invoice for Factoring

```bash
curl -X POST "http://localhost:8004/api/v1/invoices/submit?creator_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "invoice_number": "INV-2024-001",
    "invoice_amount": 10000,
    "currency": "USD",
    "brand_name": "Example Brand",
    "brand_email": "accounting@examplebrand.com",
    "brand_id": 1,
    "deal_id": 1,
    "invoice_date": "2024-11-15",
    "due_date": "2024-12-31",
    "invoice_pdf_url": "https://storage.example.com/invoice.pdf",
    "contract_url": "https://storage.example.com/contract.pdf"
  }'
```

Response:
```json
{
  "id": 1,
  "invoice_number": "INV-2024-001",
  "invoice_amount": 10000,
  "status": "pending_review",
  "risk_score": 85,
  "risk_level": "low",
  "advance_rate": 0.93,
  "advance_amount": 9300.00,
  "factor_fee": 300.00,
  "created_at": "2024-11-17T10:00:00Z"
}
```

### 3. Approve Invoice

```bash
curl -X POST "http://localhost:8004/api/v1/invoices/1/approve?approved_by=admin"
```

### 4. Fund Invoice (Send Money to Creator)

```bash
curl -X POST "http://localhost:8004/api/v1/invoices/1/fund?payment_method=stripe"
```

### 5. Get Brand Risk Profile

```bash
curl "http://localhost:8004/api/v1/risk/brand/Example%20Brand"
```

Response:
```json
{
  "id": 1,
  "brand_name": "Example Brand",
  "risk_score": 85,
  "risk_level": "low",
  "total_invoices": 12,
  "paid_on_time": 11,
  "paid_late": 1,
  "defaulted": 0,
  "average_days_to_pay": 28.5,
  "last_assessed": "2024-11-17T10:00:00Z"
}
```

### 6. Get Factoring Dashboard

```bash
curl "http://localhost:8004/api/v1/dashboard/creator/1"
```

Response:
```json
{
  "creator_id": 1,
  "total_available_funding": 250000,
  "active_invoices": 3,
  "pending_collection": 2,
  "total_advanced_ytd": 145000,
  "total_fees_ytd": 4350,
  "average_funding_time": "28.5 hours",
  "recent_invoices": [...],
  "upcoming_collections": [...]
}
```

### 7. Record Payment Received from Brand

```bash
curl -X POST "http://localhost:8004/api/v1/invoices/1/record-payment" \
  -H "Content-Type: application/json" \
  -d '{
    "amount_received": 10000,
    "payment_date": "2024-12-28"
  }'
```

---

## Python SDK Examples

### Attribution Engine

```python
import requests

API_BASE = "http://localhost:8001/api/v1"

# Create creator
response = requests.post(
    f"{API_BASE}/creators/",
    json={
        "email": "creator@example.com",
        "full_name": "Jane Creator"
    }
)
creator = response.json()

# Generate forecast
response = requests.post(
    f"{API_BASE}/forecast/creator/{creator['id']}",
    json={
        "horizon_days": 90,
        "platform": "youtube"
    }
)
forecast = response.json()
print(f"Predicted income: ${forecast['total_predicted_income']:,.2f}")
```

### Tax Optimizer

```python
import requests

API_BASE = "http://localhost:8002/api/v1"

# Upload receipt
with open("receipt.jpg", "rb") as f:
    response = requests.post(
        f"{API_BASE}/expenses/upload-receipt",
        files={"file": f},
        data={
            "creator_id": 1,
            "expense_date": "2024-11-01"
        }
    )
expense = response.json()
print(f"Category: {expense['suggested_category']} (confidence: {expense['category_confidence']})")

# Calculate deductions
response = requests.post(
    f"{API_BASE}/deductions/calculate/1",
    params={"tax_year": 2024}
)
deductions = response.json()
print(f"Total deductions: ${deductions['total_deductions']:,.2f}")
print(f"Recommendation: {deductions['recommendation']}")
```

### Invoice Factoring

```python
import requests

API_BASE = "http://localhost:8004/api/v1"

# Get quote
response = requests.post(
    f"{API_BASE}/offers/quote",
    params={"creator_id": 1},
    json={
        "invoice_amount": 10000,
        "brand_name": "Example Brand",
        "due_date": "2024-12-31"
    }
)
quote = response.json()
print(f"Eligible: {quote['eligible']}")
print(f"Advance: ${quote['net_advance']:,.2f} (fee: ${quote['factor_fee']:,.2f})")
print(f"Risk: {quote['risk_level']} (score: {quote['risk_score']})")
```

---

## JavaScript/TypeScript Examples

```typescript
// Attribution Engine
async function createCreator() {
  const response = await fetch('http://localhost:8001/api/v1/creators/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: 'creator@example.com',
      full_name: 'Jane Creator'
    })
  });
  return response.json();
}

// Brand CRM (GraphQL)
async function createDeal() {
  const query = `
    mutation {
      createDeal(
        creatorId: 1
        brandId: 1
        title: "Product Launch"
        dealValue: 15000
      ) {
        id
        stage
        probability
      }
    }
  `;

  const response = await fetch('http://localhost:8003/graphql', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query })
  });

  const data = await response.json();
  return data.data.createDeal;
}
```

---

For more examples, see the individual module READMEs:
- [Attribution Engine README](../backend/attribution-engine/README.md)
- [Tax Optimizer README](../backend/tax-optimizer/README.md)
- [Brand CRM README](../backend/brand-crm/README.md)
- [Invoice Factoring README](../backend/invoice-factoring/README.md)
