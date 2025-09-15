from logs.config_logs import setup_logging
from src.core.settings import settings
from urllib.parse import urlparse


import io
import tempfile
import os
from PIL import Image, UnidentifiedImageError

import httpx
import logging
import asyncio
import aioftp

setup_logging()
logger = logging.getLogger(__name__)


async def check_image_existence(image_url: str, httpx_client: httpx.AsyncClient) -> bool:
    if settings.check_image_existence is False:
        return True
    
    if not image_url:
        return False
    
        
    try:
        response = await httpx_client.head(image_url)
    except Exception as e:
        logger.error(f"Error while checking image at {image_url}: {e}")
        return False
    
    if response.status_code == 200:
        logger.debug(f"Image found at {image_url}")
        return True
    else:
        logger.warning(f"Image not found at {image_url}, status code: {response.status_code}")
        return False
    

async def get_image_size(url: str, client: httpx.AsyncClient):
    try:
        headers = {"Range": "bytes=0-20000"}  # читаем первые 20KB
        resp = await client.get(url, headers=headers, timeout=10)
        resp.raise_for_status()

        try:
            img = Image.open(io.BytesIO(resp.content))
            img.verify()  # проверяем, что изображение не повреждено
            img = Image.open(io.BytesIO(resp.content))  # нужно открыть заново после verify
            logger.info(f"Image {url[:50]} sizes: {img.size}")
            return url, img.size
        except Exception as e:
            logger.warning(f"Image {url[:50]} error: {e}")
            return url, f"Pillow error: {e}"
        
    except Exception as e:
        logger.warning(f"Image {url[:50]} error: {e}")
        return url, e  # вернём ошибку вместе с url
    

