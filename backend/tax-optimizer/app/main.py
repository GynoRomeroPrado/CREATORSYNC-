"""
FastAPI main application for Tax Optimizer.
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
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": "2025-11-17T00:00:00Z"
    }


# Include API routes
app.include_router(routes.expense_router, prefix="/api/v1/expenses", tags=["Expenses"])
app.include_router(routes.bank_router, prefix="/api/v1/banks", tags=["Bank Accounts"])
app.include_router(routes.deduction_router, prefix="/api/v1/deductions", tags=["Deductions"])
app.include_router(routes.quarterly_router, prefix="/api/v1/quarterly", tags=["Quarterly Taxes"])
app.include_router(routes.form_router, prefix="/api/v1/forms", tags=["Tax Forms"])
app.include_router(routes.dashboard_router, prefix="/api/v1/dashboard", tags=["Dashboard"])
