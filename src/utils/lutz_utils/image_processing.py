# app/services/image_processing.py
"""
Image processing service.
Проверяет размер картинок, при необходимости ресайзит и загружает на FTP.
Если по EAN уже есть готовая картинка на FTP — используем её.
Возвращает новые ссылки (или оригинальные, если resize отключён или картинка уже валидна).
"""

import io
import os
import re
import asyncio
import logging
import unicodedata
from urllib.parse import unquote, urlparse, quote
from typing import Optional, Tuple

from src.core.settings import settings
from src import resources

import httpx
import aioftp
from PIL import Image, UnidentifiedImageError
from logs.config_logs import setup_logging

setup_logging()

logger = logging.getLogger(__name__)


# ---- Хелпер обработки картинок ----
async def _process_images_for_product(mapped: dict, raw_item: dict) -> dict:
    """
    Обработка изображений:
    - скачиваем все картинки параллельно через httpx
    - ресайзим (если нужно)
    - заливаем на FTP по очереди (иначе aioftp падает с readuntil error)
    - возвращаем корректные URL без битых символов
    """

    if not settings.enable_image_resize_lutz:
        return mapped

    ean = raw_item.get("ean") or raw_item.get("gtin") or raw_item.get("sku") or "unknown"

    main_url = (mapped.get("images.main_image") or "").strip()
    secondary_field = mapped.get("images.secondary_image") or ""
    secondary_urls = [u.strip() for u in re.split(r"[\s,]+", secondary_field) if u.strip()]

    if not main_url and not secondary_urls:
        return mapped

    try:
        async with resources.ftp_semaphore:
            async with aioftp.Client.context(
                host=settings.ftp_host,
                port=settings.ftp_port,
                user=settings.ftp_user,
                password=settings.ftp_password,
                socket_timeout=20
            ) as ftp_client, httpx.AsyncClient(timeout=30.0) as http_client:

                # Сначала скачиваем все картинки параллельно
                urls = []
                if main_url:
                    urls.append(("main", main_url))
                urls.extend([("sec", u) for u in secondary_urls])

                download_tasks = [download_image_bytes(url, http_client) for _, url in urls]
                downloaded = await asyncio.gather(*download_tasks, return_exceptions=True)

                results = []
                for (typ, orig), res in zip(urls, downloaded):
                    if isinstance(res, Exception):
                        logger.error("Ошибка скачивания %s: %s", orig, res)
                        results.append((typ, orig))  # оставляем оригинал
                        continue

                    img_bytes, err = res
                    if not img_bytes:
                        logger.error("Не удалось скачать %s: %s", orig, err)
                        results.append((typ, orig))
                        continue

                    # ресайз (если нужно)nnnn
                    img_bytes, ext, was_resized = check_and_resize(img_bytes)

                    # если картинка нормальная и resize выключен, оставляем оригинал
                    if not was_resized:
                        results.append((typ, orig))
                        continue

                    # FTP upload (⚠️ строго последовательно!)
                    path = urlparse(orig).path
                    orig_file_name = normalize_basename(os.path.basename(path))
                    if not orig_file_name.endswith(f".{ext}"):
                        orig_file_name = f"{orig_file_name}.{ext}"

                    try:
                        new_url = await upload_to_ftp(img_bytes, orig_file_name, ean, ftp_client)
                        results.append((typ, new_url))
                    except Exception as e:
                        logger.error("Ошибка загрузки %s → %s", orig, e)
                        results.append((typ, orig))

                # собираем обратно в mapped
                sec_results = []
                for typ, url in results:
                    if typ == "main":
                        mapped["images.main_image"] = url
                        mapped["main_picture"] = url
                    else:
                        sec_results.append(url)

                mapped["images.secondary_image"] = " ".join(sec_results) if sec_results else ""

    except Exception as e:
        logger.exception("FTP/HTTP ошибка при обработке картинок (product ean=%s): %s", ean, e)
        return mapped

    return mapped

# =============================== helpers ===============================


def normalize_basename(name: str) -> str:
    """Нормализация имени файла для FTP."""
    name = unquote(name or "")
    name = unicodedata.normalize("NFC", name)
    name = re.sub(r'[<>:"|?*\x00-\x1f]', '_', name)
    name = name.replace('/', '_').replace('\\', '_')
    name = re.sub(r'\s+', '_', name).strip()
    return name


async def download_image_bytes(url: str, httpx_client: httpx.AsyncClient) -> Tuple[Optional[bytes], Optional[str]]:
    """Скачиваем байты картинки по URL."""
    try:
        resp = await httpx_client.get(url, timeout=20.0)
        if resp.status_code == 200 and resp.headers.get("Content-Type", "").startswith("image/"):
            return resp.content, None
        return None, f"Invalid response: {resp.status_code} {resp.headers.get('Content-Type')}"
    except Exception as e:
        return None, str(e)


