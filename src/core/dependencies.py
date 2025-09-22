"""
Dependency injection module for FastAPI.
Provides HTTP client instances for API endpoints.
"""

from src import resources
from src.core.settings import settings

import httpx
import aioftp

async def get_httpx_client() -> httpx.AsyncClient:
    """
    Returns the global HTTP client instance.
    Raises RuntimeError if client is not initialized.
    """
    if not resources.client:
        raise RuntimeError("Client not initialized")
    return resources.client
