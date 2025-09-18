"""
Afterbuy API integration module.
Handles authentication, product data retrieval, and brand information from Afterbuy API.
"""

from src.core.settings import settings
from logs.config_logs import setup_logging

import httpx
import logging
import time
import json
import asyncio

setup_logging()
logger = logging.getLogger(__name__)

# Global token management variables
_access_token = None
_access_token_expiry = 0  # Unix timestamp
_access_token_lock = asyncio.Lock()


async def get_access_token(httpx_client: httpx.AsyncClient):
    """
    Retrieves and manages Afterbuy API access token.
    Uses caching to avoid unnecessary authentication requests.
    """
    global _access_token, _access_token_expiry
    
    async with _access_token_lock:
        # If token exists and hasn't expired, return it
        if _access_token and time.time() < _access_token_expiry:
            logger.info(f"Using cached access token, that will expire in {_access_token_expiry - time.time():.0f} seconds")
            return _access_token

        credentials = {
            "login": settings.afterbuy_login,
            "password": settings.afterbuy_password,
        }

        logger.info("Requesting access token from Afterbuy")
        
        try:
            response = await httpx_client.post(f"{settings.afterbuy_url}/v1/auth/login", json=credentials)
                
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


async def get_brand_by_id(brand_id: int, httpx_client: httpx.AsyncClient):
    """
    Retrieves brand information by brand ID from Afterbuy API.
    """
    logger.info(f"get_brand_by_id with brand-id: {brand_id} was accessed")
    
    try:
        access_token = await get_access_token(httpx_client=httpx_client) 
    except Exception as e:
        raise e(str(e))
    
    headers = {
        "access-token": access_token,
        "Accept": "application/json",
    }
    
    try:
        response = await httpx_client.get(f"{settings.afterbuy_url}/v1/brands/{brand_id}", headers=headers)
    except Exception as e:
        logger.error(f"Error while requesting brand by id: {e}")
        raise Exception(
            f"Error while requesting brand from Afterbuy: {e}",
        )

    if response.status_code != 200:
        logger.error(f"Failed to get brand by id: {response.status_code} - {response.text}")
        raise Exception(
            f"Error retrieving brand from Afterbuy parser: {response.status_code} - {response.text}",
        )

    data = response.json()
    
    if not data:
        logger.error(f"No data received when obtaining brand for brand_id {brand_id}")
        raise Exception(
            f"No data received when obtaining brand from Afterbuy for brand_id {brand_id}",
        )

    return data["name"]


async def get_product_data(ean: int, httpx_client: httpx.AsyncClient):
    """
    Retrieves product data by EAN from Afterbuy API.
    Includes HTML description if enabled in settings.
    """
    logger.info(f"get_product_data with ean: {ean} was accessed")
    
    try:
        access_token = await get_access_token(httpx_client=httpx_client) 
    except Exception as e:
        raise e
    
    headers = {"access-token": access_token}
    
    data = {
        "ean": str(ean)
    }

    limit = 100
    
    logger.debug(f"Got access token, making request for ean {ean}")
    
    try:
        response = await httpx_client.post(
            f"{settings.afterbuy_url}/v1/products/filter?limit={limit}", headers=headers, json=data
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
            if settings.use_real_html_desc:
                data[0]['html_description'] = await get_product_html_desc(data[0].get('id'), httpx_client)
            else:
                logger.debug(f"Skipping fetching real html description for product with ean {ean} as per settings")
                data[0]['html_description'] = "<p>Sample description for testing purposes.</p> <p>Sample description for testing purposes.</p> <p>Sample description for testing purposes.</p> <p>Sample description for testing purposes.</p> <p>Sample description for testing purposes.</p>"
        except Exception as e:
            raise e
        
        logger.debug(f"Successfully fetched product data for product_num: {data[0].get('product_num')} with EAN: {data[0].get('ean')}")
        
    elif isinstance(data, dict) and data.get('id'):
        try:
            if settings.use_real_html_desc:
                data['html_description'] = await get_product_html_desc(data.get('id'), httpx_client)
            else:
                logger.debug(f"Skipping fetching real html description for product with ean {ean} as per settings")
                data['html_description'] = "<p>Sample description for testing purposes.</p> <p>Sample description for testing purposes.</p> <p>Sample description for testing purposes.</p> <p>Sample description for testing purposes.</p> <p>Sample description for testing purposes.</p>"
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
    Retrieves all products associated with a specific fabric ID from Afterbuy API.
    Processes products in parallel with semaphore for rate limiting.
    """
    logger.info(f"get_products_and_data_by_fabric with afterbuy_fabric_id: {afterbuy_fabric_id} was accessed")
    
    fabric_id = await get_fabric_id_by_afterbuy_id(afterbuy_fabric_id, httpx_client)
    
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
                f"{settings.afterbuy_url}/v1/products/filter?limit={limit}", headers=headers, json=data
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
                if settings.use_real_html_desc:
                    async with semaphore:
                        # Retry logic for product description
                        for attempt in range(3):
                            try:
                                product["html_description"] = await get_product_html_desc(product["id"], httpx_client)
                                break
                            except Exception as e:
                                if attempt == 2:
                                    raise e
                                await asyncio.sleep(0.5 * (attempt + 1))
                else:
                    logger.debug(
                        f"Skipping fetching real html description for product with ean {product.get('ean')} as per settings"
                    )
                    product["html_description"] = "<p>Sample description for testing purposes.</p>" * 5
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
    }


async def get_product_html_desc(product_id: int, httpx_client: httpx.AsyncClient):
    """
    Retrieves HTML description for a specific product from Afterbuy API.
    """
    logger.info(f"get_product_html_desc with product_id: {product_id} was accessed")
    
    try:
        access_token = await get_access_token(httpx_client=httpx_client) 
    except Exception as e:
        raise e
    
    headers = {"access-token": access_token}
    
    logger.debug(f"Got access token, making request for product_id {product_id}")
    
    for attempt in range(3):
        try:
            response = await httpx_client.get(
                f"{settings.afterbuy_url}/v1/products/{product_id}", headers=headers
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
    Returns fabric ID in parser based on afterbuy_fabric_id for product search.
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
                f"{settings.afterbuy_url}/v1/fabrics/find", headers=headers, json=data
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
        logger.debug(f"Successfully fetched fabric id for afterbuy_fabric_id: {afterbuy_fabric_id}")
        
    elif isinstance(data, dict):
        only_id = data.get('id')
        logger.debug(f"Successfully fetched fabric id for afterbuy_fabric_id: {afterbuy_fabric_id}")
        
    else:
        logger.warning(f"Fabric with afterbuy_fabric_id: {afterbuy_fabric_id}, cannot fetch fabric id")
    
    if not only_id:
        raise Exception(
            f"Fabric with afterbuy_fabric_id {afterbuy_fabric_id} has no fabric id",
        )
    
    return only_id