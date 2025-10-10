# app/routers/local_importer.py
import json
import logging
from fastapi import HTTPException, APIRouter, Depends
import os

from src.core.dependencies import get_current_user
from src.schemas.product_schemas import FabricWithDeliveryAndMarketRequest
from src.services.lutz_services import mirakl
from src.utils.lutz_utils.image_processing import _process_images_for_product
from src.utils.lutz_utils import mapping_tools, csv_tools
from src.const.constants_lutz import mapping, real_mapping_v12, color_mapping, material_mapping, brand_mapping

from logs.config_logs import setup_logging

setup_logging()

logger = logging.getLogger(__name__)

fieldnames = csv_tools.build_fieldnames(mapping)

router = APIRouter()


# Define the paths to the local data files
DATA_DIR = "src/const/import_data"
FABRICS_DIR = os.path.join(DATA_DIR, "fabrics_jv")
FABRIC_ID_FILE = os.path.join(DATA_DIR, "fabric_id.json")


def adapt_local_item_for_mapping(local_item: dict, market: str) -> dict:
    """
    Адаптирует НОВУЮ ПЛОСКУЮ структуру локального элемента JSON к структуре,
    ожидаемой основной функцией сопоставления (map_product).
    """
    core_fields = {
        "Artikelbeschreibung", "Currency", "Startpreis", "Typ", "Menge",
        "SofortkaufenPreis", "CategoryID", "Category2ID", "GalleryURL",
        "PictureURL", "pictureurls", "Description", "EAN", "Fabric"
    }
    properties = {k: v for k, v in local_item.items() if k not in core_fields}
    properties["EAN"] = local_item.get("EAN", "")
    ean = local_item.get("EAN", "")

    html_description = ""
    if ean:
        html_path = os.path.join(DATA_DIR, f"HTML_{market}", f"{ean}.html")
        try:
            with open(html_path, "r", encoding="utf-8") as f:
                html_description = f.read()
        except FileNotFoundError:
            logger.warning("HTML file not found for EAN %s at path %s", ean, html_path)
        except Exception as e:
            logger.error("Error reading HTML file for EAN %s: %s", ean, e)

    adapted_item = {
        "article": local_item.get("Artikelbeschreibung", ""),
        "price": local_item.get("Startpreis", "0.00"),
        "category": local_item.get("CategoryID", ""),
        "pic_main": local_item.get("GalleryURL", ""),
        "pics": local_item.get("pictureurls", ""),
        "ean": ean,
        "properties": properties,
        "html_description": html_description,
    }

    for key, value in adapted_item["properties"].items():
        if "maße" in key.lower() and isinstance(value, str):
            adapted_item["properties"][key] = [value]
            break

    return adapted_item


@router.post("/import-local-fabric", tags=["lutz"])
async def import_local_fabric(request: FabricWithDeliveryAndMarketRequest):
    """Импорт всех продуктов по fabric_id из локальных данных"""
    afterbuy_fabric_id = request.afterbuy_fabric_id
    delivery_days = request.delivery_days
    market = request.market

    try:
        with open(FABRIC_ID_FILE, "r", encoding="utf-8") as f:
            fabric_id_map = json.load(f)

        fabric_name = fabric_id_map.get(str(afterbuy_fabric_id))
        if not fabric_name:
            raise HTTPException(status_code=404, detail=f"Fabric ID {afterbuy_fabric_id} не найден в fabric_id.json.")

        safe_fabric_name = fabric_name.replace("/", "_").replace("\\", "_")
        products_file_path = os.path.join(FABRICS_DIR, f"{safe_fabric_name}.json")

        with open(products_file_path, "r", encoding="utf-8") as f:
            products_to_process = json.load(f)

        if not products_to_process:
            raise HTTPException(status_code=404, detail=f"Файл {products_file_path} пуст или не содержит продуктов.")

        all_mapped = []
        for local_item in products_to_process:
            try:
                raw_item_for_mapping = adapt_local_item_for_mapping(local_item, market)

                if "properties" in raw_item_for_mapping and isinstance(raw_item_for_mapping["properties"], str):
                    try:
                        raw_item_for_mapping["properties"] = json.loads(raw_item_for_mapping["properties"])
                    except json.JSONDecodeError:
                        raw_item_for_mapping["properties"] = {}

                mapped = await mapping_tools.map_product(
                    raw_item_for_mapping, mapping, fieldnames,
                    real_mapping_v12, color_mapping,
                    material_mapping, {}, brand_mapping,
                    delivery_days
                )

                mapped = await _process_images_for_product(mapped, raw_item_for_mapping)
                all_mapped.append(mapped)

            except Exception as e:
                product_identifier = local_item.get('EAN') or local_item.get('Herstellernummer') or 'Unknown'
                logger.error("Error processing local product %s: %s", product_identifier, e)

        if not all_mapped:
            raise HTTPException(status_code=400, detail="Нет продуктов для импорта после обработки.")

        csv_content = csv_tools.write_csv(fieldnames, all_mapped)
        result = await mirakl.upload_csv(csv_content)

        return {
            "status": "success",
            "fabric_id": afterbuy_fabric_id,
            "fabric_name": fabric_name,
            "processed_products": len(all_mapped),
            "mirakl_response": result,
        }

    except FileNotFoundError as e:
        logger.exception("Data file not found: %s", e.filename)
        raise HTTPException(status_code=500, detail=f"Файл с данными не найден: {e.filename}")
    except Exception as e:
        logger.exception("Error importing local products for fabric_id: %s", afterbuy_fabric_id)
        raise HTTPException(status_code=500, detail=str(e))
