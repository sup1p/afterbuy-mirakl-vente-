"""
Модуль интеграции с Afterbuy API.
Обрабатывает аутентификацию, получение данных о продуктах и информации о брендах из Afterbuy API.
"""

from fastapi import HTTPException
from src.core.settings import settings
from src.const.constants_vente.constants import ban_keywords_for_fabrics
from logs.config_logs import setup_logging

from typing import Optional
from pathlib import Path

import httpx
import logging
import time
import asyncio
import json

from src.services.lutz_services import afterbuy

setup_logging()
logger = logging.getLogger(__name__)

# Глобальные переменные для управления токенами
# _access_token используется для хранения текущего токена доступа.
# _access_token_expiry хранит время истечения токена в формате Unix.
# _access_token_lock обеспечивает синхронизацию при обновлении токена.

_access_token = None
_access_token_expiry = 0  # Unix timestamp
_access_token_lock = asyncio.Lock()


async def get_access_token(httpx_client: httpx.AsyncClient):
    """
    Получает и кэширует токен доступа к Afterbuy API.

    Функция использует глобальные переменные для хранения токена и времени его истечения.
    Если токен уже существует и действителен, возвращается кэшированное значение.
    В противном случае выполняется новый запрос на аутентификацию к API Afterbuy.

    Аргументы:
        httpx_client (httpx.AsyncClient): Асинхронный HTTP-клиент для выполнения запросов.

    Возвращает:
        str: Действительный токен доступа.

    Исключения:
        Exception: Если токен не может быть получен из-за сетевой ошибки,
            недействительного статуса ответа или пустых данных ответа.
    """
    
    global _access_token, _access_token_expiry
    
    async with _access_token_lock:
        # Если токен существует и не истек, возвращаем его
        if _access_token and time.time() < _access_token_expiry:
            logger.debug(f"Используется кэшированный токен доступа, который истечет через {_access_token_expiry - time.time():.0f} секунд")
            return _access_token

        credentials = {
            "login": settings.afterbuy_login,
            "password": settings.afterbuy_password,
        }

        logger.info("Запрос токена доступа к Afterbuy")
        
        try:
            response = await httpx_client.post(f"{settings.afterbuy_url}/v1/auth/login", json=credentials, timeout=40.0)
                
        except Exception as e:
            logger.error(f"Ошибка при запросе токена доступа: {e}")
            raise Exception(f"Ошибка при запросе токена доступа у Afterbuy: {e}")
            
        if response.status_code != 200:
            logger.error(f"Не удалось получить токен доступа: {response.status_code} - {response.text}")
            raise Exception(
                f"Не удалось получить токен доступа у Afterbuy: {response.status_code} - {response.text}"
            )
        data = response.json()
        
        if not data:
            logger.error("Не получены данные при получении токена доступа")
            raise Exception("Не получены данные при получении токена доступа у Afterbuy")
        
        _access_token = data["access_token"]
        expires_in = 1000
        _access_token_expiry = time.time() + expires_in - 10  # -10 секунд буфер для безопасности

        return _access_token


async def get_product_data(ean: int, httpx_client: httpx.AsyncClient, afterbuy_fabric_id: Optional[int] = None):
    """
    Получает данные о продукте из Afterbuy API по EAN.

    Функция запрашивает информацию о продукте из Afterbuy, используя действительный токен доступа.
    Если в настройках включено, также запрашивается реальное HTML-описание продукта.
    Если указан afterbuy_fabric_id, выполняется фильтрация продукта по EAN и FABRIC_ID.

    Аргументы:
        ean (int): EAN продукта (Европейский артикул).
        httpx_client (httpx.AsyncClient): Асинхронный HTTP-клиент для выполнения запросов.

    Возвращает:
        dict: Данные о продукте, включая метаданные и, опционально, HTML-описание.

    Исключения:
        Exception: Если токен доступа не может быть получен,
            запрос к Afterbuy не удался,
            статус ответа не 200,
            данные о продукте отсутствуют
            или получение HTML-описания завершилось ошибкой.
    """
    
    try:
        access_token = await get_access_token(httpx_client=httpx_client) 
    except Exception as e:
        raise e
    
    headers = {"access-token": access_token}
    
    data = {
        "ean": str(ean)
    }
    
    if afterbuy_fabric_id:
        fabric_data = await get_fabric_id_by_afterbuy_id(afterbuy_fabric_id=afterbuy_fabric_id, httpx_client=httpx_client)
        data["fabric_id"] = fabric_data.get("id")

    limit = 100
    
    logger.debug(f"Получен токен доступа, выполняется запрос для ean {ean}")
    
    try:
        response = await httpx_client.post(
            f"{settings.afterbuy_url}/v1/products/filter?limit={limit}", headers=headers, json=data, timeout=40.0
        )
        logger.debug(f"{settings.afterbuy_url}/v1/products/filter?limit={limit} _-------------- {data}")
    except Exception as e:
        logger.error(f"Ошибка при запросе данных о продукте: {e}")
        raise Exception(
            f"Ошибка при запросе данных о продукте у Afterbuy: {e}",
        )

    if response.status_code != 200:
        logger.error(f"Не удалось получить данные о продукте: {response.status_code} - {response.text}")
        raise Exception(
            f"Ошибка получения данных у Afterbuy: {response.status_code} - {response.text}",
        )

    data = response.json()
    
    if not data:
        logger.error(f"Продукт с ean {ean} не найден в Afterbuy")
        raise Exception(
            f"Продукт с ean {ean} не найден в Afterbuy",
        )
    
    logger.debug(f"Данные ответа содержат для ean {ean}: {data}")   
    
    if isinstance(data, list) and data[0].get('id'):
        try:
            data[0]['html_description'] = await _get_product_html_desc(data[0].get('id'), httpx_client)
        except Exception as e:
            raise e
        
        logger.debug(f"Успешно получены данные о продукте для product_num: {data[0].get('product_num')} с EAN: {data[0].get('ean')}")
        
    elif isinstance(data, dict) and data.get('id'):
        try:
            data['html_description'] = await _get_product_html_desc(data.get('id'), httpx_client)
        except Exception as e:
            raise e
        
        logger.debug(f"Успешно получены данные о продукте для product_num: {data.get('product_num')} с EAN: {data.get('ean')}")
        
    else:
        raise Exception(
            f"Не удалось получить html-описание для продукта с ean {ean}",
        )
    
    return data[0] if isinstance(data, list) else data


