from fastapi import APIRouter, HTTPException

from src.services.mirakl_api_calls import (
    check_import_error,
    check_platform_settings,
    check_non_integrated_products,
)

router = APIRouter()


@router.get("/import-product-error/{import_parameter}", tags=["mirakl_platform"])
async def get_product_error(import_parameter: str):
    result = await check_import_error(import_parameter)
    if isinstance(result, dict) and result.get("status") == 404:
        raise HTTPException(status_code=404, detail=result.get("message", "Not found"))
    return {"message": result}


@router.get("/mirakl-platform-settings", tags=["mirakl_platform"])
async def get_mirakl_settings():
    return await check_platform_settings()


@router.get(
    "/mirakl-product-non-integrated/{import_parameter}", tags=["mirakl_platform"]
)
async def get_product_non_integrated(import_parameter: str):
    result = await check_non_integrated_products(import_parameter)
    if isinstance(result, dict) and result.get("status") == 404:
        raise HTTPException(status_code=404, detail=result.get("message", "Not found"))
    return {"message": result}