"""
Test router module.
Provides testing endpoints for development and debugging purposes.
"""

from fastapi import APIRouter, HTTPException, Depends

from src.core.dependencies import get_httpx_client, get_current_user
from src.core.settings import settings
from src.services.afterbuy_api_calls import get_product_data, get_products_by_fabric
from src.services.mapping import map_attributes
from src.utils.image_worker import resize_image_and_upload
from src.utils.format_little import is_valid_ean
from src.schemas.product_schemas import TestImageResize, MappedProduct, FabricMappedProducts
from src.services.csv_converter import make_big_csv

from logs.config_logs import setup_logging

import logging
import asyncio
import httpx
import aioftp

setup_logging()
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/test-import-product/{ean}/", tags=["test"], response_model=MappedProduct)
async def dev_import_product(ean: str, afterbuy_fabric_id: int | None = None,httpx_client: httpx.AsyncClient = Depends(get_httpx_client), current_user = Depends(get_current_user)):
    """
    Test endpoint for importing a single product by EAN (returns mapped data without importing to Mirakl).
    If afterbuy_fabric_id is given is also fetches product filtering by EAN and FABRIC_ID

    Args:
        ean (str): EAN code of the product.
        httpx_client (httpx.AsyncClient): HTTP client dependency.

    Returns:
        dict: Mapped product data for Mirakl.

    Raises:
        HTTPException: 400 if EAN is invalid, 500 if data fetch or mapping fails.
    """
    if not is_valid_ean(ean):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid EAN {ean}"
        )
        
    try:
        data = await get_product_data(ean=int(ean), afterbuy_fabric_id=afterbuy_fabric_id,httpx_client=httpx_client)
    except Exception as e:
        logger.error(f"Error fetching data for ean {ean}: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )
    try:
        mapped_data_result = await map_attributes(data=data, httpx_client=httpx_client)
        mapped_data = mapped_data_result.get('data_for_mirakl')
    except Exception as e:
        logger.error(f"Error mapping attributes for ean {ean}: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )
    return mapped_data

@router.post("/test-import-products-by-fabric/{afterbuy_fabric_id}", tags=["test"], response_model=FabricMappedProducts)
async def dev_import_products_by_fabric(afterbuy_fabric_id: int, httpx_client: httpx.AsyncClient = Depends(get_httpx_client), current_user = Depends(get_current_user)):
    """
    Test endpoint for importing products by Afterbuy fabric ID (returns mapped data for all products in the fabric, without importing to Mirakl).

    Args:
        afterbuy_fabric_id (int): Afterbuy fabric ID.
        httpx_client (httpx.AsyncClient): HTTP client dependency.

    Returns:
        dict: Contains not added EANs, total not added, total EANs in fabric, and mapped data for CSV.

    Raises:
        HTTPException: 500 if data fetch fails, 404 if no products found or CSV creation fails.
    """
    
    try:
        data = await get_products_by_fabric(afterbuy_fabric_id=afterbuy_fabric_id, httpx_client=httpx_client)        
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
    all_eans = {prod.get("ean") for prod in products}
    
    logger.info(f"Fetched {len(products)} products for fabric {afterbuy_fabric_id}")
    
    tasks = []
    for idx, prod in enumerate(products, start=1):
        async def wrapper(p=prod, i=idx):
            try:
                res = await map_attributes(p, httpx_client)
                logger.info(f"[{i}/{len(products)}] Processed product with EAN={p.get('ean')}")
                return res
            except Exception as e:
                logger.error(f"[{i}/{len(products)}] Error processing product EAN={p.get('ean')}: {e}")
                return e
        tasks.append(wrapper())

    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    data_for_csv = []
    processed_eans = set()
    
    for res in results:
        if isinstance(res, Exception):
            logger.error(f"Error fetching data (not adding it to csv): {res}")
            continue
        data_for_mirakl = res.get("data_for_mirakl")        
        if data_for_mirakl.get("category") == "No mapping":
            logger.error(f"No mapping found of ean {data_for_mirakl.get('ean')}")
            continue
        processed_eans.add(data_for_mirakl.get("ean"))
        data_for_csv.append(data_for_mirakl)
        
    not_added_eans = list(all_eans - processed_eans)
    logger.info(
        f"not_added_eans: {not_added_eans},\n total_not_added: {len(not_added_eans)}, \n total eans in fabric: {len(all_eans)}"
    )
    
    csv_content = make_big_csv(data_for_csv)
    
    if not csv_content:
        logger.error(f"Making csv failed or make_csv got no 'data' for fabric id: {afterbuy_fabric_id}")
        raise HTTPException(
            status_code=404,
            detail=f"Creating big csv failed for fabric: {afterbuy_fabric_id}",
        )
        
    with open("output.csv", "w", encoding="utf-8", newline="") as f:
        f.write(csv_content)
        
    return {
        "not_added_eans": not_added_eans,
        "total_not_added": len(not_added_eans),
        "total_eans_in_fabric": len(all_eans),
        "data_for_csv_by_fabric": data_for_csv
    }

@router.post("/test-resize-image", tags=["test"], response_model=str)
async def dev_resize_image(data: TestImageResize, httpx_client: httpx.AsyncClient = Depends(get_httpx_client), current_user = Depends(get_current_user)):
    """
    Test endpoint for image resizing and FTP upload functionality.

    Args:
        data (TestImageResize): Image resize request data (url, ean).
        httpx_client (httpx.AsyncClient): HTTP client dependency.

    Returns:
        dict: Result of image resize and upload operation.

    Raises:
        HTTPException: 422 if image processing or FTP upload fails.
    """
    try:
        async with aioftp.Client.context(host=settings.ftp_host,port=settings.ftp_port,user=settings.ftp_user,password=settings.ftp_password) as ftp_client:
            result = await resize_image_and_upload(url=data.url, ean=data.ean, httpx_client=httpx_client, ftp_client=ftp_client, test=True)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=str(e)
        )
    return result