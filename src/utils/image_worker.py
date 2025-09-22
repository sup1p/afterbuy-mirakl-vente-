"""
Image processing utilities module.
Handles image validation, resizing, and FTP upload operations.
"""

from logs.config_logs import setup_logging
from src.core.settings import settings


import io
import os
import re
from urllib.parse import unquote, quote, urlparse
from PIL import Image, UnidentifiedImageError
from typing import Optional

import httpx
import logging
import asyncio
import aioftp

setup_logging()
logger = logging.getLogger(__name__)


async def check_image_existence(image_url: str, httpx_client: httpx.AsyncClient, retries: int = 3, timeout: int = 5) -> bool:
    """
    Verify whether an image is accessible at the given URL.

    The function attempts to check the image's availability using an HTTP HEAD request. 
    If HEAD is not supported (403/405), it falls back to GET. Retries with exponential 
    backoff are used in case of failures.

    Args:
        image_url (str): The URL of the image.
        httpx_client (httpx.AsyncClient): Asynchronous HTTP client instance.
        retries (int, optional): Number of retry attempts. Defaults to 3.
        timeout (int, optional): Timeout per request in seconds. Defaults to 5.

    Returns:
        bool: True if the image is accessible (HTTP 200), False otherwise.
    """
    
    if settings.check_image_existence is False:
        return True

    if not image_url:
        return False

    image_url = unquote(image_url)

    for attempt in range(1, retries + 1):
        try:
            response = await httpx_client.head(image_url, timeout=40.0)
            if response.status_code == 200:
                return True
            elif response.status_code in (403, 405):  
                # 403 Forbidden или 405 Method Not Allowed — часто указывает, что HEAD не поддерживается
                response = await httpx_client.get(image_url, timeout=40.0)
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Attempt {attempt}/{retries} failed for {image_url}: {e}")
            if attempt < retries:
                await asyncio.sleep(2 ** attempt)  # экспоненциальная задержка

    logger.error(f"Image not accessible at {image_url} after {retries} attempts")
    return False
    

async def get_image_size(url: str, httpx_client: httpx.AsyncClient):
    """
    Retrieve image dimensions by partially downloading the image.

    Downloads the first 2 MB of the image to read its metadata and determine 
    width and height without fetching the entire file.

    Args:
        url (str): Image URL.
        httpx_client (httpx.AsyncClient): Asynchronous HTTP client instance.

    Returns:
        tuple: A tuple (url, (width, height)) if successful, or (url, Exception) if an error occurred.

    Raises:
        Exception: If all retry attempts fail or a non-recoverable error occurs.
    """
    
    for attempt in range(3):
        try:
            headers = {"Range": "bytes=0-2000000"}  # Read first 2000KB
            resp = await httpx_client.get(url, headers=headers, timeout=40.0)
            if resp.status_code in [200, 206]:
                try:
                    img = Image.open(io.BytesIO(resp.content))
                    logger.debug(f"Image {url[:50]} sizes: {img.size}")
                    return url, img.size
                except Exception as e:
                    logger.warning(f"Image {url[:50]} error: {e}")
                    return url, e
            resp.raise_for_status()

        except Exception as e:
            if attempt == 2:
                logger.warning(f"Image {url[:50]} error: {e}")
                return url, e  # Return error along with url
            await asyncio.sleep(0.5 * (attempt+1))
            continue
            
        # Handle non-200 status codes
        if attempt == 2:  # Last attempt
            logger.error(f"Failed to get check image existence: {resp.status_code}")
            raise Exception(f"Error checking image existence: {resp.status_code}")
        await asyncio.sleep(0.5 * (attempt + 1))  # Wait before retry
            

