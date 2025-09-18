"""
Product management router module.
Provides endpoints for importing products from Afterbuy to Mirakl system.
"""

from fastapi import APIRouter, HTTPException, Depends

from src.services.afterbuy_api_calls import get_product_data, get_products_by_fabric
from src.services.mirakl_api_calls import import_product as import_product_mirakl
from src.schemas import ProductEan
from src.services.csv_converter import make_csv, make_big_csv
from src.services.mapping import map_attributes
from src.core.dependencies import get_httpx_client
from logs.config_logs import setup_logging

import asyncio
import logging
import httpx
import aioftp

setup_logging()
logger = logging.getLogger(__name__)



router = APIRouter()


@router.post("/import-product/{ean}", tags=["product"])
async def import_product(ean: int, httpx_client: httpx.AsyncClient = Depends(get_httpx_client)):
    """
    Imports a single product by EAN from Afterbuy to Mirakl system.
    """
    try:
        data = await get_product_data(ean=ean, httpx_client=httpx_client)
    except Exception as e:
        logger.error(f"Error fetching data for ean {ean}: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )
    
    logger.info(f"Fetched data for ean {ean}: {len(data)} items")
    try:
        mapped_data_result = await map_attributes(data=data, httpx_client=httpx_client)
        mapped_data = mapped_data_result.get('data_for_mirakl')
        logger.debug(f"MAPPED DATA IN THE MAP_ATTRIBUTES: {mapped_data}")
        
    except Exception as e:
        logger.error(f"Error mapping attributes for ean {ean}: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )
    
    if mapped_data is None or mapped_data in ["", {}, []]:
        logger.error(f"Mapping failed or returned empty for ean {ean}")
        raise HTTPException(
            status_code=404,
            detail=f"Product with ean {ean} not found or mapping failed",
        )
    
    logger.info(f"Mapped data for ean {ean}: {mapped_data}")

    if mapped_data.get("category") == "No mapping":
        logger.error(f"No mapping found for category {data.get('category')} of ean {ean}")
        raise HTTPException(
            status_code=404,
            detail=f"Category: {data.get('category')}, does not have mapping in the system",
        )

    csv_content = make_csv(mapped_data)
    
    if csv_content is None or csv_content in ["", {}, []]:
        logger.error(f"Making csv failed or make_csv got no 'data' for: {ean}")
        raise HTTPException(
            status_code=404,
            detail=f"Product with ean {ean} not found or make_csv failed",
        )

    return await import_product_mirakl(csv_content, httpx_client=httpx_client)


@router.post("/import-products", tags=["product"])
async def import_products(eans: ProductEan, httpx_client: httpx.AsyncClient = Depends(get_httpx_client)):
    """
    Imports multiple products by EAN list from Afterbuy to Mirakl system.
    """
    ean_list = eans.ean_list
    if not ean_list:
        raise HTTPException(
            status_code=400,
            detail="EAN list is empty",
        )
        
        
    tasks = [get_product_data(ean=ean, httpx_client=httpx_client) for ean in ean_list]
    results = await asyncio.gather(*tasks, return_exceptions=True)    
    
    data = []
    not_added_eans = []
    
    for ean,res in zip(ean_list, results):
        if isinstance(res, Exception):
            logger.error(f"Error fetching data for ean {ean}: {res}")
            not_added_eans.append(ean)
            continue
    
        single_product = res
        logger.info(f"Fetched data for ean {ean}")
        
        try:
            mapped_data_results = await map_attributes(data=single_product, httpx_client=httpx_client)
            mapped_data = mapped_data_results.get('data_for_mirakl')
        except Exception as e:
            logger.error(f"Error mapping attributes for ean {ean}: {e}")
            not_added_eans.append(ean)
            continue
        
        if not mapped_data:
            logger.error(f"Mapping failed or returned empty for ean {ean}")
            not_added_eans.append(ean)
            continue
        
        if mapped_data.get("category") == "No mapping":
            logger.error(f"No mapping found for category {single_product.get('category')} of ean {ean}")
            not_added_eans.append(ean)
            continue
        
        logger.info(f"Mapped data for ean {ean}: {mapped_data}")

        data.append(mapped_data)


    csv_content = make_big_csv(data)
    
    if not csv_content:
        logger.error(f"Making csv failed or make_csv got no 'data' for: {ean_list}")
        raise HTTPException(
            status_code=404,
            detail=f"Creating big csv failed",
        )
        
    try:
        mirakl_answer = await import_product_mirakl(csv_content, httpx_client=httpx_client)
    except Exception as e:
        logger.error(f"Error importing products to Mirakl: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

    return {
        "mirakl_response": mirakl_answer,
        "not_added_eans": not_added_eans,
        "total_not_added": len(not_added_eans)
    }


@router.post("/import-products-by-fabric/{fabric_id}", tags=["product"])
async def import_products_by_fabric(fabric_id: int, httpx_client: httpx.AsyncClient = Depends(get_httpx_client)):
    """
    Imports products by fabric ID from Afterbuy to Mirakl system.
    """
    try:
        data = await get_products_by_fabric(fabric_id=fabric_id, httpx_client=httpx_client)
    except Exception as e:
        logger.error(f"Error fetching data for fabric {fabric_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )
    
    if not data or not isinstance(data, list):
        logger.error(f"No products found for fabric {fabric_id}")
        raise HTTPException(
            status_code=404,
            detail=f"No products found for fabric {fabric_id}",
        )
        

    products = data.get("products", [])
    not_added_eans = data.get("not_added_eans", [])
    
    logger.info(f"Fetched {len(products)} products for fabric {fabric_id}")
    return