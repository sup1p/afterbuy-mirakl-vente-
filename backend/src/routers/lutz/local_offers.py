# app/routers/local_offers.py
import json
import logging
from fastapi import HTTPException, APIRouter, Depends
from pydantic import BaseModel
import os

from src.crud.products import create_uploaded_ean, create_uploaded_fabric, get_uploaded_ean_by_ean_and_fabric, get_uploaded_fabric_by_afterbuy_id_and_shop, update_uploaded_ean
from src.services.lutz_services import mirakl  # We only need mirakl, not afterbuy
from src.utils.lutz_utils.image_processing import _process_images_for_product
from src.utils.lutz_utils import mapping_tools, csv_tools
from src.utils.lutz_utils.mapping_tools import process_uvp
from src.schemas.product_schemas import FabricWithDeliveryAndMarketRequest, saveUploadedEan, saveUploadedEan, saveUploadedFabric
from src.schemas.user_schemas import UserOut
from src.const.constants_lutz import mapping, real_mapping_v12, color_mapping, material_mapping, brand_mapping
from src.core.dependencies import get_current_user, get_session
from src.utils.vente_utils.format_little import split_images
from .local_importer import adapt_local_item_for_mapping, FABRICS_DIR, FABRIC_ID_FILE

from sqlalchemy.ext.asyncio import AsyncSession


from logs.config_logs import setup_logging

setup_logging()

logger = logging.getLogger(__name__)

fieldnames = csv_tools.build_fieldnames(mapping)

router = APIRouter()



@router.post("/import-products-by-fabric-from-file/xxxlutz", tags=["lutz"])
async def import_local_offers_by_fabric(request: FabricWithDeliveryAndMarketRequest, session: AsyncSession = Depends(get_session), current_user = Depends(get_current_user)):
    """Импорт офферов по fabric_id из локальных данных."""
    
    afterbuy_fabric_id = request.afterbuy_fabric_id
    delivery_days = request.delivery_days
    market = request.market
    
    try:
        # 1. Find fabric name from fabric_id
        with open(FABRIC_ID_FILE, "r", encoding="utf-8") as f:
            fabric_id_map = json.load(f)

        fabric_name = fabric_id_map.get(str(afterbuy_fabric_id))
        if not fabric_name:
            raise HTTPException(status_code=404, detail=f"Fabric ID {afterbuy_fabric_id} не найден в fabric_id.json.")

        # 2. Load the correct product file based on fabric name
        safe_fabric_name = fabric_name.replace("/", "_").replace("\\", "_")
        products_file_path = os.path.join(FABRICS_DIR, f"{safe_fabric_name}.json")

        with open(products_file_path, "r", encoding="utf-8") as f:
            products_to_process = json.load(f)

        if not products_to_process:
            raise HTTPException(status_code=404, detail=f"Файл {products_file_path} пуст или не содержит продуктов.")

        # 3. Process each product to create an offer
        offers = []
        for local_item in products_to_process:
            try:
                # Адаптируем структуру данных перед передачей в маппер
                raw_item_for_mapping = adapt_local_item_for_mapping(local_item, market)

                # Применяем стандартное сопоставление
                mapped = await mapping_tools.map_product(
                    raw_item_for_mapping, mapping, fieldnames,
                    real_mapping_v12, color_mapping,
                    material_mapping, {}, brand_mapping, delivery_days
                )

                # Этот шаг может быть избыточным для офферов, но оставим для консистентности
                mapped = await _process_images_for_product(mapped, raw_item_for_mapping)

                # --- Логика специфичная для офферов ---
                original_price_str = raw_item_for_mapping.get("price", "0.00")
                original_price = 0.0
                try:
                    # В JSON цена может быть строкой с запятой
                    original_price = float(original_price_str.replace(",", "."))
                except (ValueError, TypeError):
                    logger.warning("Could not convert price '%s' to float for product EAN=%s. Defaulting to 0.0.",
                                 original_price_str, raw_item_for_mapping.get("ean"))

                mapped["price"] = f"{original_price:.2f}"
                mapped["product_reference_price"] = f"{process_uvp(original_price):.2f}"
                mapped["state"] = 11
                mapped["quantity"] = mapping_tools.product_quantity_check(raw_item_for_mapping.get("article", ""))
                # --- Конец специфичной логики ---

                offers.append(mapped)

            except Exception as e:
                product_identifier = local_item.get('EAN') or local_item.get('Herstellernummer') or 'Unknown'
                logger.error("Error processing offer for local product %s: %s", product_identifier, e)

        if not offers:
            raise HTTPException(status_code=400, detail="Не удалось построить офферы")


        # Добавляем новое поле в заголовки CSV, если его там нет
        offer_fieldnames = fieldnames.copy()
        if "product_reference_price" not in offer_fieldnames:
            offer_fieldnames.append("product_reference_price")

        csv_content = csv_tools.write_csv(offer_fieldnames, offers)
        # result = await mirakl.upload_price_csv(csv_content)
        
        
        
        
        # DATABASE SAVING FABRIC
        database_fabric_data = saveUploadedFabric(
            afterbuy_fabric_id=afterbuy_fabric_id,
            user_id=current_user.id,
             market=market,
             shop="xxxlutz"
        )

        fabric_obj = await get_uploaded_fabric_by_afterbuy_id_and_shop(session=session, afterbuy_fabric_id=afterbuy_fabric_id, shop="xxxlutz")
        database_created = "already exists"
        
        if not fabric_obj:
            fabric_obj = await create_uploaded_fabric(session=session, data=database_fabric_data)
            database_created = "created"
            logger.info(f"Created new Uploaded Fabric entry for Afterbuy fabric ID {afterbuy_fabric_id}")
        
        
        
        # DATABASE SAVING EANS
        for prod_idx, prod in enumerate(offers, start=1):
            # getting all images of the product
            product_images = split_images(prod.get("images.secondary_image"))
            database_ean_data = saveUploadedEan(
                ean=prod.get("ean"),
                afterbuy_fabric_id=afterbuy_fabric_id,
                title=prod.get("title"),
                image_1=prod.get("images.main_image"),
                image_2=product_images[0] if len(product_images) > 0 else "",
                image_3=product_images[1] if len(product_images) > 1 else "",
                user_id=current_user.id,
                uploaded_fabric_id=fabric_obj.id,
            )
            existing_ean = await get_uploaded_ean_by_ean_and_fabric(session=session, ean=prod.get("ean"), afterbuy_fabric_id=afterbuy_fabric_id)
            if existing_ean:
                await update_uploaded_ean(session=session, ean_obj=existing_ean, data=database_ean_data)
                logger.info(f"[{prod_idx}/{len(offers)}] Updated EAN {prod.get('ean')} in database.")
            else:
                await create_uploaded_ean(session=session, data=database_ean_data)
                logger.info(f"[{prod_idx}/{len(offers)}] Saved EAN {prod.get('ean')} to database.")


        return {
            "status": "success",
            "fabric_id": afterbuy_fabric_id,
            "fabric_name": fabric_name,
            "processed_offers": len(offers),
            # "mirakl_response": result,
            "database_status": database_created,
            "csv_preview": offers  # Возвращаем первые 500 символов CSV для проверки
        }

    except FileNotFoundError:
        logger.exception("Could not find product file for fabric_id: %s", afterbuy_fabric_id)
        raise HTTPException(status_code=404, detail=f"Файл с продуктами для фабрики {fabric_name} не найден.")
    except Exception as e:
        logger.exception("Error importing local offers for fabric_id: %s", afterbuy_fabric_id)
        raise HTTPException(status_code=500, detail=str(e))
