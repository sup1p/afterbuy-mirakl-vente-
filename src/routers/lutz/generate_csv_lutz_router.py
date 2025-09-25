# app/routers/import_products/product.py
import json
import logging
from fastapi import HTTPException, APIRouter

from src.services.lutz_services import afterbuy
from src.utils.lutz_utils.image_processing import _process_images_for_product
from src.utils.lutz_utils import mapping_tools, csv_tools
from src.const.constants_lutz import mapping, real_mapping_v12, color_mapping, material_mapping, brand_mapping

from src.schemas.product_schemas import FabricRequest
from logs.config_logs import setup_logging

setup_logging()

logger = logging.getLogger(__name__)

fieldnames = csv_tools.build_fieldnames(mapping)

router = APIRouter()


@router.post("/generate-fabric-csv-lutz", tags=["lutz"])
async def generate_fabric_csv(request: FabricRequest):
    """Генерирует CSV для всех продуктов по fabric_id без отправки в Mirakl"""
    try:
        product_ids = await afterbuy.fetch_products_by_fabric(request.fabric_id)
        all_mapped = []

        for pid in product_ids:
            try:
                raw_item = await afterbuy.fetch_product(pid)

                if "properties" in raw_item and isinstance(raw_item["properties"], str):
                    try:
                        raw_item["properties"] = json.loads(raw_item["properties"])
                    except json.JSONDecodeError:
                        raw_item["properties"] = {}

                mapped = await mapping_tools.map_product(
                    raw_item, mapping, fieldnames,
                    real_mapping_v12, color_mapping,
                    material_mapping, {}, brand_mapping
                )

                mapped = await _process_images_for_product(mapped, raw_item)
                all_mapped.append(mapped)

            except Exception as e:
                logger.error("Error processing product_id=%s: %s", pid, e)

        if not all_mapped:
            raise HTTPException(status_code=400, detail="Нет продуктов для генерации CSV")

        # csv_content = csv_tools.write_csv(fieldnames, all_mapped)

        return {
            "status": "success",
            "fabric_id": request.fabric_id,
            "processed_products": len(all_mapped),
            "csv_content": all_mapped,
        }

    except Exception as e:
        logger.exception("Error generating CSV for fabric_id: %s", request.fabric_id)
        raise HTTPException(status_code=500, detail=str(e))