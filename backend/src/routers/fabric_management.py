from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.crud import user
from src.crud.products import (change_ean_status, delete_fabric_by_afterbuy_id_and_shop, get_all_uploaded_fabrics,
                               get_eans_by_afterbuy_fabric_id_and_shop,
                               get_filtered_uploaded_eans,
                               get_filtered_uploaded_fabrics, get_uploaded_fabric_by_afterbuy_id_and_shop, get_uploaded_fabrics_by_shop,
                               get_users_uploaded_fabrics,
)
from src.schemas.product_schemas import changeEanStatusRequest, fabricsByStatusRequest, eansByStatusRequest
from src.core.dependencies import get_current_user, get_session

from typing import Literal

router = APIRouter()


@router.get("/uploaded-fabrics", tags=["fabric management"])
async def get_uploaded_fabrics(session: AsyncSession = Depends(get_session),
                               current_user = Depends(get_current_user),
                               limit: int = Query(10, ge=1, le=100),
                               offset: int = Query(0, ge=0)
                               ):
    fabrics = await get_all_uploaded_fabrics(session=session, limit=limit, offset=offset)
    return fabrics



@router.get("/uploaded-fabrics/fabrics-by-status", tags=["fabric management"])
async def get_fabrics_by_status(status: str = Query("pending", pattern="^(pending|processed|error)$"),
                                session: AsyncSession = Depends(get_session),
                                current_user = Depends(get_current_user),
                                limit: int = Query(10, ge=1, le=100),
                                offset: int = Query(0, ge=0)
                                ):
    data = fabricsByStatusRequest(status=status)
    fabrics = await get_filtered_uploaded_fabrics(session=session, data=data, limit=limit, offset=offset)
    return fabrics

@router.get("/uploaded-fabrics/fabrics-by-shop", tags=["fabric management"])
async def get_fabrics_by_shop(shop: str = Query(..., pattern="^(vente|xxxlutz)$"),
                               session: AsyncSession = Depends(get_session),
                               current_user = Depends(get_current_user),
                               limit: int = Query(10, ge=1, le=100),
                               offset: int = Query(0, ge=0)
                               ):
    fabrics = await get_uploaded_fabrics_by_shop(session=session, shop=shop, limit=limit, offset=offset)
    return fabrics

@router.get("/uploaded-eans/eans-by-status", tags=["fabric management"])
async def get_eans_by_status(afterbuy_fabric_id: int,
                             status: Literal["pending", "processed", "error"],
                             session: AsyncSession = Depends(get_session),
                             current_user = Depends(get_current_user),
                             limit: int = Query(10, ge=1, le=100),
                             offset: int = Query(0, ge=0)
                             ):
    data = eansByStatusRequest(afterbuy_fabric_id=afterbuy_fabric_id, status=status)
    eans = await get_filtered_uploaded_eans(session, data=data, limit=limit, offset=offset)
    return eans

@router.get("/uploaded-fabrics/fabrics-by-user", tags=["fabric management"])
async def get_fabrics_by_user(user_id: int,
                              session: AsyncSession = Depends(get_session),
                              current_user = Depends(get_current_user),
                              limit: int = Query(10, ge=1, le=100),
                              offset: int = Query(0, ge=0)
                              ):
    if not await user.get_user_by_id(session, user_id):
        raise HTTPException(status_code=404, detail="User not found")
    fabrics = await get_users_uploaded_fabrics(session, user_id=user_id, limit=limit, offset=offset)
    return fabrics

@router.patch("/uploaded-fabrics/update-ean-status", tags=["fabric management"])
async def update_ean_status(data: changeEanStatusRequest, session: AsyncSession = Depends(get_session), current_user = Depends(get_current_user)):
    try:
        ean_obj = await change_ean_status(session, data=data)
    except ValueError:
        raise HTTPException(status_code=404, detail="ID not found")
    return ean_obj

@router.delete("/uploaded-fabrics/vente/delete-fabric", tags=["fabric management"])
async def delete_fabric_vente(afterbuy_fabric_id: int, session: AsyncSession = Depends(get_session), current_user = Depends(get_current_user)):
    result = await delete_fabric_by_afterbuy_id_and_shop(session, afterbuy_fabric_id=afterbuy_fabric_id, shop="vente")
    if not result:
        raise HTTPException(status_code=404, detail="Fabric not found")
    return {"detail": "Fabric deleted successfully"}

@router.delete("/uploaded-fabrics/xxxlutz/delete-fabric", tags=["fabric management"])
async def delete_fabric_xxxlutz(afterbuy_fabric_id: int, session: AsyncSession = Depends(get_session), current_user = Depends(get_current_user)):
    result = await delete_fabric_by_afterbuy_id_and_shop(session, afterbuy_fabric_id=afterbuy_fabric_id, shop="xxxlutz")
    if not result:
        raise HTTPException(status_code=404, detail="Fabric not found")
    return {"detail": "Fabric deleted successfully"}


@router.get("/uploaded-fabrics/vente/{afterbuy_fabric_id}", tags=["fabric management"])
async def get_uploaded_fabric_vente(afterbuy_fabric_id: int, session: AsyncSession = Depends(get_session), current_user = Depends(get_current_user)):
    fabric = await get_uploaded_fabric_by_afterbuy_id_and_shop(session, afterbuy_fabric_id=afterbuy_fabric_id, shop="vente")
    if not fabric:
        raise HTTPException(status_code=404, detail="Fabric not found")
    return fabric

@router.get("/uploaded-fabrics/xxxlutz/{afterbuy_fabric_id}", tags=["fabric management"])
async def get_uploaded_fabric_xxxlutz(afterbuy_fabric_id: int, session: AsyncSession = Depends(get_session), current_user = Depends(get_current_user)):
    fabric = await get_uploaded_fabric_by_afterbuy_id_and_shop(session, afterbuy_fabric_id=afterbuy_fabric_id, shop="xxxlutz")
    if not fabric:
        raise HTTPException(status_code=404, detail="Fabric not found")
    return fabric

@router.get("/uploaded-fabrics/vente/{afterbuy_fabric_id}/eans", tags=["fabric management"])
async def get_uploaded_fabric_eans_vente(afterbuy_fabric_id: int,
                                   session: AsyncSession = Depends(get_session),
                                   current_user = Depends(get_current_user),
                                   limit: int = Query(10, ge=1, le=100),
                                   offset: int = Query(0, ge=0)
                                   ):
    eans = await get_eans_by_afterbuy_fabric_id_and_shop(session=session,
                                                  afterbuy_fabric_id=afterbuy_fabric_id,
                                                  shop="vente",
                                                  limit=limit,
                                                  offset=offset
    )
    if eans == "Not Found":
        raise HTTPException(status_code=404, detail="EANs not found")
    return eans

@router.get("/uploaded-fabrics/xxxlutz/{afterbuy_fabric_id}/eans", tags=["fabric management"])
async def get_uploaded_fabric_eans_xxxlutz(afterbuy_fabric_id: int,
                                   session: AsyncSession = Depends(get_session),
                                   current_user = Depends(get_current_user),
                                   limit: int = Query(10, ge=1, le=100),
                                   offset: int = Query(0, ge=0)
                                   ):
    eans = await get_eans_by_afterbuy_fabric_id_and_shop(session=session,
                                                  afterbuy_fabric_id=afterbuy_fabric_id,
                                                  shop="xxxlutz",
                                                  limit=limit,
                                                  offset=offset
    )
    if eans == "Not Found":
        raise HTTPException(status_code=404, detail="EANs not found")
    return eans