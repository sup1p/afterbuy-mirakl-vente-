from fastapi import HTTPException

from src.core.settings import settings
from logs.config_logs import setup_logging

import httpx
import logging
import time
import json

setup_logging()
logger = logging.getLogger(__name__)



_access_token = None
_access_token_expiry = 0  # Unix timestamp

async def get_access_token(client: httpx.AsyncClient):
    global _access_token, _access_token_expiry

    # Если токен есть и не истёк, возвращаем его
    if _access_token and time.time() < _access_token_expiry:
        logger.info(f"Using cached access token, that will expire in {_access_token_expiry - time.time():.0f} seconds")
        return _access_token

    credentials = {
        "login": settings.afterbuy_login,
        "password": settings.afterbuy_password,
    }

    logger.info("Requesting access token from Afterbuy")
    
    try:
        response = await client.post(f"{settings.afterbuy_url}/v1/auth/login", json=credentials)
            
    except httpx.RequestError as e:
        logger.error(f"Error while requesting access token: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error while requesting access token from Afterbuy",
        )
        
    if response.status_code != 200:
        logger.error(f"Failed to get access token: {response.status_code} - {response.text}")
        raise HTTPException(
            status_code=response.status_code,
            detail="Failed to obtain access token from Afterbuy",
        )

    data = response.json()
    
    if not data:
        logger.error("No data received when obtaining access token")
        raise HTTPException(
            status_code=404,
            detail="No data received when obtaining access token from Afterbuy",
        )
    
    _access_token = data["access_token"]
    expires_in = 1000
    _access_token_expiry = time.time() + expires_in - 10  # -10 сек на всякий случай

    return _access_token


async def get_brand_by_id(brand_id: int, client: httpx.AsyncClient):
    logger.info(f"get_brand_by_id with brand-id: {brand_id} was accessed")
    headers = {
        "access-token": await get_access_token(client=client),
        "Accept": "application/json",
    }
    
    try:
        response = await client.get(f"{settings.afterbuy_url}/v1/brands/{brand_id}", headers=headers)
    except httpx.RequestError as e:
        logger.error(f"Error while requesting brand by id: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error while requesting brand from Afterbuy",
        )

    if response.status_code != 200:
        logger.error(f"Failed to get brand by id: {response.status_code} - {response.text}")
        raise HTTPException(
            status_code=response.status_code,
            detail="Ошибка получения бренда из Afterbuy парсера",
        )

    data = response.json()
    
    if not data:
        logger.error(f"No data received when obtaining brand for brand_id {brand_id}")
        raise HTTPException(
            status_code=404,
            detail="No data received when obtaining brand from Afterbuy",
        )

    return data["name"]


async def get_product_data(ean: int, client: httpx.AsyncClient):
    
    logger.info(f"get_product_data with ean: {ean} was accessed")
    
    headers = {"access-token": await get_access_token(client=client)}
    
    data = {
        "ean": str(ean)
    }

    limit = 100
    
    logger.debug(f"Got access token, making request for ean {ean}")
    
    try:
        response = await client.post(
            f"{settings.afterbuy_url}/v1/products/filter?limit={limit}", headers=headers, json=data
        )
    except httpx.RequestError as e:
        logger.error(f"Error while requesting product data: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error while requesting product data from Afterbuy",
        )

    if response.status_code != 200:
        logger.error(f"Failed to get product data: {response.status_code} - {response.text}")
        raise HTTPException(
            status_code=response.status_code,
            detail="Ошибка получения данных из Afterbuy",
        )

    data = response.json()
    
    if not data:
        logger.error(f"Product with ean {ean} not found in Afterbuy")
        raise HTTPException(
            status_code=404,
            detail=f"Product with ean {ean} not found in Afterbuy",
        )
    
    logger.debug(f"Response data contains for ean {ean}: {data}")   
    
    if isinstance(data, list) and data[0].get('id'):
        data[0]['html_description'] = await get_product_html_desc(data[0].get('id'), client)
        logger.debug(f"Successfully fetched product data for product_num: {data[0].get('product_num')} with EAN: {data[0].get('ean')}")
        
    elif isinstance(data, dict) and data.get('id'):
        data['html_description'] = await get_product_html_desc(data.get('id'), client)
        logger.debug(f"Successfully fetched product data for product_num: {data.get('product_num')} with EAN: {data.get('ean')}")
        
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Could not fetch html description for product with ean {ean}",
        )
    
    return data[0] if isinstance(data, list) else data


async def get_product_html_desc(product_id: int, client: httpx.AsyncClient):
    
    logger.info(f"get_product_html_desc with product_id: {product_id} was accessed")
    
    headers = {"access-token": await get_access_token(client=client)}
    
    logger.debug(f"Got access token, making request for product_id {product_id}")
    
    try:
        response = await client.get(
            f"{settings.afterbuy_url}/v1/products/{product_id}", headers=headers
        )
    except httpx.RequestError as e:
        logger.error(f"Error while requesting product html description: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error while requesting product html description from Afterbuy",
        )

    if response.status_code != 200:
        logger.error(f"Failed to get product data: {response.status_code} - {response.text}")
        raise HTTPException(
            status_code=response.status_code,
            detail="Ошибка получения данных из Afterbuy",
        )

    data = response.json()
    
    if not data:
        logger.error(f"Product with product_id {product_id} not found in Afterbuy")
        raise HTTPException(
            status_code=404,
            detail=f"Product with product_id {product_id} not found in Afterbuy",
        )
    
    only_html = data.get("html_description")
    
    if isinstance(data, list):
        only_html = data[0]['html_description']
        logger.debug(f"Successfully fetched html description for product_num: {data[0].get('product_num')} with EAN: {data[0].get('ean')}")
        
    elif isinstance(data, dict):
        only_html = data.get('html_description')
        logger.debug(f"Successfully fetched html description for product_num: {data.get('product_num')} with EAN: {data.get('ean')}")
        
    else:
        logger.warning(f"Product with ean {data.get('ean')}, cannot fetch html description")
    
    if not only_html:
        raise HTTPException(
            status_code=404,
            detail=f"Product with product_id {product_id} has no html description",
        )
    
    return only_html

def get_product_data_loaded(product_num: int):
    
    logger.info(f"get_product_data_loaded with product_num: {product_num} was accessed")
    
    with open('product_samples.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    single_product = None
        
    for product in data:
        if int(product.get("id")) == int(product_num):
            single_product = product
            break
    if not single_product:
        logger.error(f"Product with product_num {product_num} not found in sample data")
        raise HTTPException(
            status_code=404,
            detail=f"Product with product_num {product_num} not found in sample data",
        )

    logger.info(f"Successfully fetched product data for product_id: {single_product.get('id')} with EAN: {single_product.get('ean')}")
    
    single_product["html_description"] = "<p>Sample description for testing purposes.</p> <p>Sample description for testing purposes.</p> <p>Sample description for testing purposes.</p> <p>Sample description for testing purposes.</p> <p>Sample description for testing purposes.</p>"

    return single_product