"""
Main FastAPI application module.
Handles application lifecycle, HTTP client management, and router registration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager


from src.routers.vente.product_vente_router import router as product_vente_router
from src.routers.vente.mirakl_system_vente_router import router as mirakl_system_vente_router
from src.routers.vente.dev_vente_router import router as dev_vente_router 

from src.routers.user_router import router as user_router
from src.routers.fabric_management import router as fabric_management_router
from src.routers.lutz.fabric_lutz_router import router as fabric_lutz_router
from src.routers.lutz.generate_csv_lutz_router import router as generate_csv_lutz_router
from src.routers.lutz.offers_lutz_router import router as offers_lutz_router
from src.routers.lutz.product_lutz_router import router as product_lutz_router

from src.services.vente_services.agents import create_agent_with_httpx
from src import resources
import logging
from logs.config_logs import setup_logging

import httpx
import asyncio

# Initialize logging configuration
setup_logging()

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Initializes HTTP client and LLM agent on startup,
    and properly closes them on shutdown.
    """
    # --- startup ---
    resources.client = httpx.AsyncClient()
    resources.llm_semaphore = asyncio.Semaphore(8)
    resources.ftp_semaphore = asyncio.Semaphore(8)
    logger.info("Startup: ftp and llm semaphore initialized")
    
    try:
        # инициализируем глобальный агент (он сохранится в resources.llm_agent)
        await create_agent_with_httpx(
            resources.client
        )

        logger.info("Startup: httpx client, OpenAI client and LLM agent initialized")
        

        yield

    finally:
        # --- shutdown ---
        try:
            if resources.openai_client:
                await resources.openai_client.close()
                logger.info("Shutdown: OpenAI client closed")
        except Exception:
            logger.exception("Shutdown: closing OpenAI client failed")

        try:
            if resources.client:
                await resources.client.aclose()
                logger.info("Shutdown: HTTP client closed")
        except Exception:
            logger.exception("Shutdown: closing HTTP client failed")

        # cleanup globals
        resources.client = None
        resources.openai_client = None
        resources.llm_agent = None
        resources.llm_semaphore = None
        resources.ftp_semaphore = None

        logger.info("Shutdown: resources cleaned up")
    
# Create FastAPI application with lifespan management
app = FastAPI(lifespan=lifespan)

origins = ['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # кому разрешаем
    allow_credentials=True,           # отправка куков / авторизации
    allow_methods=["*"],              # какие методы (GET, POST...) разрешены
    allow_headers=["*"],              # какие заголовки разрешены
)

@app.get("/")
def root():
    """Health check endpoint to verify application is running."""
    logger.info("Root endpoint accessed")
    return "We are live!"

# Register all API routers
# mutual
app.include_router(user_router)
app.include_router(fabric_management_router)
# vente
app.include_router(product_vente_router)
# app.include_router(mirakl_system_vente_router)
# app.include_router(dev_vente_router)
# lutz
# app.include_router(product_lutz_router)
# app.include_router(offers_lutz_router)
# app.include_router(generate_csv_lutz_router)
app.include_router(fabric_lutz_router)

# ЭТО НУЖНО ЗАМЕРДЖИТЬ !!!
# app/main.py
from fastapi import FastAPI
from app.logging_config import setup_logging
from app.routers import product, fabric, offers, generate_csv, afterbuy_fabric, local_importer

# Set up logging
setup_logging()

app = FastAPI(title="Midlmiddleware API")

# Подключаем роутеры
app.include_router(product.router, prefix="/api", tags=["Products"])
app.include_router(fabric.router, prefix="/api", tags=["Fabrics"])
app.include_router(afterbuy_fabric.router, prefix="/api", tags=["Afterbuy Fabrics"])
app.include_router(offers.router, prefix="/api", tags=["Offers"])
app.include_router(generate_csv.router, prefix="/api", tags=["CSV Generation"])
app.include_router(local_importer.router, prefix="/api", tags=["Local Importer"])


@app.get("/")
async def root():
    return {"status": "ok", "message": "Server is running"}
