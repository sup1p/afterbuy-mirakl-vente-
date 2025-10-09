"""
Модуль роутера системы Mirakl.
Предоставляет эндпоинты для проверки статуса платформы Mirakl, ошибок импорта и конфигурации системы.
"""

from fastapi import APIRouter, HTTPException, Depends

from src.services.vente_services.mirakl_api_calls import (
    check_import_error,
    check_non_integrated_products,
    check_offer_import_error
)
from src.core.dependencies import get_httpx_client, get_current_user

import httpx

router = APIRouter()


@router.get("/import-product-error/{import_parameter}", tags=["mirakl_platform_vente"])
async def get_product_error(import_parameter: str, httpx_client: httpx.AsyncClient = Depends(get_httpx_client), current_user = Depends(get_current_user)):
    """
    Возвращает ошибку импорта продукта по параметру импорта - если существует.
    """
    
    try:
        # Проверяем ошибку импорта продукта
        result = await check_import_error(import_parameter=import_parameter, httpx_client=httpx_client)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    if isinstance(result, dict) and result.get("status") == 404:
        raise HTTPException(status_code=404, detail=result.get("message", "Not found"))
    return {"message": result}


@router.get(
    "/mirakl-product-non-integrated/{import_parameter}", tags=["mirakl_platform_vente"]
)
async def get_product_non_integrated(import_parameter: str, httpx_client: httpx.AsyncClient = Depends(get_httpx_client), current_user = Depends(get_current_user)):
    """
    Возвращает неинтегрированные продукты по параметру импорта - если существуют.
    """
    
    try:
        # Проверяем неинтегрированные продукты
        result = await check_non_integrated_products(import_parameter, httpx_client=httpx_client)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    if isinstance(result, dict) and result.get("status") == 404:
        raise HTTPException(status_code=404, detail=result.get("message", "Not found"))
    return {"message": result}

@router.get("/mirakl-offer-import-error/{import_parameter}", tags=["mirakl_platform_vente"])
async def get_offer_import_error(import_parameter: str, httpx_client: httpx.AsyncClient = Depends(get_httpx_client), current_user = Depends(get_current_user)):
    """
    Возвращает ошибку импорта предложения по параметру импорта - если существует.
    """
    
    try:
        # Проверяем ошибку импорта предложения
        result = await check_offer_import_error(import_parameter=import_parameter, httpx_client=httpx_client)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    if isinstance(result, dict) and result.get("status") == 404:
        raise HTTPException(status_code=404, detail=result.get("message", "Not found"))
    return {"message": result}