# Tax Optimizer - Backend

Sistema de optimización fiscal automatizado para creadores de contenido.

## Características

- **OCR de recibos**: Extracción automática de datos con Tesseract
- **Categorización automática**: ML para categorizar gastos
- **Cálculo de deducciones**: Deducciones específicas para creadores
- **Formularios fiscales**: Generación de 1099-NEC, Schedule C, W-9
- **Estimaciones trimestrales**: Cálculo automático de impuestos
- **Integración bancaria**: Plaid para importar transacciones

## Stack Tecnológico

- **Framework**: FastAPI
- **OCR**: Tesseract OCR / AWS Textract
- **ML**: scikit-learn (categorización)
- **PDF Generation**: ReportLab
- **Banking**: Plaid API

## Instalación

```bash
# Instalar dependencias del sistema (Linux/Mac)
sudo apt-get install tesseract-ocr tesseract-ocr-eng poppler-utils

# Crear entorno virtual
python -m venv venv
source venv/bin/activate

# Instalar dependencias de Python
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# Iniciar servidor
uvicorn app.main:app --reload --port 8002
```

## Uso

### API Documentation

http://localhost:8002/docs

### Ejemplos de API

#### Subir un recibo

```bash
curl -X POST "http://localhost:8002/api/v1/expenses/upload-receipt" \
  -F "creator_id=1" \
  -F "expense_date=2024-11-01" \
  -F "file=@receipt.jpg"
```

#### Calcular deducciones

```bash
curl -X POST "http://localhost:8002/api/v1/deductions/calculate/1?tax_year=2024"
```

#### Generar estimación trimestral

```bash
curl -X POST "http://localhost:8002/api/v1/quarterly/estimate/1?year=2024&quarter=4"
```

#### Generar Schedule C

```bash
curl -X POST "http://localhost:8002/api/v1/forms/schedule-c/1?tax_year=2024" \
  -H "Content-Type: application/json" \
  -d '{
    "business_info": {"description": "Content Creator"},
    "income_data": {"gross_receipts": 100000},
    "expense_data": {"equipment": 5000, "software": 2000}
  }'
```

## Categorías de Gastos

El sistema reconoce las siguientes categorías:

- **Equipment**: Cámaras, computadoras, micrófonos
- **Software**: Suscripciones, herramientas
- **Travel**: Viajes de negocio
- **Meals**: Comidas de negocio
- **Home Office**: Gastos de oficina en casa
- **Utilities**: Internet, teléfono
- **Advertising**: Publicidad pagada
- **Professional Services**: Contador, abogado
- **Education**: Cursos, capacitación
- **Insurance**: Seguros de negocio
- **Supplies**: Materiales generales

## OCR y Procesamiento de Recibos

El sistema utiliza:

1. **Preprocesamiento**: Escala de grises, threshold, denoise
2. **Tesseract OCR**: Extracción de texto
3. **Parsing**: Extrae total, fecha, vendor
4. **Categorización ML**: Asigna categoría automáticamente

## Cálculos Fiscales

### Deducciones

- Cálculo por categoría
- Porcentajes de deducción personalizables
- Comparación itemized vs standard deduction

### Impuestos Trimestrales

- Federal income tax (brackets 2024)
- Self-employment tax (15.3%)
- State tax (configurable)

### Home Office

- **Método simplificado**: $5/sq ft (max 300 sq ft)
- **Método actual**: Porcentaje de gastos del hogar

## Formularios Fiscales

### 1099-NEC

Para ingresos de marcas/sponsors > $600

### Schedule C

Profit or Loss from Business

### W-9

Request for Taxpayer ID

## Integración con Plaid

```python
# Conectar cuenta bancaria
POST /api/v1/banks/connect
{
  "creator_id": 1,
  "plaid_public_token": "..."
}
```

## Testing

```bash
pytest
```

## Estructura

```
tax-optimizer/
├── app/
│   ├── api/              # Endpoints REST
│   ├── core/             # Configuración
│   ├── db/               # Modelos de base de datos
│   ├── services/         # Lógica de negocio
│   │   ├── ocr_service.py
│   │   ├── categorizer_service.py
│   │   ├── tax_calculation_service.py
│   │   └── tax_form_generator.py
│   └── tasks/            # Tareas de Celery
├── uploads/              # Recibos subidos
├── generated_forms/      # PDFs generados
└── ml-models/            # Modelos ML entrenados
```

## Compliance

- IRS guidelines 2024
- State tax laws
- Data encryption at rest
- PII handling

## License

MIT
