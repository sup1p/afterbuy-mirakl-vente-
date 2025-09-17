"""
Dependency injection module for FastAPI.
Provides HTTP and FTP client instances for API endpoints.
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

async def get_ftp_client() -> aioftp.Client:
    """
    Returns the global FTP client instance.
    If client is not created yet, creates and connects it.
    """
    if resources.ftp_client is None:
        client = aioftp.Client()
        await client.connect(
            host=settings.ftp_host,
            port=settings.ftp_port
        )
        await client.login(
            settings.ftp_user,
            settings.ftp_password
        )
        resources.ftp_client = client
    return resources.ftp_client