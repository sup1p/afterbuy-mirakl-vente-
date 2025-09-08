from fastapi import APIRouter, HTTPException, Depends

from src.services.afterbuy_api_calls import get_product_data, get_product_data_loaded
from src.services.mirakl_api_calls import import_product as import_product_mirakl
from src.schemas import ProductEan, ProductId
from src.services.csv_converter import make_csv, make_big_csv
from src.services.mapping import map_attributes
from src.core.dependencies import get_client
from logs.config_logs import setup_logging

import asyncio
import logging
import httpx

setup_logging()
logger = logging.getLogger(__name__)



router = APIRouter()


@router.post("/import-product/{ean}", tags=["product"])
async def import_product(ean: int, client: httpx.AsyncClient = Depends(get_client)):
    
    try:
        data = await get_product_data(ean=ean, client=client)
    except Exception as e:
        logger.error(f"Error fetching data for ean {ean}: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )
    
    logger.info(f"Fetched data for ean {ean}: {len(data)} items")
    try:
        mapped_data = await map_attributes(data)
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
    
    logger.info(f"Mapped data for product_num {ean}: {mapped_data}")

    if mapped_data.get("category") == "No mapping":
        print(data.get("category"))
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

    return await import_product_mirakl(csv_content, client=client)


@router.post("/import-products", tags=["product"])
async def import_products(eans: ProductEan, client: httpx.AsyncClient = Depends(get_client)):
    
    ean_list = eans.ean_list
    if not ean_list:
        raise HTTPException(
            status_code=400,
            detail="EAN list is empty",
        )
        
        
    tasks = [get_product_data(ean=ean, client=client) for ean in ean_list]
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
            mapped_data = await map_attributes(single_product)
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
        
        logger.info(f"Mapped data for product_num {ean}: {mapped_data}")

        data.append(mapped_data)


    csv_content = make_big_csv(data)
    
    if not csv_content:
        logger.error(f"Making csv failed or make_csv got no 'data' for: {ean_list}")
        raise HTTPException(
            status_code=404,
            detail=f"Creating big csv failed",
        )
        
    try:
        mirakl_answer = await import_product_mirakl(csv_content, client=client)
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


@router.post("/test-import-product/{ean}", tags=["product"])
async def test_import_product(ean: int, client: httpx.AsyncClient = Depends(get_client)):
    
    try:
        data = await get_product_data(ean=ean, client=client)
    except Exception as e:
        logger.error(f"Error fetching data for ean {ean}: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )
        
    try:
        mapped_data = await map_attributes(data)
    except Exception as e:
        logger.error(f"Error mapping attributes for ean {ean}: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

    return mapped_data