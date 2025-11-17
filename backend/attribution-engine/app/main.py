"""
FastAPI main application for the Attribution Engine.
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
app.include_router(routes.creator_router, prefix="/api/v1/creators", tags=["Creators"])
app.include_router(routes.content_router, prefix="/api/v1/content", tags=["Content"])
app.include_router(routes.income_router, prefix="/api/v1/income", tags=["Income"])
app.include_router(routes.attribution_router, prefix="/api/v1/attributions", tags=["Attributions"])
app.include_router(routes.forecast_router, prefix="/api/v1/forecast", tags=["Forecast"])
app.include_router(routes.dashboard_router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(routes.sync_router, prefix="/api/v1/sync", tags=["Sync"])
