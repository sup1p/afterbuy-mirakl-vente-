"""
Mirakl system router module.
Provides endpoints for checking Mirakl platform status, import errors, and system configuration.
"""

from fastapi import APIRouter, HTTPException, Depends

from src.services.mirakl_api_calls import (
    check_import_error,
    check_non_integrated_products,
    check_offer_import_error
)
from src.core.dependencies import get_httpx_client, get_current_user

import httpx

router = APIRouter()


@router.get("/import-product-error/{import_parameter}", tags=["mirakl_platform"])
async def get_product_error(import_parameter: str, httpx_client: httpx.AsyncClient = Depends(get_httpx_client), current_user = Depends(get_current_user)):
    """
    Returns error of product import parameter - if exists

    Args:
        import_parameter (str): import parameter that mirakl platform gave when product was imported.

    Returns:
        dict: {message: mirakl answer}.
    """
    
    try:
        result = await check_import_error(import_parameter=import_parameter, httpx_client=httpx_client)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    if isinstance(result, dict) and result.get("status") == 404:
        raise HTTPException(status_code=404, detail=result.get("message", "Not found"))
    return {"message": result}


@router.get(
    "/mirakl-product-non-integrated/{import_parameter}", tags=["mirakl_platform"]
)
async def get_product_non_integrated(import_parameter: str, httpx_client: httpx.AsyncClient = Depends(get_httpx_client), current_user = Depends(get_current_user)):
    """
    Returns non integrated products of product import parameter - if exists

    Args:
        import_parameter (str): import parameter that mirakl platform gave when product was imported.

    Returns:
        dict: {message: mirakl answer}.
    """
    
    try:
        result = await check_non_integrated_products(import_parameter, httpx_client=httpx_client)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    if isinstance(result, dict) and result.get("status") == 404:
        raise HTTPException(status_code=404, detail=result.get("message", "Not found"))
    return {"message": result}

@router.get("/mirakl-offer-import-error/{import_parameter}", tags=["mirakl_platform"])
async def get_offer_import_error(import_parameter: str, httpx_client: httpx.AsyncClient = Depends(get_httpx_client), current_user = Depends(get_current_user)):
    """
    Returns offer error of import parameter - if exists

    Args:
        import_parameter (str): import parameter that mirakl platform gave when product offer was imported.

    Returns:
        dict: {message: mirakl answer}.
    """
    
    try:
        result = await check_offer_import_error(import_parameter=import_parameter, httpx_client=httpx_client)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    if isinstance(result, dict) and result.get("status") == 404:
        raise HTTPException(status_code=404, detail=result.get("message", "Not found"))
    return {"message": result}