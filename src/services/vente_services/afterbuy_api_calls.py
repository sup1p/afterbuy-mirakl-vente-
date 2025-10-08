"""
Afterbuy API integration module.
Handles authentication, product data retrieval, and brand information from Afterbuy API.
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

# Global token management variables
_access_token = None
_access_token_expiry = 0  # Unix timestamp
_access_token_lock = asyncio.Lock()


async def get_access_token(httpx_client: httpx.AsyncClient):
    """
    Retrieves and caches the Afterbuy API access token.

    The function uses global variables to store the token and its expiration time.
    If a valid token already exists, the cached value is returned.
    Otherwise, a new authentication request to the Afterbuy API is performed.

    Args:
        httpx_client (httpx.AsyncClient): Asynchronous HTTP client used for making requests.

    Returns:
        str: A valid access token.

    Raises:
        Exception: If the token cannot be retrieved due to a network error,
            invalid response status, or empty response data.
    """
    
    global _access_token, _access_token_expiry
    
    async with _access_token_lock:
        # If token exists and hasn't expired, return it
        if _access_token and time.time() < _access_token_expiry:
            logger.debug(f"Using cached access token, that will expire in {_access_token_expiry - time.time():.0f} seconds")
            return _access_token

        credentials = {
            "login": settings.afterbuy_login,
            "password": settings.afterbuy_password,
        }

        logger.info("Requesting access token from Afterbuy")
        
        try:
            response = await httpx_client.post(f"{settings.afterbuy_url}/v1/auth/login", json=credentials, timeout=40.0)
                
        except Exception as e:
            logger.error(f"Error while requesting access token: {e}")
            raise Exception(f"Error while requesting access token from Afterbuy: {e}")
            
        if response.status_code != 200:
            logger.error(f"Failed to get access token: {response.status_code} - {response.text}")
            raise Exception(
                f"Failed to obtain access token from Afterbuy: {response.status_code} - {response.text}"
            )
        data = response.json()
        
        if not data:
            logger.error("No data received when obtaining access token")
            raise Exception("No data received when obtaining access token from Afterbuy")
        
        _access_token = data["access_token"]
        expires_in = 1000
        _access_token_expiry = time.time() + expires_in - 10  # -10 seconds buffer for safety

        return _access_token


async def get_product_data(ean: int, httpx_client: httpx.AsyncClient, afterbuy_fabric_id: Optional[int] = None):
    """
    Retrieves product data from the Afterbuy API by EAN.

    The function requests product information from Afterbuy, using a valid access token.
    If enabled in settings, it also fetches the real HTML description for the product.
    Otherwise, a sample HTML description is added.
    If afterbuy_fabric_id is given is also fetches product filtering by EAN and FABRIC_ID

    Args:
        ean (int): Product EAN (European Article Number).
        httpx_client (httpx.AsyncClient): Asynchronous HTTP client used for API requests.

    Returns:
        dict: Product data including metadata and optionally an HTML description.

    Raises:
        Exception: If the access token cannot be retrieved,
            if the request to Afterbuy fails,
            if the response status is not 200,
            if no product data is returned,
            or if fetching the HTML description fails.
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
    
    logger.debug(f"Got access token, making request for ean {ean}")
    
    try:
        response = await httpx_client.post(
            f"{settings.afterbuy_url}/v1/products/filter?limit={limit}", headers=headers, json=data, timeout=40.0
        )
        logger.debug(f"{settings.afterbuy_url}/v1/products/filter?limit={limit} _-------------- {data}")
    except Exception as e:
        logger.error(f"Error while requesting product data: {e}")
        raise Exception(
            f"Error while requesting product data from Afterbuy: {e}",
        )

    if response.status_code != 200:
        logger.error(f"Failed to get product data: {response.status_code} - {response.text}")
        raise Exception(
            f"Error retrieving data from Afterbuy: {response.status_code} - {response.text}",
        )

    data = response.json()
    
    if not data:
        logger.error(f"Product with ean {ean} not found in Afterbuy")
        raise Exception(
            f"Product with ean {ean} not found in Afterbuy",
        )
    
    logger.debug(f"Response data contains for ean {ean}: {data}")   
    
    if isinstance(data, list) and data[0].get('id'):
        try:
            data[0]['html_description'] = await _get_product_html_desc(data[0].get('id'), httpx_client)
        except Exception as e:
            raise e
        
        logger.debug(f"Successfully fetched product data for product_num: {data[0].get('product_num')} with EAN: {data[0].get('ean')}")
        
    elif isinstance(data, dict) and data.get('id'):
        try:
            data['html_description'] = await _get_product_html_desc(data.get('id'), httpx_client)
        except Exception as e:
            raise e
        
        logger.debug(f"Successfully fetched product data for product_num: {data.get('product_num')} with EAN: {data.get('ean')}")
        
    else:
        raise Exception(
            f"Could not fetch html description for product with ean {ean}",
        )
    
    return data[0] if isinstance(data, list) else data


