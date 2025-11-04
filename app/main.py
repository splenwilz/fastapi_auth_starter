"""
FastAPI application entry point
Main application factory and configuration
Reference: https://fastapi.tiangolo.com/tutorial/bigger-applications/
"""
from fastapi import FastAPI

from app.api.v1.api import api_router
from app.core.config import settings


# Create FastAPI application instance
# Reference: https://fastapi.tiangolo.com/reference/fastapi/
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="A clean architecture FastAPI starter with PostgreSQL and Alembic",
    docs_url="/docs",  # Swagger UI documentation
    redoc_url="/redoc",  # ReDoc documentation
)


# Include API routers
# All routes from api_router will be included in the main app
app.include_router(api_router)


@app.get("/")
async def root():
    """
    Root endpoint
    Provides basic information about the API
    """
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "docs": "/docs",
    }

