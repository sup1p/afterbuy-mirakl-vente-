# app/routers/afterbuy_fabric.py
import json
import logging
from fastapi import HTTPException
from pydantic import BaseModel
from fastapi import HTTPException, APIRouter, Depends

from src.services.lutz_services import afterbuy, mirakl
from src.utils.lutz_utils.image_processing import _process_images_for_product
from src.utils.lutz_utils import mapping_tools, csv_tools
from src.const.constants_lutz import mapping, real_mapping_v12, color_mapping, material_mapping, brand_mapping

from src.core.dependencies import get_current_user

from src.schemas.product_schemas import FabricRequest
from logs.config_logs import setup_logging

setup_logging()

logger = logging.getLogger(__name__)

fieldnames = csv_tools.build_fieldnames(mapping)

router = APIRouter()


class AfterbuyIdRequest(BaseModel):
    afterbuy_id: str


@router.post("/import-by-afterbuy-id")
async def import_by_afterbuy_id(request: AfterbuyIdRequest):
    """
    Импорт всех продуктов по afterbuy_id.
    Сначала получает fabric_id, затем выполняет стандартный импорт.
    """
    try:
        # Шаг 1: Получаем fabric_id по afterbuy_id
        fabric_id = await afterbuy.fetch_fabric_by_afterbuy_id(request.afterbuy_id)
        if fabric_id is None:
            raise HTTPException(
                status_code=404,
                detail=f"Не удалось найти fabric_id для afterbuy_id: {request.afterbuy_id}",
            )

        # Шаг 2: Выполняем остальную логику, как в import_fabric
        product_ids = await afterbuy.fetch_products_by_fabric(fabric_id)
        all_mapped = []

        for pid in product_ids:
            try:
                raw_item = await afterbuy.fetch_product(pid)

                # Обрабатываем поле properties, если оно строковое
                if "properties" in raw_item and isinstance(raw_item["properties"], str):
                    try:
                        raw_item["properties"] = json.loads(raw_item["properties"])
                    except json.JSONDecodeError:
                        raw_item["properties"] = {}

                # Применяем маппинг продукта
                mapped = await mapping_tools.map_product(
                    raw_item, mapping, fieldnames,
                    real_mapping_v12, color_mapping,
                    material_mapping, {}, brand_mapping
                )

                # Обрабатываем изображения для продукта
                mapped = await _process_images_for_product(mapped, raw_item)
                all_mapped.append(mapped)

            except Exception as e:
                logger.error("Error processing product_id=%s: %s", pid, e)

        if not all_mapped:
            raise HTTPException(status_code=400, detail="Нет продуктов для импорта")

        # Создаем CSV и загружаем в Mirakl
        csv_content = csv_tools.write_csv(fieldnames, all_mapped)
        result = await mirakl.upload_csv(csv_content)

        return {
            "status": "success",
            "afterbuy_id": request.afterbuy_id,
            "resolved_fabric_id": fabric_id,
            "processed_products": len(all_mapped),
            "mirakl_response": result,
        }

    except Exception as e:
        logger.exception("Error importing products for afterbuy_id: %s", request.afterbuy_id)
        raise HTTPException(status_code=500, detail=str(e))
