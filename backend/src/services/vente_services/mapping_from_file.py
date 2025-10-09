"""
Product data mapping module.
Transforms Afterbuy product data into Mirakl-compatible format with proper attribute mapping.
"""

from src import resources
from src.const.constants_vente.constants import (
    mapping_attr,
    category_attrs_map,
    mapping_attr_to_def_fallback,
    mapping_attr_with_no_map_to_def_value,
    mapping_categories_current,
    mapping_extra_attrs,
)
from src.const.prompts import build_description_prompt_vente
from src.utils.vente_utils.substitute_formatter import substitute_attr
from src.utils.vente_utils.format_attr import product_quantity_check
from src.core.settings import settings
from src.schemas.ai_schemas import ProductDescriptionAIVente
from src.services.vente_services.agents import get_agent
from src.utils.vente_utils.image_worker import check_image_existence, process_images, resize_image_and_upload, remove_image_bg_and_upload
from logs.config_logs import setup_logging
from src.utils.vente_utils.format_html import extract_product_properties_from_html

import logging
import httpx
import aioftp
import asyncio
import re

setup_logging()
logger = logging.getLogger(__name__)


def safe_get(images, idx):
    """
    Безопасно получает изображение из списка по индексу.

    Аргументы:
        images (list): Список URL изображений.
        idx (int): Индекс изображения для получения.

    Возвращает:
        str: URL изображения, если доступно, иначе пустую строку.
    """
    # Проверяем, находится ли индекс в пределах списка
    return images[idx] if idx < len(images) else ""

def normalize_url(url):
    """
    Нормализует URL изображений продуктов:
    - Исправляет некорректный протокол (https:: → https:).
    - Разделяет склеенные URL.
    - Убирает дублирующиеся расширения.

    Аргументы:
        url (str): Исходная строка URL.

    Возвращает:
        str: Нормализованный URL.
    """
    # Исправляем https:: на https:
    url = re.sub(r'https?::?//', 'https://', url)

    # Разделяем склеенные URL по паттерну https://
    # Ищем места где https:// встречается не в начале строки
    parts = re.split(r'(?<!^)(?=https://)', url)

    # Берем первую часть и очищаем её
    first_url = parts[0].strip()

    # Убираем возможные артефакты в конце (например, повторяющиеся расширения)
    # Ищем корректное окончание URL
    first_url = re.sub(r'\.webp.*$', '.webp', first_url)

    return first_url

