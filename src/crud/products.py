from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models import UploadedFabric, UploadedEan
from src.schemas.product_schemas import eansByStatusRequest, fabricsByStatusRequest, saveUploadedEan, saveUploadedFabric, changeEanStatusRequest


async def get_all_uploaded_fabrics(session: AsyncSession):
    q = select(UploadedFabric)
    res = await session.execute(q)
    return res.scalars().all()

async def get_eans_by_afterbuy_fabric_id(session: AsyncSession, afterbuy_fabric_id: int):
    q = select(UploadedEan).where(UploadedEan.afterbuy_fabric_id == afterbuy_fabric_id)
    res = await session.execute(q)
    return res.scalars().all()

async def get_filtered_uploaded_fabrics(session: AsyncSession, data: fabricsByStatusRequest):
    q = select(UploadedFabric)
    q = q.where(UploadedFabric.status == data.status)
    res = await session.execute(q)
    return res.scalars().all()

async def get_filtered_uploaded_eans(session: AsyncSession, data: eansByStatusRequest):
    q = select(UploadedEan)
    q = q.where(
        (UploadedEan.status == data.status) & 
        (UploadedEan.afterbuy_fabric_id == data.afterbuy_fabric_id)
    )
    res = await session.execute(q)
    return res.scalars().all()

async def get_users_uploaded_fabrics(session: AsyncSession, user_id: int):
    q = select(UploadedFabric).where(UploadedFabric.user_id == user_id)
    res = await session.execute(q)
    return res.scalars().all()

async def create_uploaded_fabric(session: AsyncSession, data: saveUploadedFabric) -> UploadedFabric:
    new_fabric = UploadedFabric(
        afterbuy_fabric_id=data.afterbuy_fabric_id,
        user_id=data.user_id,
        status=data.status,
        date_time=data.date_time
    )
    session.add(new_fabric)
    await session.commit()
    await session.refresh(new_fabric)
    return new_fabric

async def create_uploaded_ean(session: AsyncSession, data: saveUploadedEan) -> UploadedEan:
    new_ean = UploadedEan(
        ean=data.ean,
        afterbuy_fabric_id=data.afterbuy_fabric_id,
        title=data.title,
        image_1=data.image_1,
        image_2=data.image_2,
        image_3=data.image_3,
        user_id=data.user_id,
        uploaded_fabric_id=data.uploaded_fabric_id,
        status=data.status,
        date_time=data.date_time
    )
    session.add(new_ean)
    await session.commit()
    await session.refresh(new_ean)
    return new_ean

async def change_fabric_status(session: AsyncSession, afterbuy_fabric_id: int, new_status: str) -> UploadedFabric:
    if new_status not in ("pending", "processed", "error"):
        raise ValueError("Invalid status")
    q = select(UploadedFabric).where(UploadedFabric.afterbuy_fabric_id == afterbuy_fabric_id)
    res = await session.execute(q)
    fabric = res.scalars().first()
    if not fabric:
        raise ValueError("Fabric not found")
    fabric.status = new_status
    await session.commit()
    await session.refresh(fabric)
    return fabric

async def change_ean_status(session: AsyncSession, data: changeEanStatusRequest) -> UploadedEan:
    if data.new_status not in ("pending", "processed", "error"):
        raise ValueError("Invalid status")
    q = select(UploadedEan).where(UploadedEan.ean == data.ean)
    res = await session.execute(q)
    ean_obj = res.scalars().first()
    if not ean_obj:
        raise ValueError("EAN not found")
    ean_obj.status = data.new_status
    await session.commit()
    await session.refresh(ean_obj)
    return ean_obj