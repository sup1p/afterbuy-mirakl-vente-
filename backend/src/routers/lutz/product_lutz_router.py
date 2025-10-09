# app/routers/import_products/product.py
import json
import logging
from fastapi import HTTPException, APIRouter, Depends

from src.services.lutz_services import afterbuy, mirakl
from src.utils.lutz_utils.image_processing import _process_images_for_product
from src.utils.lutz_utils import mapping_tools, csv_tools
from src.const.constants_lutz import mapping, real_mapping_v12, color_mapping, material_mapping, brand_mapping

from src.core.dependencies import get_current_user

from src.schemas.product_schemas import ProductRequest
from logs.config_logs import setup_logging

setup_logging()

logger = logging.getLogger(__name__)

fieldnames = csv_tools.build_fieldnames(mapping)

router = APIRouter()

@router.post("/import-product-lutz", tags=["lutz"])
async def import_product(request: ProductRequest, current_user = Depends(get_current_user)):
    try:
        raw_item = await afterbuy.fetch_product(request.product_id)

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

        csv_content = csv_tools.write_csv(fieldnames, [mapped])
        result = await mirakl.upload_csv(csv_content)

        return {
            "status": "success",
            "product_id": request.product_id,
            "mirakl_response": result,
        }

    except Exception as e:
        logger.exception("Error importing product %s", request.product_id)
        raise HTTPException(status_code=500, detail=str(e))