async def process_images(urls: list[str], httpx_client: httpx.AsyncClient):
    """
    Validate multiple images asynchronously and check their dimensions.

    Uses asyncio.gather to fetch image sizes in parallel. 
    Validates dimensions against configured minimum width and height.

    Args:
        urls (list[str]): List of image URLs to process.
        httpx_client (httpx.AsyncClient): Asynchronous HTTP client instance.

    Returns:
        dict: Dictionary containing:
            - sizes (dict): Mapping {url: (width, height)} for valid images.
            - errors (list): List of (url, error) tuples for invalid or small images.
    """
    
    if len(urls) > 1:
        tasks = [get_image_size(url, httpx_client) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.debug(f"Results: {results}")

        sizes = {}
        errors = []

        for url, res in results:
            if isinstance(res, Exception):
                errors.append((url, res))
            elif isinstance(res,(tuple, list)) and len(res) >= 2:
                if res[0] < settings.min_image_width or res[1] < settings.min_image_height:
                    errors.append((url, "small"))
                else:
                    sizes[url] = res  # (w, h)

        logger.info(f"Processed: Normal images: {len(sizes)}, images with errors: {len(errors)}")
        
        return {
            "sizes": sizes,   # dictionary {url: (width, height)}
            "errors": errors  # list [(url, "error")]
        }
    else:
        result = await get_image_size(urls[0], httpx_client)
        errors = []
        sizes = result[1]
        
        if result[1][0] < settings.min_image_width or result[1][1] < settings.min_image_height:
            errors.append((urls[0], "small"))
        
        return {
            "sizes": sizes,   # tuple (w,h) 
            "errors": errors  # list [(url, "error")]
        }
    


async def download_image_bytes(url: str, httpx_client: httpx.AsyncClient):
    """
    Download image content as raw bytes.

    Verifies that the response has an image Content-Type header. 
    Retries are performed with incremental backoff.

    Args:
        url (str): Image URL.
        httpx_client (httpx.AsyncClient): Asynchronous HTTP client instance.

    Returns:
        tuple: (image_bytes, None) if successful, (None, error_message/Exception) if failed.
    """
    
    for attempt in range(3):
        try:
            resp = await httpx_client.get(url, timeout=40.0)

            if resp.status_code == 200:
                # Проверяем, что это картинка
                ctype = resp.headers.get("Content-Type", "")
                if not ctype.startswith("image/"):
                    logger.warning(f"URL did not return image: {url}, Content-Type: {ctype}")
                    return None, f"URL did not return image: {url}, Content-Type: {ctype}"

                return resp.content, None

        except Exception as e:
            if attempt == 2:  # последняя попытка
                logger.error(f"Error downloading image {url}: {e}")
                return None, e
            await asyncio.sleep(0.5 * (attempt + 1))
            continue

        # Если статус != 200
        if attempt == 2:  # последняя попытка
            logger.error(f"Failed to download image {url}: {resp.status_code} - {resp.text}")
            return None, f"HTTP {resp.status_code}: {resp.text}"
        await asyncio.sleep(0.5 * (attempt + 1))

    return None, "Unexpected error in download image bytes"  # на всякий случай



def resize_image_bytes(img_bytes: bytes):
    """
    Resize an image to meet minimum width/height requirements.

    The function scales the image proportionally based on configured minimum 
    dimensions. Images with transparency are saved as PNG, otherwise JPEG.

    Args:
        img_bytes (bytes): Raw image bytes.

    Returns:
        tuple: (resized_image_bytes, extension) on success, (None, error_message) on failure.
    """
    
    try:
        with Image.open(io.BytesIO(img_bytes)) as im:
            w, h = im.size
            if w == 0 or h == 0:
                logger.error("Invalid image dimensions")
                return None, "Invalid image dimensions"

            # Scaling
            scale_h = settings.min_image_height / h
            scale_w = settings.min_image_width / w
            scale = max(scale_h, scale_w)

            new_w = int(round(w * scale))
            new_h = int(round(h * scale))

            im = im.resize((new_w, new_h), Image.LANCZOS)

            # Determine output format
            if im.mode in ("RGBA", "LA") or (
                im.mode == "P" and "transparency" in im.info
            ):
                out_format = "PNG"
                ext = "png"
            else:
                im = im.convert("RGB")  # JPEG doesn't support alpha
                out_format = "JPEG"
                ext = "jpg"

            out = io.BytesIO()
            im.save(out, format=out_format, quality=85 if out_format == "JPEG" else None)

            return out.getvalue(), ext

    except UnidentifiedImageError:
        logger.error("Provided bytes are not an image")
        return None, "Provided bytes are not an image"
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        return None, f"Error processing image: {e}"


# Helper: normalizes name from URL/basename
def normalize_basename(name: str) -> str:
    """
    Normalize a filename extracted from a URL or path.

    - Decodes percent-encoding.
    - Removes control characters.
    - Replaces slashes with underscores.
    - Compresses multiple spaces into one.

    Args:
        name (str): Original filename or path fragment.

    Returns:
        str: A safe, normalized filename.
    """
    
    # Decode percent-encoding
    name = unquote(name or "")
    # Remove control characters
    name = re.sub(r'[\x00-\x1f\x7f]+', '', name)
    # Replace slashes with underscores (to avoid path issues)
    name = name.replace('/', '_').replace('\\', '_')
    # Compress multiple spaces into one
    name = re.sub(r'\s+', ' ', name).strip()
    return name


async def upload_to_ftp(
    data: bytes,
    filename: str,
    remote_dir: str,
    ean: str,
    ftp_client: aioftp.Client,
    max_retries: int = 3,
) -> str:
    """Asynchronous FTP upload via aioftp with retry logic."""
    
    filename_only = os.path.basename(filename)
    temp_filename = filename  # temp file = исходное имя
    
    for attempt in range(max_retries):
        try:
            if remote_dir:
                try:
                    await asyncio.wait_for(
                        ftp_client.make_directory(remote_dir, parents=True),
                        timeout=30.0
                    )
                except aioftp.StatusCodeError as e:
                    # 550 - директория уже существует
                    if "550" not in str(e):
                        raise
                await asyncio.wait_for(
                    ftp_client.change_directory(remote_dir),
                    timeout=30.0
                )

            logger.debug(f"[Attempt {attempt+1}] Start of file upload: {filename_only}")

            # Сохраняем временный файл
            with open(temp_filename, "wb") as temp_file:
                temp_file.write(data)

            # Загружаем
            await asyncio.wait_for(
                ftp_client.upload(temp_filename),
                timeout=60.0
            )

            logger.debug(f"[Attempt {attempt+1}] End of file upload: {filename_only}")

            # Успех -> чистим и возвращаем URL
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)

            return f"{settings.image_base_url}/{ean}/{filename_only}"

        except Exception as e:
            logger.error(f"[Attempt {attempt+1}] FTP upload failed for {filename_only}: {e}")

            # Чистим временный файл (на случай неудачи тоже)
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)

            if attempt == max_retries - 1:
                raise Exception(f"FTP upload failed after {max_retries} attempts: {e}")

            # Ждём перед новой попыткой
            await asyncio.sleep(0.5 * (attempt + 1))


