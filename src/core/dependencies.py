from src import resources
from src.core.settings import settings

import httpx
import aioftp

async def get_httpx_client() -> httpx.AsyncClient:
    if not resources.client:
        raise RuntimeError("Client not initialized")
    return resources.client

async def get_ftp_client() -> aioftp.Client:
    """
    Возвращает общий FTP-клиент из ресурсов.
    Если клиент ещё не создан, создаёт и подключает его.
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