async def get_products_by_fabric(afterbuy_fabric_id: int, httpx_client: httpx.AsyncClient):
    """
    Получает все продукты, связанные с определенным идентификатором ткани, из Afterbuy API.

    Функция сначала определяет внутренний идентификатор ткани по предоставленному идентификатору ткани Afterbuy.
    Затем она запрашивает все связанные продукты у Afterbuy, применяя логику повторных попыток для надежности.
    Для каждого продукта, при необходимости, данные дополнительно обогащаются HTML-описанием, полученным
    параллельно с использованием семафора для ограничения параллельности.

    Аргументы:
        afterbuy_fabric_id (int): Идентификатор ткани, используемый в Afterbuy.
        httpx_client (httpx.AsyncClient): Асинхронный HTTP-клиент для выполнения запросов к API.

    Возвращает:
        dict: Словарь, содержащий:
            - "products" (list[dict]): Успешно полученные и обогащенные данные о продуктах.
            - "not_added_eans" (list[str]): Список EAN для продуктов, которые не удалось обработать.

    Исключения:
        Exception: Если не удается получить токен доступа,
            если запрос к Afterbuy многократно не удается,
            если продукты отсутствуют,
            или если обогащение продукта сталкивается с необработанными ошибками.
    """
    logger.info(f"get_products_and_data_by_fabric с afterbuy_fabric_id: {afterbuy_fabric_id} был вызван")
    
    fabric_data = await get_fabric_id_by_afterbuy_id(afterbuy_fabric_id, httpx_client)
    fabric_id = fabric_data.get("id")
    fabric_name = fabric_data.get("name")
    
    try:
        access_token = await get_access_token(httpx_client=httpx_client) 
    except Exception as e:
        raise e
    
    headers = {"access-token": access_token}
    
    data = {
        "fabric_id": str(fabric_id)
    }

    limit = 3000
    
    logger.debug(f"Получен токен доступа, выполняется запрос для fabric_id {fabric_id}")
    
    # Логика повторных попыток для основного запроса
    for attempt in range(3):
        try:
            response = await httpx_client.post(
                f"{settings.afterbuy_url}/v1/products/filter?limit={limit}", headers=headers, json=data, timeout=40.0
            )
            if response.status_code == 200:
                break
        except Exception as e:
            if attempt == 2:  # Последняя попытка
                logger.error(f"Ошибка при запросе продуктов по fabric_id: {e}")
                raise Exception(f"Ошибка при запросе продуктов по fabric_id у Afterbuy: {e}")
            await asyncio.sleep(1 * (attempt + 1))  # Экспоненциальная задержка
    else:
        logger.error(f"Не удалось получить продукты по fabric_id: {response.status_code} - {response.text}")
        raise Exception(f"Ошибка получения данных у Afterbuy по fabric_id: {response.status_code} - {response.text}")

    data = response.json()
    
    if not data:
        logger.error(f"Продукты не найдены для fabric_id {fabric_id} в Afterbuy")
        raise Exception(f"Продукты не найдены для fabric_id {fabric_id} в Afterbuy")
    
    logger.debug(f"Данные ответа содержат {len(data)} продуктов для fabric_id {fabric_id}")
    
    full_data = []
    not_added_eans = []
    
    if isinstance(data, list):
        
        semaphore = asyncio.Semaphore(10)  # Ограничение до 10 параллельных запросов
        
        async def enrich_product(product):
            product_ean = product.get("ean", "Нет EAN")
            if not product.get("id"):
                return (product_ean, None)
            try:
                async with semaphore:
                    # Логика повторных попыток для описания продукта
                    for attempt in range(3):
                        try:
                            product["html_description"] = await _get_product_html_desc(product["id"], httpx_client)
                            break
                        except Exception as e:
                            if attempt == 2:
                                raise e
                            await asyncio.sleep(0.5 * (attempt + 1))
                return (product_ean, product)
            except Exception as e:
                logger.error(f"Ошибка при получении html-описания для продукта {product.get('id')}: {e}")
                return (product_ean, e)
                
        
        tasks = [enrich_product(prod) for prod in data]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for product_ean, res in results:
            if isinstance(res, Exception) or res is None:
                not_added_eans.append(product_ean)
                logger.error(f"Ошибка в ean: {product_ean}")
            elif res:
                full_data.append(res)
                
        logger.info(
            f"Успешно получено {len(full_data)} продуктов, произошла ошибка для {len(not_added_eans)} продуктов с fabric_id {fabric_id}"
        )
                
    else:
        raise Exception(
            f"Не удалось получить данные для продукта с тканью {fabric_id}",
        )   
    
    return {
        "products": full_data,
        "not_added_eans": not_added_eans,
        "fabric_name": fabric_name
    }


