from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models import UploadedFabric, UploadedEan
from src.schemas.product_schemas import eansByStatusRequest, fabricsByStatusRequest, saveUploadedEan, saveUploadedFabric, changeEanStatusRequest,changeFabricStatusRequest


async def get_all_uploaded_fabrics(session: AsyncSession, limit: int = 10, offset: int = 0):
    q = select(UploadedFabric).limit(limit).offset(offset)
    res = await session.execute(q)
    return res.scalars().all()

async def get_uploaded_fabric_by_afterbuy_id(session: AsyncSession, afterbuy_fabric_id: int):
    q = select(UploadedFabric).where(UploadedFabric.afterbuy_fabric_id == afterbuy_fabric_id)
    res = await session.execute(q)
    return res.scalars().first()

async def get_eans_by_afterbuy_fabric_id(session: AsyncSession, afterbuy_fabric_id: int, limit: int = 10, offset: int = 0):
    fabric_exists = await session.execute(
        select(UploadedFabric.id).where(UploadedFabric.afterbuy_fabric_id == afterbuy_fabric_id)
    )
    if fabric_exists.scalar() is None:
        return "Not Found"

    res = await session.execute(select(UploadedEan).where(UploadedEan.afterbuy_fabric_id == afterbuy_fabric_id).limit(limit).offset(offset))
    eans = res.scalars().all()

    return eans

async def get_filtered_uploaded_fabrics(session: AsyncSession, data: fabricsByStatusRequest, limit: int = 10, offset: int = 0):
    q = select(UploadedFabric)
    q = q.where(UploadedFabric.status == data.status)
    q = q.limit(limit).offset(offset)
    res = await session.execute(q)
    return res.scalars().all()

async def get_filtered_uploaded_eans(session: AsyncSession, data: eansByStatusRequest, limit: int = 10, offset: int = 0):
    q = select(UploadedEan)
    q = q.where(
        (UploadedEan.status == data.status) & 
        (UploadedEan.afterbuy_fabric_id == data.afterbuy_fabric_id)
    ).limit(limit).offset(offset)
    res = await session.execute(q)
    return res.scalars().all()

async def get_users_uploaded_fabrics(session: AsyncSession, user_id: int, limit: int = 10, offset: int = 0):
    q = select(UploadedFabric).where(UploadedFabric.user_id == user_id)
    q = q.limit(limit).offset(offset)
    res = await session.execute(q)
    return res.scalars().all()

async def create_uploaded_fabric(session: AsyncSession, data: saveUploadedFabric) -> UploadedFabric:
    new_fabric = UploadedFabric(
        afterbuy_fabric_id=data.afterbuy_fabric_id,
        user_id=data.user_id,
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
    )
    session.add(new_ean)
    await session.commit()
    await session.refresh(new_ean)
    return new_ean

async def change_fabric_status(session: AsyncSession, data: changeFabricStatusRequest) -> UploadedFabric:
    if data.new_status not in ("pending", "processed", "error"):
        raise ValueError("Invalid status")
    q = select(UploadedFabric).where(UploadedFabric.afterbuy_fabric_id == data.afterbuy_fabric_id)
    res = await session.execute(q)
    fabric = res.scalars().first()
    if not fabric:
        raise ValueError("Fabric not found")
    fabric.status = data.new_status
    await session.commit()
    await session.refresh(fabric)
    return fabric

async def change_ean_status(session: AsyncSession, data: changeEanStatusRequest) -> UploadedEan:
    if data.new_status not in ("pending", "processed", "error"):
        raise ValueError("Invalid status")
    q = select(UploadedEan).where(UploadedEan.id == data.id)
    res = await session.execute(q)
    ean_obj = res.scalars().first()
    if not ean_obj:
        raise ValueError("ID not found")
    ean_obj.status = data.new_status
    await session.commit()
    await session.refresh(ean_obj)
    return ean_obj

async def delete_fabric_by_afterbuy_id(session: AsyncSession, afterbuy_fabric_id: int) -> bool:
    q = select(UploadedFabric).where(UploadedFabric.afterbuy_fabric_id == afterbuy_fabric_id)
    res = await session.execute(q)
    fabric = res.scalars().first()
    if not fabric:
        return False
    await session.delete(fabric)
    await session.commit()
    return True