async def _prepare_images(
    data: dict,
    httpx_client: httpx.AsyncClient,
    ftp_client = aioftp.Client,
):
    """
    Проверяет и обрабатывает изображения продуктов.

    Рабочий процесс:
    - Убеждается, что основное изображение существует и изменяет его размер, если нужно.
    - Извлекает дополнительные изображения из сырой строки.
    - Проверяет и изменяет размер маленьких изображений.
    - Загружает изменённые изображения через FTP.

    Аргументы:
        data (dict): Словарь данных о продукте.
        httpx_client (httpx.AsyncClient): HTTP-клиент для проверки изображений.
        ftp_client (aioftp.Client): FTP-клиент для загрузки изображений.

    Возвращает:
        tuple[str, list[str], int]:
            - main_image_url (str)
            - extra_images_urls (list of str)
            - amount_of_resized_images (int)

    Исключения:
        Exception: Если основное изображение отсутствует или недоступно.
    """
    # --- Основное изображение ---
    main_image = data.get("GalleryURL", "")
    if not main_image:
        # Логируем ошибку, если основное изображение отсутствует
        logger.error(
            f"Main image not found(probably None or empty) ean: {data.get('EAN')}"
        )
        raise Exception(
            f"Main image not found(probably None or empty) ean: {data.get('EAN')}"
        )

    main_image = normalize_url(main_image)
    pure_main_image = main_image  # сохраняем оригинал для сравнения с дополнительными изображениями
    
    
    if not await check_image_existence(image_url=main_image, httpx_client=httpx_client):
        # Логируем ошибку, если изображение недоступно
        logger.error(
            f"Main image not found or inaccessible for ean: {data.get('EAN')}"
        )
        raise Exception(
            f"Main image not found or inaccessible for ean: {data.get('EAN')}"
        )
        
    if settings.use_image_bg_remover:
        # Удаляем фон изображения, если это включено в настройках
        try:
            # Глобальный таймаут на FTP операцию удаления фона (максимум 3 минуты)
            async with asyncio.timeout(180):
                async with resources.ftp_semaphore:
                    async with aioftp.Client.context(host=settings.ftp_host,port=settings.ftp_port,user=settings.ftp_user,password=settings.ftp_password,socket_timeout=30) as ftp_client:
                        main_image = await remove_image_bg_and_upload(url=main_image, ean=data.get('EAN'), ftp_client=ftp_client, httpx_client=httpx_client)
        except asyncio.TimeoutError:
            logger.error(f"FTP operation timeout for background removal: {main_image}")
            # Продолжаем с оригинальной картинкой
        except Exception as e:
            logger.error(f"FTP operation failed for background removal: {e}")
            # Продолжаем с оригинальной картинкой


    amount_of_resized_images = 0
    process_images_result = await process_images([main_image], httpx_client)
    errors = process_images_result.get("errors", [])


    if errors:
        # Логируем ошибки обработки изображений
        logger.debug(f"Main image has ERRORS, {main_image}")
        try:
            # Глобальный таймаут на FTP операцию (максимум 2 минуты)
            async with asyncio.timeout(120):
                async with resources.ftp_semaphore:
                    async with aioftp.Client.context(host=settings.ftp_host,port=settings.ftp_port,user=settings.ftp_user,password=settings.ftp_password,socket_timeout=30) as ftp_client:
                        main_image = await resize_image_and_upload(url=main_image,ean=data.get("EAN"),ftp_client=ftp_client,httpx_client=httpx_client)
                amount_of_resized_images = amount_of_resized_images + 1
        except asyncio.TimeoutError:
            logger.error(f"FTP operation timeout for main image resize: {main_image}")
            raise Exception(f"Image resize failed due to timeout: {main_image}")
        except Exception as e:
            logger.error(f"FTP operation failed for main image resize: {e}")
            raise Exception(f"Image resize failed: {str(e)}")

    # --- Дополнительные изображения ---
    # Получаем строку с картинками
    extra_images_not_checked_for_size = data.get("pictureurls") or ""
    pics_list = []
    
    # Проверяем, есть ли в строке полные URL'ы с протоколом
    if 'http' in extra_images_not_checked_for_size:
        pics_list = [url.strip() for url in extra_images_not_checked_for_size.split(';')]
    
    # Очищаем от лишних пробелов
    pics_list = [pic.strip() for pic in pics_list if pic.strip()]
    
    # Нормализуем https::// -> https://
    pics_list = [normalize_url(pic) for pic in pics_list]
    
    # Убираем дубликат главного изображения
    pics_list = [pic for pic in pics_list if pic != pure_main_image]
    
    if len(pics_list) < 1:
        return main_image, [], amount_of_resized_images

    # Проверка размеров extra image
    processed_images_error_sizes_result = await process_images(
        pics_list, httpx_client
    )
    processed_images_error_sizes = processed_images_error_sizes_result.get("errors", [])
    
    bad_urls = [err[0] for err in processed_images_error_sizes if isinstance(err, (list, tuple)) and len(err) >= 1]
    extra_images = [img for img in pics_list if img not in bad_urls]

    # TODO: Refactor to use asyncio.gather for better performance
    resized_error_images = [
        await resize_image_and_upload(
            url=img[0],
            ean=data.get("EAN"),
            ftp_client=ftp_client,
            httpx_client=httpx_client,
        )
        for img in processed_images_error_sizes
        if img[1] == "small"
    ]
    
    logger.info(f"Resized and uploaded: {len(resized_error_images)}, - {resized_error_images}")

    extra_images.extend(resized_error_images)
    amount_of_resized_images = amount_of_resized_images + len(resized_error_images)

    if extra_images and len(extra_images) == 0:
        logger.warning("extra_images length is 0, returning empty list")
    return main_image, extra_images, amount_of_resized_images