# Modified file_exists_on_ftp: tries multiple name variants
async def file_exists_on_ftp(filename: str, remote_dir: str, ean: str, ftp_client: aioftp.Client) -> bool:
    """
    Checks if file exists on FTP. Returns URL or False.
    Tries decoded name and encoded variants (for compatibility).
    """
    if remote_dir:
        try:
            await asyncio.wait_for(
                ftp_client.change_directory(remote_dir),
                timeout=30.0
                )
        except aioftp.StatusCodeError as e:
            # If directory doesn't exist, file definitely doesn't exist
            if "550" in str(e):
                return False
            raise

    # Name candidates: as passed, decoded, URL-encoded
    decoded = normalize_basename(filename)
    quoted = quote(decoded, safe='')  # fully encoded
    space_encoded = decoded.replace(' ', '%20')  # commonly encountered variant

    candidates = []
    # preserve order: original -> decoded -> space-encoded -> fully quoted
    if filename not in candidates:
        candidates.append(filename)
    if decoded not in candidates:
        candidates.append(decoded)
    if space_encoded not in candidates:
        candidates.append(space_encoded)
    if quoted not in candidates:
        candidates.append(quoted)

    for candidate in candidates:
        try:
            await asyncio.wait_for(
                ftp_client.stat(candidate),
                timeout=30.0
            )
            # Return URL with the name variant that was actually found
            return f"{settings.image_base_url}/{ean}/{candidate}"
        except aioftp.StatusCodeError as e:
            # Code 550 — file not found, try next variant
            if "550" in str(e):
                continue
            raise

    return False


