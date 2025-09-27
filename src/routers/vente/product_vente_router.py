"""
Product management router module.
Provides endpoints for importing products from Afterbuy to Mirakl system.
"""

from fastapi import APIRouter, HTTPException, Depends

from src.services.vente_services.afterbuy_api_calls import get_product_data, get_products_by_fabric
from src.services.vente_services.mirakl_api_calls import import_product as import_product_mirakl
from src.utils.vente_utils.format_little import is_valid_ean
from src.schemas.product_schemas import ProductEan, MiraklImportResponse, ImportManyEanResponse, ImportFabricProductsResponse
from src.services.vente_services.csv_converter import make_csv, make_big_csv
from src.services.vente_services.mapping import map_attributes
from src.core.dependencies import get_httpx_client, get_current_user
from logs.config_logs import setup_logging

import asyncio
import logging
import httpx

setup_logging()
logger = logging.getLogger(__name__)



router = APIRouter()


@router.post("/import-product/vente/{ean}", tags=["product vente"], response_model=MiraklImportResponse)
async def import_product(ean: str, afterbuy_fabric_id: int | None = None, httpx_client: httpx.AsyncClient = Depends(get_httpx_client), current_user = Depends(get_current_user)):
    """
    Import a single product by EAN from Afterbuy to Mirakl.Uses EAN and optional fabric id for getting product
    

    Args:
        ean (str): EAN code of the product to import.
        afterbuy_fabric_id (int): Optional parameter if user wants to get exact product
        httpx_client (httpx.AsyncClient): HTTP client dependency.

    Returns:
        dict: Mirakl API response for the imported product.

    Raises:
        HTTPException: 400 if EAN is invalid.
        HTTPException: 500 if data fetch or mapping fails.
        HTTPException: 404 if mapping or CSV creation fails.
    """
    if not is_valid_ean(ean):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid EAN {ean}"
        )
    
    try:
        data = await get_product_data(ean=ean, afterbuy_fabric_id=afterbuy_fabric_id, httpx_client=httpx_client)
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


@router.post("/import-products/vente", tags=["product vente"], response_model=ImportManyEanResponse)
async def import_products(eans: ProductEan, httpx_client: httpx.AsyncClient = Depends(get_httpx_client), current_user = Depends(get_current_user)):
    """
    Import multiple products by a list of EANs from Afterbuy to Mirakl.

    Args:
        eans (ProductEan): List of EAN codes to import.
        httpx_client (httpx.AsyncClient): HTTP client dependency.

    Returns:
        dict: Mirakl API response and list of EANs not imported.

    Raises:
        HTTPException: 400 if EAN list is empty.
        HTTPException: 404 if CSV creation fails.
        HTTPException: 500 if import to Mirakl fails.
    """
    ean_list = eans.ean_list
    if not ean_list:
        raise HTTPException(
            status_code=400,
            detail="EAN list is empty",
        )
        
    tasks = []
    for idx, ean in enumerate(ean_list, start=1):
        async def wrapper(e=ean, i=idx):
            try:
                res = await get_product_data(e, httpx_client)
                logger.info(f"[{i}/{len(ean_list)}] Got product with EAN={e}")
                return res
            except Exception as e:
                logger.error(f"[{i}/{len(ean_list)}] Error processing product EAN={e}: {e}")
                return e
        tasks.append(wrapper())
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
            detail="Creating big csv failed",
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


@router.post("/import-products-by-fabric/vente/{afterbuy_fabric_id}", tags=["product vente"], response_model=ImportFabricProductsResponse)
async def import_products_by_fabric(afterbuy_fabric_id: int, httpx_client: httpx.AsyncClient = Depends(get_httpx_client), current_user = Depends(get_current_user)):
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
            logger.error(f"No mapping found of ean {data_for_mirakl.get('ean')}") # TODO: Change to real category from main products 
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

    try:
        mirakl_answer = await import_product_mirakl(csv_content, httpx_client=httpx_client)
    except Exception as e:
        logger.error(f"Error importing products to Mirakl: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )
    
    return {
        "mirakl_answer": mirakl_answer,
        "not_added_eans": not_added_eans,
        "total_not_added": len(not_added_eans),
        "total_eans_in_fabric": len(all_eans),
    }