async def process_images(urls: list[str], client: httpx.AsyncClient):
    """Асинхронно с помощью gather проверяет размеры изображения на соответсвие требованиям."""
    if len(urls) > 1:
        tasks = [get_image_size(url, client) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.debug(f"Results: {results}")

        sizes = {}
        errors = []

        for url, res in results:
            if isinstance(res, Exception):
                errors.append((url, res))
            elif res[0] < settings.min_image_width or res[1] < settings.min_image_height:
                errors.append((url, "small"))
            else:
                sizes[url] = res  # (w, h)

        logger.info(f"Processed: Normal images: {len(sizes)}, images with errors: {len(errors)}")
        
        return {
            "sizes": sizes,   # словарь {url: (width, height)}
            "errors": errors  # список [(url, "ошибка")]
        }
    else:
        result = await get_image_size(urls[0], client)
        errors = []
        sizes = result[1]
        
        if result[1][0] < settings.min_image_width or result[1][1] < settings.min_image_height:
            errors.append((urls[0], "small"))
        
        return {
            "sizes": sizes,   # tuple (w,h) 
            "errors": errors  # список [(url, "ошибка")]
        }
    


async def download_image_bytes(url: str, client: httpx.AsyncClient):
    try:
        resp = await client.get(url, timeout=30)
        resp.raise_for_status()

        # Проверяем заголовок
        ctype = resp.headers.get("Content-Type", "")
        if not ctype.startswith("image/"):
            logger.warning(f"URL не вернул изображение: {url}, Content-Type: {ctype}")
            return None, f"URL не вернул изображение: {url}, Content-Type: {ctype}"

        return resp.content, None
    except Exception as e:
        logger.error(f"Ошибка при скачивании изображения {url}: {e}")
        return None, e



def resize_image_bytes(img_bytes: bytes):
    try:
        with Image.open(io.BytesIO(img_bytes)) as im:
            w, h = im.size
            if w == 0 or h == 0:
                logger.error("Некорректные размеры изображения")
                return None, "Некорректные размеры изображения"

            # Масштабирование (увеличиваем, если меньше минимума)
            scale_h = settings.min_image_height / h
            scale_w = settings.min_image_width / w
            scale = max(scale_h, scale_w)

            new_w = int(round(w * scale))
            new_h = int(round(h * scale))

            im = im.resize((new_w, new_h), Image.LANCZOS)

            # Конвертация в RGB, если нужно (JPEG не поддерживает P/RGBA)
            if im.mode in ("P", "RGBA", "LA"):
                im = im.convert("RGB")

            out = io.BytesIO()
            # Всегда сохраняем в JPEG
            im.save(out, format="JPEG", quality=85)

            return out.getvalue(), "jpg"

    except UnidentifiedImageError:
        logger.error("Переданные байты не являются изображением")
        return None, "Переданные байты не являются изображением"
    except Exception as e:
        logger.error(f"Ошибка при обработке изображения: {e}")
        return None, f"Ошибка при обработке изображения: {e}"


async def upload_to_ftp(data: bytes, filename: str, remote_dir: str, ean: str,ftp_client: aioftp.Client) -> str:
    """Асинхронная загрузка на FTP через aioftp."""
    if remote_dir:
        try:
            await ftp_client.make_directory(remote_dir, parents=True)
        except aioftp.StatusCodeError as e:
            if "550" not in str(e):
                raise
        await ftp_client.change_directory(remote_dir)

    logger.debug("Start of file upload")

    temp_filename = filename
    filename = os.path.basename(filename)
    current_dir = await ftp_client.get_current_directory()
    print("Current FTP directory:", current_dir)
    
    try:
        # Записываем данные во временный файл
        with open(temp_filename, 'wb') as temp_file:
            temp_file.write(data)
        
        # Загружаем файл - aioftp увидит только имя файла без слешей
        await ftp_client.upload(temp_filename)
    finally:
        # Удаляем временный файл
        if os.path.exists(temp_filename):
            os.unlink(temp_filename)
    
    logger.debug("End of file upload")
    
    
    return f"{settings.image_base_url}/{ean}/{filename}"


async def file_exists_on_ftp(filename: str, remote_dir: str, ean: str, ftp_client: aioftp.Client) -> bool:
    """
    Проверяет, существует ли файл на FTP.
    """
    if remote_dir:
        try:
            await ftp_client.change_directory(remote_dir)
        except aioftp.StatusCodeError as e:
            # Если директории нет, то файла точно нет
            if "550" in str(e):
                return False
            raise

    try:
        await ftp_client.stat(filename)
        return f"{settings.image_base_url}/{ean}/{filename}"
    except aioftp.StatusCodeError as e:
        # код 550 — файл не найден
        if "550" in str(e):
            return False
        raise


async def resize_image_and_upload(
    url: str,
    ean: str,
    ftp_client: aioftp.Client,
    httpx_client: httpx.AsyncClient
) -> str:
    """
    1. Скачивает изображение по URL.
    2. Ресайзит (с сохранением пропорций).
    3. Загружает на FTP.
    4. Возвращает путь к файлу на FTP.
    """
    # 1. Скачиваем байты
    img_bytes, err = await download_image_bytes(url, httpx_client)
    if img_bytes is None:
        logger.error(f"Error occured while downloading image: {url}, error: {err}")
        raise Exception(f"While downloading image: {url}, error: {err}")

    # 2. Ресайз (CPU-операция → уводим в поток, чтобы не блокировать event loop)
    resized_bytes, ext_or_arr = await asyncio.to_thread(resize_image_bytes, img_bytes)
    
    if resized_bytes is None:
        logger.error(f"Ошибка ресайза: {ext_or_arr}")
        raise Exception(f"While resizing image: {url}, error: {ext_or_arr}")
    
    # 3. Генерация имени файла
    path = urlparse(url).path
    orig_file_name_with_ext = os.path.basename(path)
    orig_file_name, _ = os.path.splitext(orig_file_name_with_ext)
    orig_file_name = f"{orig_file_name}.{ext_or_arr}"
    
    # out_path = os.path.join(os.getcwd(), orig_file_name)
    # with open(out_path, "wb") as f:
    #     f.write(resized_bytes)

    # print(f"Файл сохранён локально: {out_path}")

    # # вернём путь к локальному файлу (для проверки)
    # return out_path

    
    # 4. Проверка на существование
    existing_url = await file_exists_on_ftp(filename=orig_file_name, remote_dir=f"/xlmoebel.at/image/afterbuy_resized_images_for_mirakl/{ean}", ean=ean,ftp_client=ftp_client)
    if existing_url:
        logger.info(f"Image {orig_file_name} already exists in ftp server, returning its address")
        return existing_url
    
    logger.debug(f"Image {orig_file_name} does not exist in ftp server, importing there")

    # 5. Загрузка на FTP
    ftp_url = await upload_to_ftp(data=resized_bytes, filename=orig_file_name, remote_dir=f"/xlmoebel.at/image/afterbuy_resized_images_for_mirakl/{ean}", ean=ean,ftp_client=ftp_client)

    return ftp_url