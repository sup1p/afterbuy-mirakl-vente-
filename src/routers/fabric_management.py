from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.crud import user
from src.crud.products import (change_ean_status, get_all_uploaded_fabrics,
                               get_eans_by_afterbuy_fabric_id,
                               get_filtered_uploaded_eans,
                               get_filtered_uploaded_fabrics,
                               get_users_uploaded_fabrics,
)
from src.schemas.product_schemas import changeEanStatusRequest, fabricsByStatusRequest, eansByStatusRequest
from src.core.dependencies import get_current_user, get_session

from typing import Literal

router = APIRouter()


@router.get("/uploaded-fabrics", tags=["fabric management"])
async def get_uploaded_fabrics(session: AsyncSession = Depends(get_session), current_user = Depends(get_current_user)):
    fabrics = await get_all_uploaded_fabrics(session)
    return fabrics

@router.get("/uploaded-fabrics/eans", tags=["fabric management"])
async def get_uploaded_fabric(afterbuy_fabric_id: int, session: AsyncSession = Depends(get_session), current_user = Depends(get_current_user)):
    fabric = await get_eans_by_afterbuy_fabric_id(session, afterbuy_fabric_id=afterbuy_fabric_id)
    if not fabric:
        raise HTTPException(status_code=404, detail="Fabric not found")
    return fabric

@router.get("/uploaded-fabrics/fabrics-by-status", tags=["fabric management"])
async def get_fabrics_by_status(status: Literal["pending", "processed", "error"], session: AsyncSession = Depends(get_session), current_user = Depends(get_current_user)):
    data = fabricsByStatusRequest(status=status)
    fabrics = await get_filtered_uploaded_fabrics(session, data=data)
    return fabrics

@router.get("/uploaded-eans/eans-by-status", tags=["fabric management"])
async def get_eans_by_status(afterbuy_fabric_id: int, status: Literal["pending", "processed", "error"], session: AsyncSession = Depends(get_session), current_user = Depends(get_current_user)):
    data = eansByStatusRequest(afterbuy_fabric_id=afterbuy_fabric_id, status=status)
    eans = await get_filtered_uploaded_eans(session, data=data)
    return eans

@router.get("/uploaded-eans/fabrics-by-user", tags=["fabric management"])
async def get_fabrics_by_user(user_id: int, session: AsyncSession = Depends(get_session), current_user = Depends(get_current_user)):
    if not await user.get_user_by_id(session, user_id):
        raise HTTPException(status_code=404, detail="User not found")
    fabrics = await get_users_uploaded_fabrics(session, user_id=user_id)
    return fabrics


@router.patch("/uploaded-fabrics/update-ean-status", tags=["fabric management"])
async def update_ean_status(ean: str, new_status: Literal["pending", "processed", "error"], session: AsyncSession = Depends(get_session), current_user = Depends(get_current_user)):
    data = changeEanStatusRequest(ean=ean, new_status=new_status)
    ean_obj = await change_ean_status(session, data=data)
    return ean_obj