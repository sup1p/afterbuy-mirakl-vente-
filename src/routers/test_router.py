"""
Test router module.
Provides testing endpoints for development and debugging purposes.
"""

from fastapi import APIRouter, HTTPException, Depends

from src.core.dependencies import get_httpx_client, get_ftp_client
from src.services.afterbuy_api_calls import get_product_data, get_products_by_fabric
from src.services.mapping import map_attributes
from src.utils.image_worker import resize_image_and_upload
from src.schemas import TestImageResize

from logs.config_logs import setup_logging

import logging
import asyncio
import httpx
import aioftp

setup_logging()
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/test-import-product/{ean}", tags=["test"])
async def test_import_product(ean: int, httpx_client: httpx.AsyncClient = Depends(get_httpx_client), ftp_client: aioftp.Client = Depends(get_ftp_client)):
    """
    Test endpoint for importing a single product by EAN (returns mapped data without importing to Mirakl).
    """
    try:
        data = await get_product_data(ean=ean, client=httpx_client)
    except Exception as e:
        logger.error(f"Error fetching data for ean {ean}: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )
        
    try:
        mapped_data_result = await map_attributes(data=data, httpx_client=httpx_client, ftp_client=ftp_client)
        mapped_data = mapped_data_result.get('data_for_mirakl')
    except Exception as e:
        logger.error(f"Error mapping attributes for ean {ean}: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

    return mapped_data

@router.post("/test-import-products-by-fabric/{afterbuy_fabric_id}", tags=["test"])
async def test_import_products_by_fabric(afterbuy_fabric_id: int, get_httpx_client: httpx.AsyncClient = Depends(get_httpx_client)):
    """
    Test endpoint for importing products by fabric ID (returns mapped data without importing to Mirakl).
    """
    try:
        data = await get_products_by_fabric(afterbuy_fabric_id=afterbuy_fabric_id, client=get_httpx_client)        
    except Exception as e:
        logger.error(f"Error fetching data for fabric {afterbuy_fabric_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )
    
    if not data:
        logger.error(f"No products found for fabric {afterbuy_fabric_id}")
        raise HTTPException(
            status_code=404,
            detail=f"No products found for fabric {afterbuy_fabric_id}",
        )
        

    products = data.get("products", [])
    not_added_eans = data.get("not_added_eans", [])
    
    logger.info(f"Fetched {len(products)} products for fabric {afterbuy_fabric_id}")
    
    tasks = [map_attributes(prod, get_httpx_client) for prod in products]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    data_for_csv = []
    
    for res in results:
        ean = res.get("ean")
        data_for_mirakl = res.get("data_for_mirakl")
        
        if isinstance(res, Exception):
            not_added_eans.append(ean)
            logger.error(f"Error fetching data for ean (not adding it to csv){ean}: {res}")
            continue
                
        if data_for_mirakl.get("category") == "No mapping":
            logger.error(f"No mapping found for category {data_for_mirakl.get('category')} of ean {ean}") # TODO: Change to real category from main products 
            not_added_eans.append(ean)
            continue
        
        data_for_csv.append(data_for_mirakl)
    
    return {
        "not_added_eans": not_added_eans,
        "total_not_added": len(not_added_eans),
        "data_for_csv_by_fabric": data_for_csv
    }
    

@router.post("/test-resize-image", tags=["test"])
async def test_resize_image(data: TestImageResize, httpx_client: httpx.AsyncClient = Depends(get_httpx_client), ftp_client: aioftp.Client = Depends(get_ftp_client)):
    """
    Test endpoint for image resizing and FTP upload functionality.
    """
    try:
        result = await resize_image_and_upload(url=data.url, ean=data.ean, httpx_client=httpx_client, ftp_client=ftp_client)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=str(e)
        )
    return result