async def resize_image_and_upload(
    url: str,
    ean: str,
    ftp_client: aioftp.Client,
    httpx_client: httpx.AsyncClient,
    test: Optional[bool] = False
) -> str:
    """
    Upload a file to an FTP server with retry logic.

    Creates the target directory if it does not exist, then uploads the file. 
    A temporary local file is created during the process and deleted after completion.

    Args:
        data (bytes): File content to upload.
        filename (str): Local filename to assign during upload.
        remote_dir (str): Remote directory path on the FTP server.
        ean (str): Product EAN code, used for remote path construction.
        ftp_client (aioftp.Client): Asynchronous FTP client instance.
        max_retries (int, optional): Number of retry attempts. Defaults to 3.

    Returns:
        str: URL of the uploaded file on the FTP server.

    Raises:
        Exception: If upload fails after all retry attempts.
    """
    
    # 1. Download bytes
    img_bytes, err = await download_image_bytes(url, httpx_client)
    if img_bytes is None:
        logger.error(f"Error occurred while downloading image: {url}, error: {err}")
        raise Exception(f"While downloading image: {url}, error: {err}")

    # 2. Resize
    resized_bytes, ext_or_arr = await asyncio.to_thread(resize_image_bytes, img_bytes)
    if resized_bytes is None:
        logger.error(f"Resize error: {ext_or_arr}")
        raise Exception(f"While resizing image: {url}, error: {ext_or_arr}")

    # 3. Form filename: decode basename and set correct extension
    path = urlparse(url).path
    orig_file_name = normalize_basename(path)
    # orig_file_name_with_ext = os.path.basename(path)
    # orig_file_name_with_ext = unquote(orig_file_name_with_ext)  # convert %20 -> space
    # print(orig_file_name_with_ext)
    # orig_file_name, _ = os.path.splitext(orig_file_name_with_ext)
    # print(orig_file_name)
    # orig_file_name = normalize_basename(orig_file_name)  # safe name
    # orig_file_name = f"{orig_file_name}.{ext_or_arr}"
    # print(orig_file_name)

    # 4. Check existence (file_exists_on_ftp now considers variants)
    existing_url = await file_exists_on_ftp(
        filename=orig_file_name,
        remote_dir=f"/xlmoebel.at/image/afterbuy_resized_images_for_mirakl/{ean}",
        ean=ean,
        ftp_client=ftp_client
    )
    if existing_url:
        logger.info(f"Image {orig_file_name} already exists in ftp server, returning its address")
        if test:
            return {
                "ftp_url" : existing_url,
                "sizes": await process_images([existing_url], httpx_client=httpx_client)
            }
        return existing_url

    logger.debug(f"Image {orig_file_name} does not exist in ftp server, importing there")

    # 5. FTP upload — logic unchanged, pass normalized name
    ftp_url = await upload_to_ftp(
        data=resized_bytes,
        filename=orig_file_name,
        remote_dir=f"/xlmoebel.at/image/afterbuy_resized_images_for_mirakl/{ean}",
        ean=ean,
        ftp_client=ftp_client
    )
    if test:
        return {
            "ftp_url" : ftp_url,
            "sizes": await process_images([ftp_url], httpx_client=httpx_client)
        }
    return ftp_url