async def _build_html_description(data: dict):
    """
    Извлекает и корректирует HTML-описание продукта.

    Правила:
    - Отбрасывает слишком короткие описания (< 51 символов).
    - Дублирует текст, если длина от 51 до 100 символов.

    Аргументы:
        data (dict): Данные о продукте, содержащие 'html_description'.

    Возвращает:
        str | None: Обработанное HTML-описание или None, если недействительно.
    """
    
    article = data.get("Artikelbeschreibung")
    delivery_days = data.get("delivery_days")
    html_desc = extract_product_properties_from_html(data.get("html_description"))
    
    if not html_desc:
        html_desc = "No html description for this product"
        logger.warning("Native html_desc is None")
        
    if not settings.use_ai_description_generator:
        return {"desc_de": html_desc, "desc_fr": html_desc}
    
    agent = get_agent()
    sem = resources.llm_semaphore

    async with sem:
        for attempt in range(3):
            try:
                result = await agent.run(
                    build_description_prompt_vente(
                        html_desc=html_desc,
                        product_article=article,
                        product_price=data.get("Startpreis"),
                        delivery_days=delivery_days,
                    ),
                    output_type=ProductDescriptionAIVente,
                    model_settings={"temperature": 0.0, "timeout": 30.0}
                )
                ai_html_desc_de = result.output.description_de.strip()
                ai_html_desc_fr = result.output.description_fr.strip()
                logger.info("AI desc length DE=%d", len(ai_html_desc_de))
                logger.info("AI desc length FR=%d", len(ai_html_desc_fr))
                break
            except Exception as e:
                logger.error(
                    f"Attempt {attempt+1}/3 failed for AI Description EAN={data.get('EAN')}: {e}"
                )
        else:
            raise Exception(
                f"All 3 attempts failed AI Description for EAN={data.get('EAN')}"
            )
    if ai_html_desc_de and ai_html_desc_fr:
        return {"desc_de": ai_html_desc_de, "desc_fr": ai_html_desc_fr}


def _build_base_fields(
    data: dict,
    main_image: str,
    extra_images: list[str],
    html_desc_de: str | None,
    html_desc_fr: str | None,
) -> dict:
    """
    Формирует базовые поля продукта Mirakl.

    Аргументы:
        data (dict): Словарь данных о продукте.
        main_image (str): URL основного изображения.
        extra_images (list[str]): Список URL дополнительных изображений.
        html_desc (str | None): Обработанное HTML-описание.

    Возвращает:
        dict: Словарь с базовыми полями продукта для Mirakl.
    """        
    
    return {
        "sku": data.get("EAN"),
        "product-id": data.get("EAN"),
        "offer-description": html_desc_fr if html_desc_fr else "",
        "product-id-type": "EAN",
        "price": data.get("Startpreis"),
        "state": 11, # new state
        "quantity": product_quantity_check(data.get("Artikelbeschreibung", "")),
        "leadtime-to-ship": data.get("delivery_days"),
        # -----------------
        "brand": "", # no brand
        "internal-description": "",
        "title_de": data.get("Artikelbeschreibung"),
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
        "category": map_categories(data.get("CategoryID", 0)),
        "ean": data.get("EAN"),
        "description": html_desc_de,
        "description_de": html_desc_de,
    }


def _fill_category_attributes(filtered_properties: dict, category: str) -> dict:
    """
    Заполняет атрибуты, специфичные для категории, для продукта.

    Рабочий процесс:
    - Сопоставляет атрибуты с помощью предопределённых словарей сопоставления.
    - Применяет запасные или значения по умолчанию, если сопоставление отсутствует.
    - Обрабатывает дополнительные атрибуты, если они определены.

    Аргументы:
        filtered_properties (dict): Распакованные свойства продукта.
        category (str): Целевая категория Mirakl ID.

    Возвращает:
        dict: Словарь заполненных атрибутов категории.
    """
    
    filled_attrs: dict = {}
    if category == "No mapping":
        return filled_attrs

    category_attributes = category_attrs_map.get(int(category), [])
    logger.info("Attributes for category %s: %s", category, category_attributes)

    for attr_code in category_attributes:
        value_extra_set = False
        value = None
        value_extra = None

        try:
            if attr_code in mapping_attr and mapping_attr[attr_code] != "NO MAPPING":
                source_key = mapping_attr[attr_code]

                if isinstance(source_key, list):
                    logger.debug(f"Source key for {attr_code} is list")
                    value = filtered_properties.get(source_key[0])
                    if len(source_key) > 2:
                        if not value_extra_set:
                            for key in source_key:
                                if filtered_properties.get(key) is not None:
                                    logger.debug(
                                        f"Source key for {attr_code} - {key} is not None, value_extra = {filtered_properties.get(key)}"
                                    )
                                    value_extra = filtered_properties.get(key)
                                    value_extra_set = True
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
                logger.warning("[NO MAP] %s: set default value: %s", attr_code, val)

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

