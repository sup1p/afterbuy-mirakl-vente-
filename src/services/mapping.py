from src.const.constants import (
    mapping_attr,
    category_attrs_map,
    mapping_attr_to_def_fallback,
    mapping_attr_with_no_map_to_def_value,
    mapping_categories_current,
    mapping_extra_attrs,
    default_html_description
)
from src.utils.substitute_formatter import substitute_attr
from src.utils.format_attr import product_quantity_check
from src.utils.image_worker import check_image_existence, process_images, resize_image_and_upload
from logs.config_logs import setup_logging
from src.utils.format_html import extract_product_properties_from_html

import json
import logging
import httpx
import aioftp

setup_logging()
logger = logging.getLogger(__name__)


def _log_html_length(html_desc: str | None):
    logger.debug("Extracted HTML description length: %s", len(html_desc) if html_desc else 0)


def safe_get(images, idx):
    return images[idx] if idx < len(images) else ""


async def _prepare_images(
    data: dict,
    httpx_client: httpx.AsyncClient,
    ftp_client = aioftp.Client,
):
    """
    Validates and processes product images. Returns tuple:
    (main_image_url, extra_images_urls_list, amount_of_resized_images)
    """
    # --- main image ---
    main_image = data.get("pic_main", "")

    if not main_image or not await check_image_existence(image_url=main_image, httpx_client=httpx_client):
        logger.error(
            f"Main image not found or inaccessible for product_id: {data.get('id')}, ean: {data.get('ean')}"
        )
        raise Exception(
            f"Main image not found or inaccessible for product_id: {data.get('id')}, ean: {data.get('ean')}"
        )

    amount_of_resized_images = 0
    process_images_result = await process_images([main_image], httpx_client)
    errors = process_images_result.get("errors", [])


    if errors:
        logger.debug(f"Main image has ERRORS, {main_image}")
        main_image = await resize_image_and_upload(url=main_image,ean=data.get("ean"),ftp_client=ftp_client,httpx_client=httpx_client)
        amount_of_resized_images = amount_of_resized_images + 1

    # --- extra images ---
    extra_images_not_checked_for_existence = str(data.get("pics", "")).split()
    extra_images_not_checked_for_size = [
        img
        for img in extra_images_not_checked_for_existence
        if await check_image_existence(image_url=img, httpx_client=httpx_client)
    ]

    processed_images_error_sizes_result = await process_images(
        extra_images_not_checked_for_size, httpx_client
    )
    processed_images_error_sizes = processed_images_error_sizes_result.get("errors", [])
    extra_images = [
        img
        for img in extra_images_not_checked_for_size
        if img not in [err[0] for err in processed_images_error_sizes]
    ]

    # ПОТОМ ПЕРЕДЕЛАТЬ ПОД ASYNCIO.GATHER
    resized_error_images = [
        await resize_image_and_upload(
            url=img[0],
            ean=data.get("ean"),
            ftp_client=ftp_client,
            httpx_client=httpx_client,
        )
        for img in processed_images_error_sizes
        if img[1] == "small"
    ]

    extra_images.extend(resized_error_images)
    amount_of_resized_images = amount_of_resized_images + len(resized_error_images)

    logger.info(
        f"Total amount of came images: {len(extra_images_not_checked_for_size)}.  Total amount of resized images: {amount_of_resized_images}"
    )

    return main_image, extra_images, amount_of_resized_images


def _parse_properties(properties_raw: str) -> dict:
    try:
        filtered_properties = json.loads(properties_raw)
    except json.JSONDecodeError:
        logger.warning("Некорректный JSON в 'properties': %s", properties_raw)
        filtered_properties = {}
    logger.info("Свойства товара: %s", filtered_properties)
    return filtered_properties


def _build_html_description(data: dict) -> str | None:
    html_desc = extract_product_properties_from_html(data.get("html_description"))
    if not html_desc or len(html_desc) < 51:
        html_desc = None
    elif len(html_desc) < 100:
        html_desc = html_desc * 2
    _log_html_length(html_desc)
    return html_desc


def _build_base_fields(
    data: dict,
    main_image: str,
    extra_images: list[str],
    html_desc: str | None,
) -> dict:
    return {
        "sku": data.get("ean"),
        "product-id": data.get("ean"),
        # "product-id": data.get("product_num"),
        "product-id-type": "EAN",
        "price": data.get("price", "0.00"),
        "state": 11,
        "quantity": product_quantity_check(data.get("article", "")),
        "brand": "407",
        "internal-description": "",
        "title_de": data.get("article"),
        "image_1": main_image,
        "image_2": safe_get(extra_images, 0),
        "image_3": safe_get(extra_images, 1),
        "image_4": safe_get(extra_images, 2),
        "image_5": safe_get(extra_images, 3),
        "image_6": safe_get(extra_images, 4),
        "image_7": safe_get(extra_images, 5),
        "image_8": safe_get(extra_images, 6),
        "image_9": safe_get(extra_images, 7),
        "image_10": safe_get(extra_images, 8),
        "category": map_categories(int(data.get("category", 0))),
        "ean": data.get("ean"),
        "description": html_desc if html_desc else default_html_description,
        "description_de": html_desc if html_desc else default_html_description,
    }


