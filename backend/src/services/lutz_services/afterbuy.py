# app/services/afterbuy.py
import httpx
import logging
import time
from src.core.settings import settings

from logs.config_logs import setup_logging

setup_logging()

logger = logging.getLogger(__name__)

# --- глобальный кэш токена ---
_token_cache: dict = {
    "access_token": None,
    "expires_at": 0,   # timestamp (epoch seconds), когда токен протухнет
}


async def get_token() -> str:
    """
    Возвращает валидный access_token из кэша или обновляет его.
    """
    global _token_cache
    now = time.time()

    # Проверяем, есть ли токен в кэше и не истек ли он
    if _token_cache["access_token"] and now < _token_cache["expires_at"]:
        logger.debug("Используем access_token из кэша, жив до %s", _token_cache["expires_at"])
        return _token_cache["access_token"]

    logger.info("Кэшированный access_token отсутствует или истёк. Запрашиваем новый...")

    # Подготавливаем данные для запроса токена
    payload = {
        "login": settings.afterbuy_login,
        "password": settings.afterbuy_password,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(f"{settings.afterbuy_url}/v1/auth/login", json=payload)
        if response.status_code != 200:
            logger.error("Ошибка получения токена: %s", response.text)
            response.raise_for_status()
        data = response.json()

    token = data.get("access_token")
    if not token:
        logger.error("Токен не найден в ответе: %s", data)
        raise ValueError("Afterbuy не вернул access_token")

    # Устанавливаем время истечения токена (по умолчанию 1 час)
    expires_in = 3600  # по умолчанию 1 час
    _token_cache["access_token"] = token
    _token_cache["expires_at"] = now + int(expires_in) - 30  # -30 сек запас

    logger.info("Получен новый access_token, срок действия ~%s секунд (до %s)", expires_in, _token_cache["expires_at"])
    return token


async def fetch_product(product_id: str) -> dict:
    """
    Асинхронно тянем JSON продукта по ID из Afterbuy с автоматическим получением токена.
    """
    # Получаем токен для авторизации
    token = await get_token()
    headers = {"access-token": token}
    url = f"{settings.afterbuy_url}/v1/products/{product_id}"

    logger.debug("Запрос продукта %s: GET %s", product_id, url)

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            logger.error("Ошибка получения продукта %s из Afterbuy: %s", product_id, response.text)
            response.raise_for_status()
        logger.debug("Успешно получен продукт %s", product_id)
        return response.json()


async def fetch_products_by_fabric(fabric_id: int) -> list[str]:
    """
    Запрашиваем товары по fabric_id через Afterbuy Filter API и возвращаем список product_ids.
    """
    # Получаем токен для авторизации
    token = await get_token()
    headers = {"access-token": token}
    payload = {"fabric_id": fabric_id}

    logger.debug("Запрос товаров по fabric_id=%s: POST %s", fabric_id, f"{settings.afterbuy_url}/v1/products/filter")

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(f"{settings.afterbuy_url}/v1/products/filter", json=payload, headers=headers)
        if response.status_code != 200:
            logger.error("Ошибка фильтрации по fabric_id=%s: %s", fabric_id, response.text)
            response.raise_for_status()
        data = response.json()

    # Обрабатываем ответ и извлекаем product_ids
    if isinstance(data, list):
        product_ids = [str(item["id"]) for item in data if isinstance(item, dict) and "id" in item]
    elif isinstance(data, dict):
        product_ids = [str(item["id"]) for item in data.get("products", []) if "id" in item]
    else:
        product_ids = []

    logger.info("Найдено %s товаров для fabric_id=%s", len(product_ids), fabric_id)
    return product_ids