async def get_products_by_fabric(afterbuy_fabric_id: int, httpx_client: httpx.AsyncClient):
    """
    Retrieves all products associated with a specific fabric ID from the Afterbuy API.

    The function first resolves the internal fabric ID from the provided Afterbuy fabric ID.
    It then requests all related products from Afterbuy, applying retry logic for reliability.
    For each product, it optionally enriches the data with an HTML description, fetched
    in parallel with a semaphore to limit concurrency.

    Args:
        afterbuy_fabric_id (int): The fabric identifier used in Afterbuy.
        httpx_client (httpx.AsyncClient): Asynchronous HTTP client for making API requests.

    Returns:
        dict: A dictionary containing:
            - "products" (list[dict]): Successfully retrieved and enriched product data.
            - "not_added_eans" (list[str]): List of EANs for products that failed to process.

    Raises:
        Exception: If access token retrieval fails,
            if the request to Afterbuy repeatedly fails,
            if no products are returned,
            or if product enrichment encounters unrecoverable errors.
    """
    logger.info(f"get_products_and_data_by_fabric with afterbuy_fabric_id: {afterbuy_fabric_id} was accessed")
    
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
    
    logger.debug(f"Got access token, making request for fabric_id {fabric_id}")
    
    # Retry logic for main request
    for attempt in range(3):
        try:
            response = await httpx_client.post(
                f"{settings.afterbuy_url}/v1/products/filter?limit={limit}", headers=headers, json=data, timeout=40.0
            )
            if response.status_code == 200:
                break
        except Exception as e:
            if attempt == 2:  # Last attempt
                logger.error(f"Error while requesting products by fabric_id: {e}")
                raise Exception(f"Error while requesting products by fabric_id from Afterbuy: {e}")
            await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
    else:
        logger.error(f"Failed to get products by fabric_id: {response.status_code} - {response.text}")
        raise Exception(f"Error retrieving data from Afterbuy by fabric_id: {response.status_code} - {response.text}")

    data = response.json()
    
    if not data:
        logger.error(f"No products found for fabric_id {fabric_id} in Afterbuy")
        raise Exception(f"No products found for fabric_id {fabric_id} in Afterbuy")
    
    logger.debug(f"Response data contains {len(data)} products for fabric_id {fabric_id}")
    
    full_data = []
    not_added_eans = []
    
    if isinstance(data, list):
        
        semaphore = asyncio.Semaphore(10)  # Limit to 10 concurrent requests
        
        async def enrich_product(product):
            product_ean = product.get("ean", "No EAN")
            if not product.get("id"):
                return (product_ean, None)
            try:
                async with semaphore:
                    # Retry logic for product description
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
                logger.error(f"Error fetching html desc for product {product.get('id')}: {e}")
                return (product_ean, e)
                
        
        tasks = [enrich_product(prod) for prod in data]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for product_ean, res in results:
            if isinstance(res, Exception) or res is None:
                not_added_eans.append(product_ean)
                logger.error(f"Error in ean: {product_ean}")
            elif res:
                full_data.append(res)
                
        logger.info(
            f"Fetched {len(full_data)} products successfully, {len(not_added_eans)} errors occurred for fabric_id {fabric_id}"
        )
                
    else:
        raise Exception(
            f"Could not fetch data for product with fabric {fabric_id}",
        )   
    
    return {
        "products": full_data,
        "not_added_eans": not_added_eans,
        "fabric_name": fabric_name
    }


async def _get_product_html_desc(product_id: int, httpx_client: httpx.AsyncClient):
    """
    Retrieves HTML description for a specific product from Afterbuy API.
    """
    logger.debug(f"get_product_html_desc with product_id: {product_id} was accessed")
    
    try:
        access_token = await get_access_token(httpx_client=httpx_client) 
    except Exception as e:
        raise e
    
    headers = {"access-token": access_token}
    
    logger.debug(f"Got access token, making request for product_id {product_id}")
    
    for attempt in range(3):
        try:
            response = await httpx_client.get(
                f"{settings.afterbuy_url}/v1/products/{product_id}", headers=headers, timeout=40.0
            )
            if response.status_code == 200:
                break
        except Exception as e:
            if attempt == 2:  # Last attempt
                logger.error(f"Error while requesting product html description: {e}")
                raise Exception(f"Error while requesting product html description from Afterbuy: {e}")
            await asyncio.sleep(0.5 * (attempt + 1))  # Wait before retry
            continue
        
        # Handle non-200 status codes
        if attempt == 2:  # Last attempt
            logger.error(f"Failed to get product data: {response.status_code} - {response.text}")
            raise Exception(f"Error retrieving data from Afterbuy: {response.status_code} - {response.text}")
        await asyncio.sleep(0.5 * (attempt + 1))  # Wait before retry

    data = response.json()
    
    if not data:
        logger.error(f"Product with product_id {product_id} not found in Afterbuy")
        raise Exception(f"Product with product_id {product_id} not found in Afterbuy")
    
    only_html = None
    
    if isinstance(data, list):
        only_html = data[0]['html_description']
        logger.debug(f"Successfully fetched html description for product_num: {data[0].get('product_num')} with EAN: {data[0].get('ean')}")
        
    elif isinstance(data, dict):
        only_html = data.get('html_description')
        logger.debug(f"Successfully fetched html description for product_num: {data.get('product_num')} with EAN: {data.get('ean')}")
        
    else:
        logger.warning(f"Product with ean {data.get('ean')}, cannot fetch html description")
    
    if not only_html:
        raise Exception(f"Product with product_id {product_id} has no html description")
    
    return only_html


