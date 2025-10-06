"""
Product management router module.
Provides endpoints for importing products from Afterbuy to Mirakl system.
"""

from fastapi import APIRouter, HTTPException, Depends

from src.services.vente_services.afterbuy_api_calls import get_products_by_fabric_temporary
from src.services.vente_services.csv_converter import make_big_csv
from src.services.vente_services.mapping_from_file import map_attributes
from src.core.dependencies import get_httpx_client, get_current_user, get_session
from logs.config_logs import setup_logging

from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

import asyncio
import logging
import httpx

setup_logging()
logger = logging.getLogger(__name__)



router = APIRouter()

class FabricWithDeliveryRequestTEMP(BaseModel):
    afterbuy_fabric_name: str
    delivery_days: int


@router.post("/import-products-by-fabric-from-file/vente", tags=["product vente by fabric"])
async def import_products_by_fabric(input_body: FabricWithDeliveryRequestTEMP, httpx_client: httpx.AsyncClient = Depends(get_httpx_client), session: AsyncSession = Depends(get_session), current_user = Depends(get_current_user)):
    """
    Import products by Afterbuy fabric ID from Afterbuy to Mirakl.

    Args:
        afterbuy_fabric_id (int): Afterbuy fabric ID to import products from.
        httpx_client (httpx.AsyncClient): HTTP client dependency.

    Returns:
        dict: Mirakl API response, not added EANs, total not added, total EANs in fabric, and mapped data for CSV.

    Raises:
        HTTPException: 500 if data fetch or import to Mirakl fails.
        HTTPException: 404 if no products found or CSV creation fails.
    """
    
    afterbuy_fabric_name = input_body.afterbuy_fabric_name
    delivery_days = input_body.delivery_days
    
    try:
        data = await get_products_by_fabric_temporary(afterbuy_fabric_name=afterbuy_fabric_name)
    except Exception as e:
        logger.error(f"Error fetching data for fabric {afterbuy_fabric_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )
    
    if not data:
        logger.error(f"No products found for fabric {afterbuy_fabric_name}")
        raise HTTPException(
            status_code=404,
            detail=f"No products found for fabric {afterbuy_fabric_name}",
        )
        

    products = data.get("products", [])
    not_added_eans = data.get("not_added_eans", [])
    all_eans = {prod.get("CustomItemSpecifics", {}).get("EAN") for prod in products}

    logger.info(f"Fetched {len(products)} products for fabric {afterbuy_fabric_name}")
    
    tasks = []
    for idx, prod in enumerate(products, start=1):
        async def wrapper(p=prod, i=idx):
            try:
                p["delivery_days"] = delivery_days
                res = await map_attributes(p, httpx_client)
                logger.info(f"[{i}/{len(products)}] Processed product with EAN={p.get('CustomItemSpecifics').get('EAN')}")
                return res
            except Exception as e:
                logger.error(f"[{i}/{len(products)}] Error processing product EAN={p.get('CustomItemSpecifics').get('EAN')}: {e}")
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

        processed_eans.add(data_for_mirakl.get('ean'))
        data_for_csv.append(data_for_mirakl)

    not_added_eans.extend(list(all_eans - processed_eans))
    not_added_eans = list(set(not_added_eans))  # Убираем дубликаты

    logger.info(
        f"not_added_eans: {not_added_eans},\n total_not_added: {len(not_added_eans)}, \n total eans in fabric: {len(all_eans)}"
    )
    
    csv_content = make_big_csv(data_for_csv)
    
    if not csv_content:
        logger.error(f"Making csv failed or make_csv got no 'data' for fabric: {afterbuy_fabric_name}")
        raise HTTPException(
            status_code=404,
            detail=f"Creating big csv failed for fabric: {afterbuy_fabric_name}",
        )

    # try:
    #     mirakl_answer = await import_product_mirakl(csv_content, httpx_client=httpx_client)
    # except Exception as e:
    #     logger.error(f"Error importing products to Mirakl: {e}")
    #     raise HTTPException(
    #         status_code=500,
    #         detail=str(e),
    #     )

    return {
        # "mirakl_answer": mirakl_answer,
        "not_added_eans": not_added_eans,
        "total_not_added": len(not_added_eans),
        "delivery days": delivery_days,
        "total_eans_in_fabric": len(all_eans),
        "afterbuty_fabric_name": afterbuy_fabric_name,
        "data_for_csv_by_fabric": data_for_csv
    }