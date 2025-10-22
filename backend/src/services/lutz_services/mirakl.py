# app/services/mirakl.py
import httpx
import logging
from src.core.settings import settings

from logs.config_logs import setup_logging

setup_logging()

logger = logging.getLogger(__name__)


async def upload_csv(csv_content: str) -> dict:
    """
    Асинхронно отправляем CSV в Mirakl.
    """
    # Подготавливаем файлы и данные для загрузки
    files = {"file": ("products.csv", csv_content, "text/csv")}
    payload = {
        "conversion_options[ai_enrichment][status]": "ENABLED",
        "conversion_options[ai_rewrite][status]": "ENABLED",
        "operator_format": "true",
        "shop": settings.shop_id_lutz,
        "with_products": "true"
    }
    headers = {"Authorization": settings.mirakl_api_key_lutz, "Accept": "application/json"}

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(settings.mirakl_url_lutz, data=payload, files=files, headers=headers)
        if response.status_code != 201:
            logger.error("Ошибка импорта в Mirakl: %s", response.text)
            response.raise_for_status()
        return response.json()


async def upload_price_csv(csv_content: str) -> dict:
    """
    Асинхронно отправляем CSV с ценой в Mirakl.
    """
    # Подготавливаем файлы и данные для загрузки цен
    files = {"file": ("products.csv", csv_content, "text/csv")}
    payload = {
        "conversion_options[ai_enrichment][status]": "ENABLED",
        "conversion_options[ai_rewrite][status]": "ENABLED",
        "import_mode": "NORMAL",
        "operator_format": "true",
        "shop": settings.shop_id_lutz,
        "with_products": "true"
    }
    headers = {"Authorization": settings.mirakl_api_key_lutz,   "Accept": "application/json"}

    logger.info(f"--- Offer Upload Request ---")
    logger.info(f"URL: {settings.mirakl_price_url_lutz}")
    logger.info(f"Payload: {payload}")

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(settings.mirakl_price_url_lutz, data=payload, files=files, headers=headers)
        
        logger.info(f"--- Offer Upload Response ---")
        logger.info(f"Status Code: {response.status_code}")
        logger.info(f"Body: {response.text}")

        if response.status_code != 201:
            logger.error("Ошибка импорта в Mirakl: %s", response.text)
            response.raise_for_status()
        return response.json()
