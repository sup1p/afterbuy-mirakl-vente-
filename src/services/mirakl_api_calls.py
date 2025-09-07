from fastapi import HTTPException
from src.core.settings import settings
from logs.config_logs import setup_logging

from io import BytesIO
import io
import csv
import pandas as pd
import logging
import httpx


setup_logging()
logger = logging.getLogger(__name__)


async def check_import_error(import_parameter: str, client: httpx.AsyncClient):
    logger.info(f"Checking import error for parameter: {import_parameter}")
    headers = {
        "Authorization": settings.mirakl_api_key,
    }
    url = (
        f"{settings.mirakl_url}/api/products/imports/"
        + import_parameter
        + "/transformation_error_report"
    )

    try:
        response = await client.get(url, headers=headers)
    except httpx.RequestError as e:
        logger.error(f"Error while requesting import error report: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error while requesting import error report from Mirakl",
        )

    if response.status_code == 200:
        df = pd.read_csv(
            BytesIO(response.content), sep=";"
        )  
        
        logger.info(f"Error report fetched successfully: {import_parameter}")

        errors = None
        warnings = None
        if "errors" in df.columns:
            errors_list = df["errors"].dropna().tolist()
            errors = errors_list if errors_list else None
            logger.info(f"Errors for {import_parameter}: \n{errors}")
            
        if "warnings" in df.columns:
            warnings_list = df["warnings"].dropna().tolist()
            warnings = warnings_list if warnings_list else None
            logger.info(f"Warnings for {import_parameter}: \n{warnings}")\

        if "ean" in df.columns:
            eans_list = df["ean"].dropna().tolist()
            eans = eans_list if eans_list else None
            logger.debug(f"EANs for {import_parameter}: \n{eans}")
            
        return {"status": 200, "ean": eans, "errors": errors, "warnings": warnings}
    
    elif response.status_code == 404:
        logger.debug(f"Ответ: {response.status_code} - {response.text}")
            
        return {"status": 200, "message": "Not found, probably no errors/warnings"}
    
    else:
        logger.error(f"Ошибка: {response.status_code} - {response.text}")
        try:
            error_json = response.json()
        except Exception:
            error_json = {"message": response.text}
            
        return {"status": response.status_code, "message": error_json.get("message", "Unknown error")}


async def check_non_integrated_products(import_parameter: str, client: httpx.AsyncClient):
    logger.info(f"Checking non-integrated products for parameter: {import_parameter}")
    headers = {
        "Authorization": settings.mirakl_api_key,
    }
    url = (
        f"{settings.mirakl_url}/api/products/imports/"
        + import_parameter
        + "/error_report"
    )

    try:
        response = await client.get(url, headers=headers)
    except httpx.RequestError as e:
        logger.error(f"Error while requesting non-integrated products: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error while requesting non-integrated products from Mirakl",
        )
        

    if response.status_code == 200:
        df = pd.read_csv(
            BytesIO(response.content), sep=";"
        ) 
        
        logger.info(f"Non-integrated report fetched successfully: {import_parameter}")
        
        errors = None
        warnings = None
        if "errors" in df.columns:
            errors_list = df["errors"].dropna().tolist()
            errors = errors_list if errors_list else None
            logger.info(f"Errors for {import_parameter}: \n{errors}")
            
        if "warnings" in df.columns:
            warnings_list = df["warnings"].dropna().tolist()
            warnings = warnings_list if warnings_list else None
            logger.info(f"Warnings for {import_parameter}: \n{warnings}")
        
        if "ean" in df.columns:
            eans_list = df["ean"].dropna().tolist()
            eans = eans_list if eans_list else None
            logger.debug(f"EANs for {import_parameter}: \n{eans}")
            
        return {"status": 200, "ean": eans, "errors": errors, "warnings": warnings}
    
    elif response.status_code == 404:
        logger.debug(f"Ответ: {response.status_code} - {response.text}")
            
        return {"status": 200, "message": "Not found, probably no errors/warnings"}
    
    else:
        logger.error(f"Ошибка: {response.status_code} - {response.text}")
        try:
            error_json = response.json()
        except Exception:
            error_json = {"message": response.text}
        return {"status": response.status_code, "message": error_json.get("message", "Unknown error")}


async def check_platform_settings(client: httpx.AsyncClient):
    logger.info("Checking Mirakl platform settings")
    url = f"{settings.mirakl_url}/api/platform/configuration"

    headers = {
        "Authorization": settings.mirakl_api_key,
        "Accept": "application/json",
    }
    
    try:
        response = await client.get(url, headers=headers)
    except httpx.RequestError as e:
        logger.error(f"Error while requesting Mirakl platform settings: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error while requesting platform settings from Mirakl",
        )
    
    if response.status_code != 200:
        logger.error(f"Failed to get platform settings: {response.status_code} - {response.text}")
        raise Exception("Failed to obtain platform settings from Mirakl")
    
    data = response.json()
    
    if not data:
        logger.error("No data received when obtaining platform settings")
        raise HTTPException(
            status_code=404,
            detail="No data received when obtaining platform settings from Mirakl",
        )
    
    logger.info("Platform settings fetched successfully")

    return data


async def import_product(csv_content, client: httpx.AsyncClient):
    reader = csv.DictReader(io.StringIO(csv_content))
    first_row = next(reader)   # берём первую строку

    category = first_row.get("category")
    product_num = first_row.get("product-id")
    ean = first_row.get("ean")
    
    logger.info(f"Importing product with category: {category}, product_num: {product_num}, ean: {ean}")
    
    
    results = []
    files = {"file": ("products.csv", csv_content, "text/csv")}
    payload = {
        "conversion_options[ai_enrichment][status]": "ENABLED",
        "conversion_options[ai_rewrite][status]": "ENABLED",
        "operator_format": "false",
        "shop": settings.mirakl_shop_id,
    }

    headers = {
        "Authorization": settings.mirakl_api_key,
        "Accept": "application/json",
    }
    
    url = f"{settings.mirakl_url}/api/products/imports"
    
    try:
        response = await client.post(url=url, data=payload, files=files, headers=headers)
    except httpx.RequestError as exc:
        logger.error(f"Request error while importing product: {exc}")
        results.append({f"product {product_num} error": str(exc)})
        return {"status": "error", "results": results}

    if response.status_code != 201:
        logger.error(f"Failed to import product: {response.status_code} - {response.text}")
        results.append({"product {product_num} error": response.text})
    else:
        logger.info(f"Product import initiated successfully: {response.json()}")
        results.append({"product {product_num} result": response.json()})

    return {"status": "done", "results": results}


# async def delete_product(product_ids: list[int]):
#     logger.info(f"Deleting products with ids: {product_ids}")
#     url = settings.mirakl_connect
    
#     payload = {
#         "products": [{"id": pid} for pid in product_ids]
#     }

#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": "Bearer <YOUR_JWT_HERE>"
#     }
        
#     try:
#         async with httpx.AsyncClient(timeout=30.0) as client:
#             response = await client.delete(url, json=payload, headers=headers)
#     except httpx.RequestError as e: 
#         logger.error(f"Error while requesting product deletion: {e}")
#         raise HTTPException(
#             status_code=500,
#             detail="Error while requesting product deletion from Mirakl Connect",
#         )

#     data = response.json()
    
#     return data