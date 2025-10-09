"""
Модуль роутера управления продуктами.
Предоставляет эндпоинты для импорта продуктов из Afterbuy в систему Mirakl.
"""

from fastapi import APIRouter, HTTPException, Depends

from src.crud.products import create_uploaded_fabric, get_uploaded_fabric_by_afterbuy_id_and_shop, create_uploaded_ean, get_uploaded_ean_by_ean_and_fabric, update_uploaded_ean
from src.schemas.product_schemas import saveUploadedFabric, FabricWithDeliveryAndMarketRequest, saveUploadedEan
from src.services.vente_services.mirakl_api_calls import import_product as import_product_mirakl
from src.services.vente_services.afterbuy_api_calls import get_products_by_fabric_from_file
from src.services.vente_services.csv_converter import make_big_csv
from src.services.vente_services.mapping_from_file import map_attributes
from src.core.dependencies import get_httpx_client, get_current_user, get_session
from logs.config_logs import setup_logging

from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

import logging
import httpx

setup_logging()
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/import-products-by-fabric-from-file/vente", tags=["product vente by fabric"])
async def import_products_by_fabric(input_body: FabricWithDeliveryAndMarketRequest, httpx_client: httpx.AsyncClient = Depends(get_httpx_client), session: AsyncSession = Depends(get_session), current_user = Depends(get_current_user)):
    """
    Импорт продуктов по ID фабрики Afterbuy из Afterbuy в Mirakl.
    """

    afterbuy_fabric_id = input_body.afterbuy_fabric_id
    delivery_days = input_body.delivery_days
    market = input_body.market
    
    try:
        # Получаем данные продуктов для фабрики из файла
        data = await get_products_by_fabric_from_file(afterbuy_fabric_id=afterbuy_fabric_id, market=market)
    except Exception as e:
        logger.error(f"Error fetching data for fabric {afterbuy_fabric_id}: {e}")
        raise HTTPException(
            status_code=403,
            detail=str(e),
        )
    
    if not data:
        logger.error(f"No products found for fabric {afterbuy_fabric_id}")
        raise HTTPException(
            status_code=404,
            detail=f"No products found for fabric {afterbuy_fabric_id}",
        )
        

    products = data.get("products", [])
    not_added_eans = data.get("not_added_eans", [])
    afterbuy_fabric_name = data.get("fabric_name")
    
    all_eans = {prod.get("EAN") for prod in products}

    logger.info(f"Fetched {len(products)} products for fabric {afterbuy_fabric_id}")
    
    data_for_csv = []
    processed_eans = set()
    
    # Обрабатываем продукты последовательно
    for idx, prod in enumerate(products, start=1):
        try:
            # Добавляем дни доставки и сопоставляем атрибуты из файла
            prod["delivery_days"] = delivery_days
            logger.info(f"[{idx}/{len(products)}] Started processing product with EAN={prod.get('EAN')}")
            res = await map_attributes(prod, httpx_client)
            logger.info(f"[{idx}/{len(products)}] Processed product with EAN={prod.get('EAN')}")
            
            data_for_mirakl = res.get("data_for_mirakl")
            processed_eans.add(data_for_mirakl.get('ean'))
            data_for_csv.append(data_for_mirakl)
            
        except Exception as e:
            logger.error(f"[{idx}/{len(products)}] Error processing product EAN={prod.get('EAN')}: {e}")
            continue

    not_added_eans.extend(list(all_eans - processed_eans))
    not_added_eans = list(set(not_added_eans))  # Убираем дубликаты

    logger.info(
        f"not_added_eans: {not_added_eans},\n total_not_added: {len(not_added_eans)}, \n total eans in fabric: {len(all_eans)}"
    )
    
    # Создаем большой CSV из данных
    csv_content = make_big_csv(data_for_csv)
    
    if not csv_content:
        logger.error(f"Making csv failed or make_csv got no 'data' for fabric: {afterbuy_fabric_id}")
        raise HTTPException(
            status_code=404,
            detail=f"Creating big csv failed for fabric: {afterbuy_fabric_id}",
        )

    try:
        # Импортируем продукты в Mirakl
        mirakl_answer = await import_product_mirakl(csv_content, httpx_client=httpx_client)
    except Exception as e:
        logger.error(f"Error importing products to Mirakl: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

    # Сохраняем данные фабрики в базу
    database_fabric_data = saveUploadedFabric(
        afterbuy_fabric_id=afterbuy_fabric_id,
        user_id=current_user.id,
        market=market,
        shop="vente",
    )
    fabric_obj = await get_uploaded_fabric_by_afterbuy_id_and_shop(session=session, afterbuy_fabric_id=afterbuy_fabric_id, shop="vente")
    database_created = "already exists"
    
    if not fabric_obj:
        fabric_obj = await create_uploaded_fabric(session=session, data=database_fabric_data)
        database_created = "created"
        logger.info(f"Created new Uploaded Fabric entry for Afterbuy fabric ID {afterbuy_fabric_id}")
        
    # Сохраняем данные EAN в базу
    for prod_idx, prod in enumerate(data_for_csv, start=1):
        database_ean_data = saveUploadedEan(
            ean=prod.get("ean"),
            afterbuy_fabric_id=afterbuy_fabric_id,
            title=prod.get("title_de"),
            image_1=prod.get("image_1"),
            image_2=prod.get("image_2"),
            image_3=prod.get("image_3"),
            user_id=current_user.id,
            uploaded_fabric_id=fabric_obj.id,
        )
        existing_ean = await get_uploaded_ean_by_ean_and_fabric(session=session, ean=prod.get("ean"), afterbuy_fabric_id=afterbuy_fabric_id)
        if existing_ean:
            await update_uploaded_ean(session=session, ean_obj=existing_ean, data=database_ean_data)
            logger.info(f"[{prod_idx}/{len(data_for_csv)}] Updated EAN {prod.get('ean')} in database.")
        else:
            await create_uploaded_ean(session=session, data=database_ean_data)
            logger.info(f"[{prod_idx}/{len(data_for_csv)}] Saved EAN {prod.get('ean')} to database.")
    

    return {
        "mirakl_answer": mirakl_answer,
        "not_added_eans": not_added_eans,
        "total_not_added": len(not_added_eans),
        "delivery days": delivery_days,
        "total_eans_in_fabric": len(all_eans),
        "afterbuty_fabric_name": afterbuy_fabric_name,
        "database_status": database_created    
    }