async def _get_product_html_desc(product_id: int, httpx_client: httpx.AsyncClient):
    """
    Получает HTML-описание для конкретного продукта из Afterbuy API.
    """
    logger.debug(f"get_product_html_desc с product_id: {product_id} был вызван")
    
    try:
        access_token = await get_access_token(httpx_client=httpx_client) 
    except Exception as e:
        raise e
    
    headers = {"access-token": access_token}
    
    logger.debug(f"Получен токен доступа, выполняется запрос для product_id {product_id}")
    
    for attempt in range(3):
        try:
            response = await httpx_client.get(
                f"{settings.afterbuy_url}/v1/products/{product_id}", headers=headers, timeout=40.0
            )
            if response.status_code == 200:
                break
        except Exception as e:
            if attempt == 2:  # Последняя попытка
                logger.error(f"Ошибка при запросе HTML-описания продукта: {e}")
                raise Exception(f"Ошибка при запросе HTML-описания продукта у Afterbuy: {e}")
            await asyncio.sleep(0.5 * (attempt + 1))  # Ждем перед повтором
            continue
        
        # Обработка статусов, отличных от 200
        if attempt == 2:  # Последняя попытка
            logger.error(f"Не удалось получить данные о продукте: {response.status_code} - {response.text}")
            raise Exception(f"Ошибка получения данных у Afterbuy: {response.status_code} - {response.text}")
        await asyncio.sleep(0.5 * (attempt + 1))  # Ждем перед повтором

    data = response.json()
    
    if not data:
        logger.error(f"Продукт с product_id {product_id} не найден в Afterbuy")
        raise Exception(f"Продукт с product_id {product_id} не найден в Afterbuy")
    
    only_html = None
    
    if isinstance(data, list):
        only_html = data[0]['html_description']
        logger.debug(f"Успешно получено html-описание для product_num: {data[0].get('product_num')} с EAN: {data[0].get('ean')}")
        
    elif isinstance(data, dict):
        only_html = data.get('html_description')
        logger.debug(f"Успешно получено html-описание для product_num: {data.get('product_num')} с EAN: {data.get('ean')}")
        
    else:
        logger.warning(f"Продукт с ean {data.get('ean')}, не удалось получить html-описание")
    
    if not only_html:
        raise Exception(f"Продукт с product_id {product_id} не имеет html-описания")
    
    return only_html