async def map_attributes(data: dict, httpx_client: httpx.AsyncClient) -> dict:
    """
    Сопоставляет данные о продукте Afterbuy в формат, совместимый с Mirakl.

    Рабочий процесс:
    - Обрабатывает изображения продукта (основное + дополнительные).
    - Парсит и сопоставляет свойства продукта.
    - Формирует базовые поля и атрибуты категории.
    - Логирует этапы обработки.

    Аргументы:
        data (dict): Сырые данные о продукте из Afterbuy.
        httpx_client (httpx.AsyncClient): HTTP-клиент для проверки изображений.

    Возвращает:
        dict: Словарь со структурой:
              {
                  "ean": str,
                  "data_for_mirakl": dict
              }
    """
        
    if map_categories(data.get("CategoryID", 0)) in ("No mapping", 0):
        logger.error("No mapping for ean: %s \n", data.get("EAN"))
        raise Exception(
            f"No mapping found for product with ean: {data.get("EAN")}",
        )

    if not data.get("Startpreis"):
        raise Exception(
            f"No price found for product with ean: {data.get("EAN")}",
        )
    
    # --- images ---
    async with resources.ftp_semaphore:
        async with aioftp.Client.context(host=settings.ftp_host,port=settings.ftp_port,user=settings.ftp_user,password=settings.ftp_password,socket_timeout=30) as ftp_client:
            main_image, extra_images, _ = await _prepare_images(data, httpx_client, ftp_client)
    
    # --- html description ---
    html_desc = await _build_html_description(data=data)
    html_desc_de = html_desc.get("desc_de")
    html_desc_fr = html_desc.get("desc_fr")

    # --- base fields ---
    data_for_mirakl = _build_base_fields(data=data, main_image=main_image, extra_images=extra_images, html_desc_de=html_desc_de, html_desc_fr=html_desc_fr)

    # --- category attributes ---
    category = map_categories(data.get("CategoryID", 0))
    filled_attrs = _fill_category_attributes(data, category)
    
    # --- result ---
    data_for_mirakl.update(filled_attrs)
    logger.info(
        "Ready product product-id=%s, category=%s",
        data_for_mirakl["product-id"],
        data_for_mirakl["category"],
    )

    logger.info("Filled Attributes for Mirakl: %s \n", filled_attrs)

    return {"ean": data_for_mirakl.get("ean"), "data_for_mirakl": data_for_mirakl}


def map_categories(afterbuy_category_num: int) -> str | list[str]:
    """
    Сопоставляет номер категории Afterbuy с Mirakl категории.

    Аргументы:
        afterbuy_category_num (int): Номер категории Afterbuy.

    Возвращает:
        str | list[str]: Соответствующий Mirakl ID категории(ий), или "No mapping", если не найдено.
    """
    
    key = str(afterbuy_category_num)

    # Check that dictionary is loaded
    if not mapping_categories_current:
        logger.error("Mapping dictionary for current_categories is empty or not initialized")
        return "No mapping"

    mirakl_category_num = mapping_categories_current.get(key)

    logger.debug(f"Afterbuy category num: {afterbuy_category_num}")
    logger.debug(f"Mirakl category num: {mirakl_category_num}")

    if not mirakl_category_num:  # None, "" or []
        logger.error(f"No mapping for {afterbuy_category_num}")
        return "No mapping"

    return mirakl_category_num