def _fill_category_attributes(filtered_properties: dict, category: str) -> dict:
    filled_attrs: dict = {}
    if category == "No mapping":
        return filled_attrs

    category_attributes = category_attrs_map.get(int(category), [])
    logger.debug("Attributes for category %s: %s", category, category_attributes)

    for attr_code in category_attributes:
        value_extra_set = False
        value_set = False
        value = None
        value_extra = None

        try:
            if attr_code in mapping_attr and mapping_attr[attr_code] != "NO MAPPING":
                source_key = mapping_attr[attr_code]

                if isinstance(source_key, list):
                    logger.debug(f"Source key for {attr_code} is list")
                    value = filtered_properties.get(source_key[0])
                    if filtered_properties.get(source_key[0]) is not None:
                        logger.debug(
                            f"Source key for {attr_code} - {source_key[0]} is not None, value = {value}"
                        )
                    if len(source_key) > 2:
                        logger.debug(f"Source key for {attr_code} is longer than 2")
                        logger.debug(f"value_extra_set: {value_extra_set}")
                        if not value_extra_set:
                            for key in source_key:
                                if filtered_properties.get(key) is not None:
                                    logger.debug(
                                        f"Source key for {attr_code} - {key} is not None, value_extra = {filtered_properties.get(key)}"
                                    )
                                    value_extra = filtered_properties.get(key)
                                    value_extra_set = True
                                    logger.debug(f"value_extra_set became: {value_extra_set}")
                                    break
                    else:
                        value_extra = filtered_properties.get(source_key[1])
                else:
                    value = filtered_properties.get(source_key)
                    value_extra = None

                if value not in (None, "", [], {}) or value_extra not in (None, "", [], {}):
                    if value:
                        filled_attrs = substitute_attr(attr_code, filled_attrs, value)
                        logger.debug("Added %s ← %s: %s", attr_code, source_key, value)
                    else:
                        filled_attrs = substitute_attr(attr_code, filled_attrs, value_extra)
                        logger.debug("Added %s ← %s: %s", attr_code, source_key, value_extra)
                else:
                    fallback_val = mapping_attr_to_def_fallback.get(attr_code, "")
                    filled_attrs[attr_code] = fallback_val
                    logger.warning(
                        "[EMPTY] %s: '%s' empty → fallback %s", attr_code, source_key, fallback_val
                    )

            elif attr_code in mapping_attr_with_no_map_to_def_value:
                val = mapping_attr_with_no_map_to_def_value[attr_code]
                filled_attrs[attr_code] = val
                logger.debug("[NO MAP] %s: set default value: %s", attr_code, val)

            else:
                fallback_val = mapping_attr_to_def_fallback.get(attr_code, "")
                filled_attrs[attr_code] = fallback_val
                logger.info("[FALLBACK] %s: not found → fallback %s", attr_code, fallback_val)

            for extra_props_val, extra_attrs_code in mapping_extra_attrs.items():
                for prop_val in filtered_properties.keys():
                    if (
                        prop_val == extra_props_val
                        and filtered_properties.get(prop_val)
                        and extra_attrs_code not in filled_attrs.keys()
                    ):
                        filled_attrs = substitute_attr(
                            extra_attrs_code, filled_attrs, filtered_properties.get(prop_val)
                        )
                        logger.debug(
                            "Added extra attribute %s ← %s: %s",
                            extra_attrs_code,
                            prop_val,
                            filtered_properties.get(prop_val),
                        )
        except Exception as e:
            fallback_val = mapping_attr_to_def_fallback.get(attr_code, "")
            filled_attrs[attr_code] = fallback_val
            logger.error("[ERROR] %s: %s → fallback %s", attr_code, e, fallback_val)

    return filled_attrs


async def map_attributes(data: dict, httpx_client: httpx.AsyncClient, ftp_client = aioftp.Client) -> dict:
    """
    Подготавливает словарь для Mirakl.
    - Обрабатывает изображения (до 10).
    - Подставляет атрибуты категории из mapping-слов.
    - Логирует ключевые этапы.
    """
    logger.info(f"Mapping attributes for product_id: {data.get('id')}, ean: {data.get('ean')}")
    # --- изображения ---
    main_image, extra_images, _ = await _prepare_images(data, httpx_client, ftp_client)

    # --- свойства товара ---
    properties_raw = data.get("properties", "{}")
    filtered_properties = _parse_properties(properties_raw)

    # --- html описание ---
    html_desc = _build_html_description(data)

    # --- базовые поля ---
    data_for_mirakl = _build_base_fields(data, main_image, extra_images, html_desc)

    # --- атрибуты категории ---
    category = data_for_mirakl["category"]
    filled_attrs = _fill_category_attributes(filtered_properties, category)

    # --- результат ---
    data_for_mirakl.update(filled_attrs)
    logger.info(
        "Ready product product-id=%s, category=%s",
        data_for_mirakl["product-id"],
        data_for_mirakl["category"],
    )

    logger.debug("Filled Attributes for Mirakl: %s \n", filled_attrs)

    return {"ean": data_for_mirakl.get("ean"), "data_for_mirakl": data_for_mirakl}


def map_categories(afterbuy_category_num: int) -> str | list[str]:
    """Находит соответствие категории Afterbuy → Mirakl."""
    key = str(afterbuy_category_num)

    # Проверка, что словарь загружен
    if not mapping_categories_current:
        logger.error("Mapping dictionary for current_categories is empty or not initialized")
        return "No mapping"

    mirakl_category_num = mapping_categories_current.get(key)

    logger.debug(f"Afterbuy category num: {afterbuy_category_num}")
    logger.debug(f"Mirakl category num: {mirakl_category_num}")

    if not mirakl_category_num:  # None, "" или []
        logger.error(f"No mapping for {afterbuy_category_num}")
        return "No mapping"

    return mirakl_category_num
