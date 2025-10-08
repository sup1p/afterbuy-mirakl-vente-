# app/routers/local_offers.py
import json
import logging
from fastapi import HTTPException, APIRouter, Depends
from pydantic import BaseModel
import os

from src.services.lutz_services import mirakl  # We only need mirakl, not afterbuy
from src.utils.lutz_utils.image_processing import _process_images_for_product
from src.utils.lutz_utils import mapping_tools, csv_tools
from src.utils.lutz_utils.mapping_tools import process_uvp
from src.const.constants_lutz import mapping, real_mapping_v12, color_mapping, material_mapping, brand_mapping
from .local_importer import adapt_local_item_for_mapping, FABRICS_DIR, FABRIC_ID_FILE

from logs.config_logs import setup_logging

setup_logging()

logger = logging.getLogger(__name__)

fieldnames = csv_tools.build_fieldnames(mapping)

router = APIRouter()


class LocalFabricRequest(BaseModel):
    fabric_id: str


@router.post("/import-local-offers-by-fabric", tags=["lutz"])
async def import_local_offers_by_fabric(request: LocalFabricRequest):
    """Импорт офферов по fabric_id из локальных данных."""
    try:
        # 1. Find fabric name from fabric_id
        with open(FABRIC_ID_FILE, "r", encoding="utf-8") as f:
            fabric_id_map = json.load(f)

        fabric_name = fabric_id_map.get(str(request.fabric_id))
        if not fabric_name:
            raise HTTPException(status_code=404, detail=f"Fabric ID {request.fabric_id} не найден в fabric_id.json.")

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
                raw_item_for_mapping = adapt_local_item_for_mapping(local_item)

                # Применяем стандартное сопоставление
                mapped = await mapping_tools.map_product(
                    raw_item_for_mapping, mapping, fieldnames,
                    real_mapping_v12, color_mapping,
                    material_mapping, {}, brand_mapping
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
        result = await mirakl.upload_price_csv(csv_content)

        return {
            "status": "success",
            "fabric_id": request.fabric_id,
            "fabric_name": fabric_name,
            "processed_offers": len(offers),
            "mirakl_response": result,
        }

    except FileNotFoundError:
        logger.exception("Could not find product file for fabric_id: %s", request.fabric_id)
        raise HTTPException(status_code=404, detail=f"Файл с продуктами для фабрики {fabric_name} не найден.")
    except Exception as e:
        logger.exception("Error importing local offers for fabric_id: %s", request.fabric_id)
        raise HTTPException(status_code=500, detail=str(e))
