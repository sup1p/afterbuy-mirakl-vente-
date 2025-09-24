"""
Main FastAPI application module.
Handles application lifecycle, HTTP client management, and router registration.
"""

from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.routers.product_router import router as product_router
from src.routers.mirakl_system_router import router as mirakl_system_router
from src.routers.dev_router import router as dev_router 
from src.routers.user_router import router as user_router 
from src import resources
import logging
from logs.config_logs import setup_logging

import httpx

# Initialize logging configuration
setup_logging()

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Initializes HTTP client on startup and properly closes it on shutdown.
    """
    # Initialize global HTTP client
    resources.client = httpx.AsyncClient()
    try:
        yield
    finally:
        # Clean up HTTP client on shutdown
        if resources.client:
            await resources.client.aclose()
    
# Create FastAPI application with lifespan management
app = FastAPI(lifespan=lifespan)

@app.get("/")
def root():
    """Health check endpoint to verify application is running."""
    logger.info("Root endpoint accessed")
    return "We are live!"

# Register all API routers
app.include_router(product_router)
app.include_router(mirakl_system_router)
app.include_router(dev_router)
app.include_router(user_router)
