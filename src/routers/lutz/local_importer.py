# app/routers/local_importer.py
import json
import logging
from fastapi import HTTPException
from pydantic import BaseModel
import os

from app.services import mirakl  # We only need mirakl, not afterbuy
from app.utils.image_processing import _process_images_for_product
from app.utils import mapping_tools, csv_tools
from . import router, fieldnames, mapping, real_mapping_v12, color_mapping, material_mapping, brand_mapping

logger = logging.getLogger("local_importer")

# Define the paths to the local data files
DATA_DIR = "app/new data"
FABRICS_DIR = os.path.join(DATA_DIR, "FABRICS")
FABRIC_ID_FILE = os.path.join(DATA_DIR, "fabric_id.json")


def adapt_local_item_for_mapping(local_item: dict) -> dict:
    """
    Адаптирует НОВУЮ ПЛОСКУЮ структуру локального элемента JSON к структуре,
    ожидаемой основной функцией сопоставления (map_product).
    """
    # В новой структуре все атрибуты находятся на верхнем уровне.
    # Собираем их в словарь 'properties'.
    # Основные поля, которые не являются свойствами
    core_fields = {
        "Artikelbeschreibung", "Currency", "Startpreis", "Typ", "Menge",
        "SofortkaufenPreis", "CategoryID", "Category2ID", "GalleryURL",
        "PictureURL", "pictureurls", "Description", "EAN", "Fabric"
    }
    properties = {k: v for k, v in local_item.items() if k not in core_fields}
    # Добавляем EAN в properties, так как он используется и там
    properties["EAN"] = local_item.get("EAN", "")
    ean = local_item.get("EAN", "")

    # --- Получение описания из HTML ---
    html_description = ""
    if ean:
        html_path = os.path.join(DATA_DIR, "HTML", f"{ean}.html")
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

    # --- FIX for extract_dimensions ---
    for key, value in adapted_item["properties"].items():
        if "maße" in key.lower() and isinstance(value, str):
            adapted_item["properties"][key] = [value]
            break

    return adapted_item


class LocalFabricRequest(BaseModel):
    fabric_id: str


@router.post("/import-local-fabric")
async def import_local_fabric(request: LocalFabricRequest):
    """Импорт всех продуктов по fabric_id из локальных данных"""
    try:
        # 1. Find fabric name from fabric_id
        with open(FABRIC_ID_FILE, "r", encoding="utf-8") as f:
            fabric_id_map = json.load(f)

        fabric_name = fabric_id_map.get(str(request.fabric_id))
        if not fabric_name:
            raise HTTPException(status_code=404, detail=f"Fabric ID {request.fabric_id} не найден в fabric_id.json.")

        # 2. Load the correct product file based on fabric name
        # Заменяем символы, недопустимые в именах файлов
        safe_fabric_name = fabric_name.replace("/", "_").replace("\\", "_")
        products_file_path = os.path.join(FABRICS_DIR, f"{safe_fabric_name}.json")

        with open(products_file_path, "r", encoding="utf-8") as f:
            products_to_process = json.load(f)

        if not products_to_process:
            raise HTTPException(status_code=404, detail=f"Файл {products_file_path} пуст или не содержит продуктов.")

        # 3. Process and map products
        all_mapped = []
        for local_item in products_to_process:
            try:
                # Адаптируем структуру данных перед передачей в маппер
                raw_item_for_mapping = adapt_local_item_for_mapping(local_item)

                # The logic from the original router
                if "properties" in raw_item_for_mapping and isinstance(raw_item_for_mapping["properties"], str):
                    try:
                        raw_item_for_mapping["properties"] = json.loads(raw_item_for_mapping["properties"])
                    except json.JSONDecodeError:
                        raw_item_for_mapping["properties"] = {}

                # Теперь передаем адаптированные данные в маппер
                mapped = await mapping_tools.map_product(
                    raw_item_for_mapping, mapping, fieldnames,
                    real_mapping_v12, color_mapping,
                    material_mapping, {}, brand_mapping
                )

                mapped = await _process_images_for_product(mapped, raw_item_for_mapping)
                all_mapped.append(mapped)

            except Exception as e:
                # Use a more descriptive log for which product failed
                product_identifier = local_item.get('EAN') or local_item.get('Herstellernummer') or 'Unknown'
                logger.error("Error processing local product %s: %s", product_identifier, e)

        if not all_mapped:
            raise HTTPException(status_code=400, detail="Нет продуктов для импорта после обработки.")

        # 4. Create CSV and upload to Mirakl
        csv_content = csv_tools.write_csv(fieldnames, all_mapped)
        result = await mirakl.upload_csv(csv_content)

        return {
            "status": "success",
            "fabric_id": request.fabric_id,
            "fabric_name": fabric_name,
            "processed_products": len(all_mapped),
            "mirakl_response": result,
        }

    except FileNotFoundError as e:
        logger.exception("Data file not found: %s", e.filename)
        raise HTTPException(status_code=500, detail=f"Файл с данными не найден: {e.filename}")
    except Exception as e:
        logger.exception("Error importing local products for fabric_id: %s", request.fabric_id)
        raise HTTPException(status_code=500, detail=str(e))
