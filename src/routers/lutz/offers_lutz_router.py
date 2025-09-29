# app/routers/import_products/product.py
import json
import logging
from fastapi import APIRouter, HTTPException, Depends

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


@router.post("/import-fabric-offers-lutz", tags=["lutz"])
async def import_fabric_offers(request: FabricRequest, current_user = Depends(get_current_user)):
    """Импорт офферов по fabric_id"""
    try:
        product_ids = await afterbuy.fetch_products_by_fabric(request.fabric_id)
        offers = []

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

                mapped["price"] = str(raw_item.get("price", "0.00"))
                mapped["state"] = 11
                mapped["quantity"] = mapping_tools.product_quantity_check(raw_item.get("article", ""))

                offers.append(mapped)

            except Exception as e:
                logger.error("Error processing offer for product_id=%s: %s", pid, e)

        if not offers:
            raise HTTPException(status_code=400, detail="Не удалось построить офферы")

        csv_content = csv_tools.write_csv(fieldnames, offers)
        result = await mirakl.upload_price_csv(csv_content)

        return {
            "status": "success",
            "fabric_id": request.fabric_id,
            "processed_offers": len(offers),
            "mirakl_response": result,
        }

    except Exception as e:
        logger.exception("Error importing offers for fabric_id: %s", request.fabric_id)
        raise HTTPException(status_code=500, detail=str(e))