"""
Mirakl API integration module.
Handles product imports, error checking, and platform configuration with Mirakl API.
"""

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



async def check_offer_import_error(import_parameter: str, client: httpx.AsyncClient):
    """
    Checks for offer import errors in Mirakl system.
    Returns EANs and error messages from the error report.
    """
    logger.info(f"Checking offer import error for parameter: {import_parameter}")
    headers = {
        "Authorization": settings.mirakl_api_key,
    }
    url = f"{settings.mirakl_url}/api/offers/imports/{import_parameter}/error_report"

    try:
        response = await client.get(url, headers=headers)
    except Exception as e:
        logger.error(f"Error while requesting offer import error report: {e}")
        raise Exception("Error while requesting offer import error report from Mirakl") from e

    if response.status_code == 200:
        df = pd.read_csv(BytesIO(response.content), sep=";")
        logger.info(f"Offer error report fetched successfully: {import_parameter}")

        # Extract EANs (from product-id, if product-id-type == 'EAN')
        eans = None
        if "product-id" in df.columns and "product-id-type" in df.columns:
            eans_list = (
                df.loc[df["product-id-type"].str.upper() == "EAN", "product-id"]
                .dropna()
                .astype(str)
                .tolist()
            )
            eans = eans_list if eans_list else None
            logger.debug(f"EANs for {import_parameter}: {eans}")

        # Extract errors
        errors = None
        if "error-message" in df.columns:
            errors_list = df["error-message"].dropna().astype(str).tolist()
            errors = errors_list if errors_list else None
            logger.info(f"Errors for {import_parameter}: {errors}")

        return {"status": 200, "ean": eans, "errors": errors}

    elif response.status_code == 404:
        logger.debug(f"Response: {response.status_code} - {response.text}")
        return {"status": 200, "message": "Not found, probably no errors"}

    else:
        logger.error(f"Error: {response.status_code} - {response.text}")
        try:
            error_json = response.json()
        except Exception:
            error_json = {"message": response.text}
        return {"status": response.status_code, "message": error_json.get("message", "Unknown error")}


async def check_import_error(import_parameter: str, client: httpx.AsyncClient):
    """
    Checks for product import errors in Mirakl system.
    Returns EANs, errors, and warnings from the transformation error report.
    """
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
    except Exception as e:
        logger.error(f"Error while requesting import error report: {e}")
        raise e("Error while requesting import error report from Mirakl")

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
            logger.info(f"Warnings for {import_parameter}: \n{warnings}")

        if "ean" in df.columns:
            eans_list = df["ean"].dropna().tolist()
            eans = eans_list if eans_list else None
            logger.debug(f"EANs for {import_parameter}: \n{eans}")
            
        return {"status": 200, "ean": eans, "errors": errors, "warnings": warnings}
    
    elif response.status_code == 404:
        logger.debug(f"Response: {response.status_code} - {response.text}")
            
        return {"status": 200, "message": "Not found, probably no errors/warnings"}
    
    else:
        logger.error(f"Error: {response.status_code} - {response.text}")
        try:
            error_json = response.json()
        except Exception:
            error_json = {"message": response.text}
            
        return {"status": response.status_code, "message": error_json.get("message", "Unknown error")}


async def check_non_integrated_products(import_parameter: str, client: httpx.AsyncClient):
    """
    Checks for non-integrated products in Mirakl system.
    Returns EANs, errors, and warnings from the error report.
    """
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
    except Exception as e:
        logger.error(f"Error while requesting non-integrated products: {e}")
        raise e("Error while requesting non-integrated products from Mirakl")
        

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
        logger.debug(f"Response: {response.status_code} - {response.text}")
            
        return {"status": 200, "message": "Not found, probably no errors/warnings"}
    
    else:
        logger.error(f"Error: {response.status_code} - {response.text}")
        try:
            error_json = response.json()
        except Exception:
            error_json = {"message": response.text}
        return {"status": response.status_code, "message": error_json.get("message", "Unknown error")}


async def check_platform_settings(client: httpx.AsyncClient):
    """
    Retrieves Mirakl platform configuration settings.
    """
    logger.info("Checking Mirakl platform settings")
    url = f"{settings.mirakl_url}/api/platform/configuration"

    headers = {
        "Authorization": settings.mirakl_api_key,
        "Accept": "application/json",
    }
    
    try:
        response = await client.get(url, headers=headers)
    except Exception as e:
        logger.error(f"Error while requesting Mirakl platform settings: {e}")
        raise e("Error while requesting platform settings from Mirakl")
    
    if response.status_code != 200:
        logger.error(f"Failed to get platform settings: {response.status_code} - {response.text}")
        raise Exception("Failed to obtain platform settings from Mirakl")
    
    data = response.json()
    
    if not data:
        logger.error("No data received when obtaining platform settings")
        raise Exception("No data received when obtaining platform settings from Mirakl")
    
    logger.info("Platform settings fetched successfully")

    return data


async def import_product(csv_content, client: httpx.AsyncClient):
    """
    Imports product data to Mirakl system via CSV upload.
    """
    reader = csv.DictReader(io.StringIO(csv_content))
    first_row = next(reader)   # Get first row

    category = first_row.get("category")
    product_num = first_row.get("product-id")
    ean = first_row.get("ean")
    
    logger.info(f"Importing product with category: {category}, product_num: {product_num}, ean: {ean}")
    
    
    results = []
    files = {"file": ("products.csv", csv_content, "text/csv")}
    payload = {
        "conversion_options[ai_enrichment][status]": "ENABLED",
        "conversion_options[ai_rewrite][status]": "ENABLED",
        "operator_format": "true",
        "shop": settings.mirakl_shop_id,
        
        "import_mode": "NORMAL",
        "with_products": "true",
    }

    headers = {
        "Authorization": settings.mirakl_api_key,
        "Accept": "application/json",
    }
    
    url = f"{settings.mirakl_url}/api/offers/imports"
    
    try:
        response = await client.post(url=url, data=payload, files=files, headers=headers)
    except Exception as exc:
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