async def get_fabric_id_by_afterbuy_id(afterbuy_fabric_id: int, httpx_client: httpx.AsyncClient):
    """
    Получает внутренний идентификатор ткани для поиска продукта на основе идентификатора ткани Afterbuy.

    Функция запрашивает информацию о ткани у Afterbuy API, используя предоставленный
    идентификатор ткани Afterbuy. Применяется логика повторных попыток для надежности. Если возвращаются несколько или один объект ткани,
    извлекается соответствующий внутренний идентификатор ткани.

    Аргументы:
        afterbuy_fabric_id (int): Идентификатор ткани в системе Afterbuy.
        httpx_client (httpx.AsyncClient): Асинхронный HTTP-клиент для выполнения запросов к API.

    Возвращает:
        int: Внутренний идентификатор ткани, используемый в парсере.

    Исключения:
        Exception: Если токен доступа не может быть получен,
            если запрос к API многократно не удается,
            если данные о ткани отсутствуют,
            или если идентификатор ткани не может быть извлечен из ответа.
    """
    
    try:
        access_token = await get_access_token(httpx_client=httpx_client) 
    except Exception as e:
        raise e
    
    headers = {"access-token": access_token}
    
    logger.debug(f"Получен токен доступа, выполняется запрос для afterbuy_fabric_id {afterbuy_fabric_id}")
    
    data = {
        "afterbuy_id": str(afterbuy_fabric_id)
    }
    
    for attempt in range(3):
        try:
            response = await httpx_client.post(
                f"{settings.afterbuy_url}/v1/fabrics/find", headers=headers, json=data, timeout=40.0
            )
            if response.status_code == 200:
                break
        except Exception as e:
            if attempt == 2:
                logger.error(f"Ошибка при запросе ткани у Afterbuy: {e}")
                raise Exception(
                    f"Ошибка при запросе ткани у Afterbuy: {e}",
                )
            await asyncio.sleep(0.5 * (attempt+1))
            continue
        
        # Обработка статусов, отличных от 200
        if attempt == 2:  # Последняя попытка
            logger.error(f"Не удалось получить айди по afterbuy_fabric_id: {response.status_code} - {response.text}")
            raise Exception(f"Ошибка получения ткани у Afterbuy по afterbuy_fabric_id: {response.status_code} - {response.text}")
        await asyncio.sleep(0.5 * (attempt + 1)) 
        
    data = response.json()
    
    if not data:
        logger.error(f"Айди не найдена для afterbuy_fabric_id {afterbuy_fabric_id} в Afterbuy")
        raise Exception(
            f"Айди не найдена для afterbuy_fabric_id {afterbuy_fabric_id} в Afterbuy",
        )
    
    logger.debug(f"Данные ответа содержат {len(data)} продукты для afterbuy_fabric_id {afterbuy_fabric_id}")
    
    only_id = None
    
    if isinstance(data, list):
        only_id = data[0]['id']
        name = data[0]['name']
        logger.debug(f"Успешно получен идентификатор ткани для afterbuy_fabric_id: {afterbuy_fabric_id}")
        
    elif isinstance(data, dict):
        only_id = data.get('id')
        name = data.get('name')
        logger.debug(f"Успешно получен идентификатор ткани для afterbuy_fabric_id: {afterbuy_fabric_id}")
        
    else:
        logger.warning(f"Айди с afterbuy_fabric_id: {afterbuy_fabric_id}, не удалось получить идентификатор ткани")
    
    if not only_id:
        raise Exception(
            f"Айди с afterbuy_fabric_id {afterbuy_fabric_id} не имеет идентификатора ткани",
        )
    
    for ban_word in ban_keywords_for_fabrics:
        if ban_word in name.casefold().strip():
            raise HTTPException(
                status_code=403,
                detail=f"Это запрещенная Айди, вы не можете загрузить ее в Mirakl! Название ткани: {name}"
            )
    
    return {
        "id": only_id,
        "name": name
    }
    
    
    
    
# ИЗ ФАЙЛА !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


async def get_products_by_fabric_from_file(afterbuy_fabric_id: int, market: str):
    
    with open("src/const/import_data/fabric_id.json", "r", encoding="utf-8") as f:
        fabric_data = json.load(f)

    afterbuy_fabric_name = fabric_data.get(afterbuy_fabric_id)
    
    if afterbuy_fabric_name is None:
        afterbuy_fabric_name = fabric_data.get(str(afterbuy_fabric_id))
        if afterbuy_fabric_name is None:
            raise Exception(f"Айди с afterbuy_fabric_id {afterbuy_fabric_id} не найдена в fabric_id.json")

    with open(f"src/const/import_data/fabrics_{market}/{afterbuy_fabric_name}.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if not data:
        logger.error(f"Продукты не найдены для fabric_name {afterbuy_fabric_name} в mock")
        raise Exception(f"Продукты не найдены для fabric_name {afterbuy_fabric_name} в mock")

    fabric_products_with_html = []
    not_added_eans = []

    # добавляем html
    for prod in data:
        fname = Path(f"src/const/import_data/HTML_{market}/{prod['EAN']}.html")
        prod['html_description'] = fname.read_text(encoding="utf-8")
        fabric_products_with_html.append(prod)
    
    logger.info(f"Получено {len(fabric_products_with_html)} продуктов для ткани {afterbuy_fabric_name}")
    
    return {
        "products": fabric_products_with_html,
        "not_added_eans": not_added_eans,
        "fabric_name": afterbuy_fabric_name
    }