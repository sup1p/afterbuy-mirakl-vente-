from fastapi import Depends
from src import resources
import httpx

async def get_client() -> httpx.AsyncClient:
    if not resources.client:
        raise RuntimeError("Client not initialized")
    return resources.client