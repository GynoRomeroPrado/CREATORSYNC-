"""
FastAPI main application for Invoice Factoring.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import routes

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "description": "Invoice factoring service for creators"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": "2025-11-17T00:00:00Z"
    }


# Include API routes
app.include_router(routes.invoice_router, prefix="/api/v1/invoices", tags=["Invoices"])
app.include_router(routes.offer_router, prefix="/api/v1/offers", tags=["Offers"])
app.include_router(routes.payment_router, prefix="/api/v1/payments", tags=["Payments"])
app.include_router(routes.collection_router, prefix="/api/v1/collections", tags=["Collections"])
app.include_router(routes.risk_router, prefix="/api/v1/risk", tags=["Risk Assessment"])
app.include_router(routes.dashboard_router, prefix="/api/v1/dashboard", tags=["Dashboard"])
