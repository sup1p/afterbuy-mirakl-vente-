"""
Mirakl API integration module.
Handles product imports, error checking, and platform configuration with Mirakl API.
"""

from src.core.settings import settings
from logs.config_logs import setup_logging

from io import BytesIO
import pandas as pd
import logging
import httpx


setup_logging()
logger = logging.getLogger(__name__)



async def check_offer_import_error(import_parameter: str, httpx_client: httpx.AsyncClient):
    """
    Retrieve and parse the Mirakl offer import error report.

    The function requests the error report for a specific offer import 
    and extracts EANs (if available) and related error messages.

    Args:
        import_parameter (str): Import identifier provided by Mirakl.
        httpx_client (httpx.AsyncClient): Asynchronous HTTP client instance.

    Returns:
        dict: Dictionary with the following keys:
            - status (int): HTTP-like status indicator.
            - ean (list[str] | None): List of EANs extracted from the report (if available).
            - errors (list[str] | None): List of error messages (if available).
            - message (str, optional): Returned if no errors are found or on failure.

    Raises:
        Exception: If the request to Mirakl fails.
    """
    logger.info(f"Checking offer import error for parameter: {import_parameter}")
    headers = {
        "Authorization": settings.mirakl_api_key,
    }
    url = f"{settings.mirakl_url}/api/offers/imports/{import_parameter}/error_report"

    try:
        response = await httpx_client.get(url, headers=headers, timeout=40.0)
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


async def check_import_error(import_parameter: str, httpx_client: httpx.AsyncClient):
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
        response = await httpx_client.get(url, headers=headers, timeout=40.0)
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


async def check_non_integrated_products(import_parameter: str, httpx_client: httpx.AsyncClient):
    """
    Retrieve and parse the Mirakl error report for non-integrated products.

    The function checks for products that were not successfully integrated 
    during the import process and extracts EANs, errors, and warnings.

    Args:
        import_parameter (str): Import identifier provided by Mirakl.
        httpx_client (httpx.AsyncClient): Asynchronous HTTP client instance.

    Returns:
        dict: Dictionary with the following keys:
            - status (int): HTTP-like status indicator.
            - ean (list[str] | None): List of EANs (if available).
            - errors (list[str] | None): List of error messages (if available).
            - warnings (list[str] | None): List of warnings (if available).
            - message (str, optional): Returned if no errors/warnings are found or on failure.

    Raises:
        Exception: If the request to Mirakl fails.
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
        response = await httpx_client.get(url, headers=headers, timeout=40.0)
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


async def check_platform_settings(httpx_client: httpx.AsyncClient):
    """
    Retrieve Mirakl platform configuration settings.

    The function requests platform-level configuration data, 
    such as enabled modules and system parameters.

    Args:
        httpx_client (httpx.AsyncClient): Asynchronous HTTP client instance.

    Returns:
        dict: JSON response containing platform configuration.

    Raises:
        Exception: If the request fails or Mirakl returns invalid/empty data.
    """
    
    logger.info("Checking Mirakl platform settings")
    url = f"{settings.mirakl_url}/api/platform/configuration"

    headers = {
        "Authorization": settings.mirakl_api_key,
        "Accept": "application/json",
    }
    
    try:
        response = await httpx_client.get(url, headers=headers, timeout=40.0)
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


async def import_product(csv_content, httpx_client: httpx.AsyncClient):
    """
    Import product data into Mirakl via CSV upload.

    The function sends a CSV file containing product data to the Mirakl API 
    and initiates the import process. Import settings include AI enrichment 
    and rewrite options, as well as operator format.

    Args:
        csv_content (bytes): CSV file content to be uploaded.
        httpx_client (httpx.AsyncClient): Asynchronous HTTP client instance.

    Returns:
        dict: Dictionary with the following keys:
            - status (str): "done" if request succeeded, "error" otherwise.
            - results (list[dict]): List of results or errors from the import process.

    Raises:
        Exception: Not raised explicitly, but request failures are logged and returned in results.
    """
    
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
        response = await httpx_client.post(url=url, data=payload, files=files, headers=headers, timeout=40.0)
    except Exception as exc:
        logger.error(f"Request error while importing product: {exc}")
        results.append({"product error": str(exc)})
        return {"status": "error", "results": results}

    if response.status_code != 201:
        logger.error(f"Failed to import product: {response.status_code} - {response.text}")
        results.append({"product {product_num} error": response.text})
    else:
        logger.info(f"Product import initiated successfully: {response.json()}")
        results.append({"product {product_num} result": response.json()})

    return {"status": "done", "results": results}