def check_and_resize(img_bytes: bytes) -> Tuple[bytes, str, bool]:
    """
    Проверка размеров картинки. Если меньше минимальных — ресайзим.
    Добавлена защита от слишком больших изображений и улучшенная обработка ошибок.
    """
    try:
        # Быстрая проверка - это вообще изображение?
        if len(img_bytes) < 100:  # слишком маленькие данные
            return img_bytes, "jpg", False
            
        with Image.open(io.BytesIO(img_bytes)) as im:
            w, h = im.size
            
            # Проверка максимальных размеров для безопасности (10k x 10k пикселей)
            max_dimension = 10000
            if w > max_dimension or h > max_dimension:
                logger.warning(f"Изображение слишком большое: {w}x{h} пикселей (макс {max_dimension})")
                return img_bytes, "jpg", False
            
            # Если размер уже достаточный - возвращаем как есть
            if w >= settings.min_image_width and h >= settings.min_image_height:
                return img_bytes, im.format.lower() if im.format else "jpg", False

            # Вычисляем новые размеры для ресайза
            scale = max(settings.min_image_width / w, settings.min_image_height / h)
            new_w, new_h = int(round(w * scale)), int(round(h * scale))
            
            # Проверяем, что новые размеры разумные
            if new_w > max_dimension or new_h > max_dimension:
                logger.warning(f"Результат ресайза слишком большой: {new_w}x{new_h}")
                return img_bytes, "jpg", False
            
            # Выполняем ресайз
            im = im.resize((new_w, new_h), Image.LANCZOS)

            # Определяем формат вывода
            if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
                out_format, ext = "PNG", "png"
            else:
                im = im.convert("RGB")
                out_format, ext = "JPEG", "jpg"

            # Сохраняем в байты
            out = io.BytesIO()
            im.save(out, format=out_format, quality=85 if out_format == "JPEG" else None)
            result_bytes = out.getvalue()
            
                
            return result_bytes, ext, True
            
    except UnidentifiedImageError:
        logger.debug("Неизвестный формат изображения")
        return img_bytes, "jpg", False
    except (OSError, IOError) as e:
        logger.warning(f"Ошибка чтения изображения (возможно поврежден): {e}")
        return img_bytes, "jpg", False
    except MemoryError:
        logger.error("Недостаточно памяти для обработки изображения")
        return img_bytes, "jpg", False
    except Exception as e:
        logger.error(f"Неожиданная ошибка обработки изображения: {e}")
        return img_bytes, "jpg", False


async def ftp_file_exists(ftp_client: aioftp.Client, ean: str, filename: str) -> Optional[str]:
    """
    Проверяем, существует ли файл на FTP.
    Если да — возвращаем URL.
    """
    remote_dir = f"{settings.ftp_base_dir}/{ean}"
    filename_only = normalize_basename(filename)
    try:
        await ftp_client.change_directory(remote_dir)
        files = [f.name async for f in ftp_client.list()]
        if filename_only in files:
            url_safe = quote(filename_only)
            return f"{settings.image_base_url}/{ean}/{url_safe}"
    except aioftp.StatusCodeError as e:
        if "550" not in str(e):  # папки может ещё не быть
            logger.error(f"FTP ошибка при проверке файла {filename}: {e}")
    return None


async def upload_to_ftp(data: bytes, filename: str, ean: str, ftp_client: aioftp.Client) -> str:
    """Загрузка изображения на FTP и возврат его URL."""
    filename_only = normalize_basename(os.path.basename(filename))
    remote_dir = f"{settings.ftp_base_dir}/{ean}"

    try:
        await ftp_client.make_directory(remote_dir, parents=True)
    except aioftp.StatusCodeError as e:
        if "550" not in str(e):
            raise

    await ftp_client.change_directory(remote_dir)

    temp_filename = filename_only
    with open(temp_filename, "wb") as f:
        f.write(data)

    await ftp_client.upload(temp_filename)
    os.unlink(temp_filename)

    url_safe = quote(filename_only)
    return f"{settings.image_base_url}/{ean}/{url_safe}"


# =============================== main API ===============================

async def process_single_image(
    url: str,
    ean: str,
    ftp_client: aioftp.Client,
    httpx_client: httpx.AsyncClient,
) -> Optional[str]:
    """
    Проверка + ресайз (если нужно) + загрузка.
    - Если resize выключен → возвращает оригинал.
    - Если >=800x800 → возвращает оригинал.
    - Если меньше → проверяем FTP:
        - если файл по EAN уже есть → возвращаем ссылку на него
        - иначе делаем ресайз и загружаем
    """
    if not settings.enable_image_resize_lutz:
        return url

    img_bytes, err = await download_image_bytes(url, httpx_client)
    if not img_bytes:
        logger.error(f"Не удалось скачать {url}: {err}")
        return url

    img_bytes, ext, was_resized = check_and_resize(img_bytes)

    if not was_resized:
        return url

    path = urlparse(url).path
    filename = os.path.basename(path)
    filename = unquote(filename)
    orig_file_name = normalize_basename(filename)

    if not orig_file_name.endswith(f".{ext}"):
        orig_file_name = f"{orig_file_name}.{ext}"

    # ⚡ Новое: проверяем, есть ли уже файл на FTP
    existing_url = await ftp_file_exists(ftp_client, ean, orig_file_name)
    if existing_url:
        logger.info(f"Найдена готовая картинка на FTP для EAN={ean}, файл={orig_file_name}")
        return existing_url

    # иначе — загружаем
    try:
        new_url = await upload_to_ftp(img_bytes, orig_file_name, ean, ftp_client)
        return new_url
    except Exception as e:
        logger.error(f"Ошибка загрузки {url} → {e}")
        return url