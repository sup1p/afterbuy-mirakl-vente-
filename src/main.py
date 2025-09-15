from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.routers.product_router import router as product_router
from src.routers.mirakl_system_router import router as mirakl_system_router
from src.routers.test_router import router as test_router 
from src import resources
import logging
from logs.config_logs import setup_logging

import httpx


setup_logging()

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    resources.client = httpx.AsyncClient()
    try:
        yield
    finally:
        if resources.client:
            await resources.client.aclose()
    
app = FastAPI(lifespan=lifespan)

@app.get("/")
def root():
    logger.info("Root endpoint accessed")
    return "We are live!"

app.include_router(product_router)
app.include_router(mirakl_system_router)
app.include_router(test_router)