async def get_fabric_id_by_afterbuy_id(afterbuy_fabric_id: int, httpx_client: httpx.AsyncClient):
    """
    Retrieves the internal fabric ID for product search based on the Afterbuy fabric ID.

    The function requests the fabric information from the Afterbuy API using the provided
    Afterbuy fabric ID. Retry logic is applied for reliability. If multiple or single fabric
    objects are returned, the corresponding internal fabric ID is extracted.

    Args:
        afterbuy_fabric_id (int): Fabric identifier in the Afterbuy system.
        httpx_client (httpx.AsyncClient): Asynchronous HTTP client for API requests.

    Returns:
        int: The internal fabric ID used in the parser.

    Raises:
        Exception: If the access token cannot be retrieved,
            if the API request repeatedly fails,
            if no fabric data is returned,
            or if the fabric ID cannot be extracted from the response.
    """
    
    try:
        access_token = await get_access_token(httpx_client=httpx_client) 
    except Exception as e:
        raise e
    
    headers = {"access-token": access_token}
    
    logger.debug(f"Got access token, making request for afterbuy_fabric_id {afterbuy_fabric_id}")
    
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
                logger.error(f"Error while requesting fabric from Afterbuy: {e}")
                raise Exception(
                    f"Error while requesting product fabric from Afterbuy: {e}",
                )
            await asyncio.sleep(0.5 * (attempt+1))
            continue
        
        # Handle non-200 status codes
        if attempt == 2:  # Last attempt
            logger.error(f"Failed to get fabric by afterbuy_fabric_id: {response.status_code} - {response.text}")
            raise Exception(f"Error retrieving fabric from Afterbuy by afterbuy_fabric_id: {response.status_code} - {response.text}")
        await asyncio.sleep(0.5 * (attempt + 1)) 
        
    data = response.json()
    
    if not data:
        logger.error(f"No fabric found for afterbuy_fabric_id {afterbuy_fabric_id} in Afterbuy")
        raise Exception(
            f"No fabric found for afterbuy_fabric_id {afterbuy_fabric_id} in Afterbuy",
        )
    
    logger.debug(f"Response data contains {len(data)} products for afterbuy_fabric_id {afterbuy_fabric_id}")
    
    only_id = None
    
    if isinstance(data, list):
        only_id = data[0]['id']
        name = data[0]['name']
        logger.debug(f"Successfully fetched fabric id for afterbuy_fabric_id: {afterbuy_fabric_id}")
        
    elif isinstance(data, dict):
        only_id = data.get('id')
        name = data.get('name')
        logger.debug(f"Successfully fetched fabric id for afterbuy_fabric_id: {afterbuy_fabric_id}")
        
    else:
        logger.warning(f"Fabric with afterbuy_fabric_id: {afterbuy_fabric_id}, cannot fetch fabric id")
    
    if not only_id:
        raise Exception(
            f"Fabric with afterbuy_fabric_id {afterbuy_fabric_id} has no fabric id",
        )
    
    for ban_word in ban_keywords_for_fabrics:
        if ban_word in name.casefold().strip():
            raise HTTPException(
                status_code=403,
                detail=f"It is banned fabric, you cannot upload it to Mirakl! Fabric name: {name}"
            )
    
    return {
        "id": only_id,
        "name": name
    }
    
    
    
    
# FROM FILE !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


async def get_products_by_fabric_from_file(afterbuy_fabric_id: int, market: str):
    
    with open("src/const/import_data/fabric_id.json", "r", encoding="utf-8") as f:
        fabric_data = json.load(f)

    afterbuy_fabric_name = fabric_data.get(afterbuy_fabric_id)
    
    if afterbuy_fabric_name is None:
        afterbuy_fabric_name = fabric_data.get(str(afterbuy_fabric_id))
        if afterbuy_fabric_name is None:
            raise Exception(f"Fabric with afterbuy_fabric_id {afterbuy_fabric_id} not found in fabric_id.json")

    with open(f"src/const/import_data/fabrics_{market}/{afterbuy_fabric_name}.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if not data:
        logger.error(f"No products found for fabric_name {afterbuy_fabric_name} in mock")
        raise Exception(f"No products found for fabric_name {afterbuy_fabric_name} in mock")

    fabric_products_with_html = []
    not_added_eans = []

    # add html
    for prod in data:
        fname = Path(f"src/const/import_data/HTML_{market}/{prod['EAN']}.html")
        prod['html_description'] = fname.read_text(encoding="utf-8")
        fabric_products_with_html.append(prod)
    
    logger.info(f"Fetched {len(fabric_products_with_html)} products for fabric {afterbuy_fabric_name}")
    
    return {
        "products": fabric_products_with_html,
        "not_added_eans": not_added_eans,
        "fabric_name": afterbuy_fabric_name
    }   