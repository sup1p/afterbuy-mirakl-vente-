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
        market=data.market,
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
    await update_fabric_status_based_on_eans(session, new_ean.uploaded_fabric_id)
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
    await update_fabric_status_based_on_eans(session, ean_obj.uploaded_fabric_id)
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

async def get_uploaded_ean_by_ean_and_fabric(session: AsyncSession, ean: str, afterbuy_fabric_id: int):
    q = select(UploadedEan).where(
        (UploadedEan.ean == ean) & (UploadedEan.afterbuy_fabric_id == afterbuy_fabric_id)
    )
    res = await session.execute(q)
    return res.scalars().first()

async def update_uploaded_ean(session: AsyncSession, ean_obj: UploadedEan, data: saveUploadedEan) -> UploadedEan:
    ean_obj.title = data.title
    ean_obj.image_1 = data.image_1
    ean_obj.image_2 = data.image_2
    ean_obj.image_3 = data.image_3
    ean_obj.user_id = data.user_id
    ean_obj.uploaded_fabric_id = data.uploaded_fabric_id
    ean_obj.status = data.status
    await session.commit()
    await session.refresh(ean_obj)
    await update_fabric_status_based_on_eans(session, ean_obj.uploaded_fabric_id)
    return ean_obj

async def update_fabric_status_based_on_eans(session: AsyncSession, uploaded_fabric_id: int):
    print(f"Updating fabric status based on EANs for fabric ID {uploaded_fabric_id}")
    # Получить все EAN'ы для fabric
    q = select(UploadedEan).where(UploadedEan.uploaded_fabric_id == uploaded_fabric_id)
    res = await session.execute(q)
    eans = res.scalars().all()
    
    if not eans:
        return  # Нет EAN'ов, ничего не делать
    
    statuses = {ean.status for ean in eans}
    
    if "error" in statuses:
        new_status = "error"
        print(f"Setting fabric ID {uploaded_fabric_id} status to 'error' due to EAN errors")
    elif all(status == "processed" for status in statuses):
        new_status = "processed"
        print(f"Setting fabric ID {uploaded_fabric_id} status to 'processed' as all EANs are processed")
    else:
        new_status = "pending"
        print(f"Setting fabric ID {uploaded_fabric_id} status to 'pending' as there are pending EANs")
    
    # Обновить статус fabric
    q_fabric = select(UploadedFabric).where(UploadedFabric.id == uploaded_fabric_id)
    res_fabric = await session.execute(q_fabric)
    fabric = res_fabric.scalars().first()
    if fabric and fabric.status != new_status:
        fabric.status = new_status
        await session.commit()