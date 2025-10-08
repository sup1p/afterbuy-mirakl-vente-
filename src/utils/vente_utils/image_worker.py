"""
Image processing utilities module.
Handles image validation, resizing, and FTP upload operations.
"""

from logs.config_logs import setup_logging
from src.core.settings import settings

import io
import os
import re
import struct
from urllib.parse import unquote, quote, urlparse
from PIL import Image, UnidentifiedImageError
from typing import Tuple, Union, Optional

import httpx
import logging
import asyncio
import aioftp

setup_logging()
logger = logging.getLogger(__name__)

SMALL_HEADER = 256
MAX_BYTES_DEFAULT = 2_000_000
RETRY_ATTEMPTS = 3
RETRY_BACKOFF = 0.5
TIMEOUT = 10.0  # секунд для stream

BYTES_BY_FORMAT = {
    "png": 1024,
    "gif": 1024,
    "bmp": 1024,
    "webp": 16 * 1024,
    "jpg": 64 * 1024,
    "jpeg": 64 * 1024,
    "tiff": 256 * 1024,
    "default": MAX_BYTES_DEFAULT,
}

# Simple circuit breaker для часто ломающихся URL
# В продакшене это должно быть в Redis или базе данных
_failed_urls = {}  # {url: {"count": int, "last_failure": timestamp}}
_CIRCUIT_BREAKER_THRESHOLD = 3  # Максимум ошибок перед блокировкой
_CIRCUIT_BREAKER_TIMEOUT = 300  # 5 минут блокировки


def _is_url_circuit_broken(url: str) -> bool:
    """Проверить, заблокирован ли URL из-за частых ошибок."""
    import time
    
    if url not in _failed_urls:
        return False
    
    failure_info = _failed_urls[url]
    
    # Если прошло достаточно времени, сбрасываем счетчик
    if time.time() - failure_info["last_failure"] > _CIRCUIT_BREAKER_TIMEOUT:
        del _failed_urls[url]
        return False
    
    # Проверяем превышен ли лимит ошибок
    return failure_info["count"] >= _CIRCUIT_BREAKER_THRESHOLD


def _record_url_failure(url: str):
    """Записать ошибку для URL."""
    import time
    
    current_time = time.time()
    if url in _failed_urls:
        _failed_urls[url]["count"] += 1
        _failed_urls[url]["last_failure"] = current_time
    else:
        _failed_urls[url] = {"count": 1, "last_failure": current_time}
    
    if _failed_urls[url]["count"] >= _CIRCUIT_BREAKER_THRESHOLD:
        logger.warning(f"Circuit breaker activated for URL (too many failures): {url}")


def _record_url_success(url: str):
    """Записать успех для URL - сбрасывает счетчик ошибок."""
    if url in _failed_urls:
        del _failed_urls[url]

MIME_MAP = {
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
    "gif": "image/gif",
    "bmp": "image/bmp",
    "tiff": "image/tiff",
}


async def check_image_existence(image_url: str, httpx_client: httpx.AsyncClient, retries: int = 2, timeout: int = 5) -> bool:
    """
    Verify whether an image is accessible at the given URL.

    Improved version with:
    - Global timeout protection (max 20 seconds total)
    - Reduced retries for faster failure
    - Fast-fail on certain error types
    - Circuit breaker for frequently failing URLs
    - Better logging for troubleshooting

    Args:
        image_url (str): The URL of the image.
        httpx_client (httpx.AsyncClient): Asynchronous HTTP client instance.
        retries (int, optional): Number of retry attempts. Defaults to 2.
        timeout (int, optional): Timeout per request in seconds. Defaults to 5.

    Returns:
        bool: True if the image is accessible (HTTP 200), False otherwise.
    """
    if not image_url or not isinstance(image_url, str):
        return False
    
    # Check circuit breaker
    if _is_url_circuit_broken(image_url):
        logger.debug(f"Circuit breaker: skipping frequently failing URL: {image_url}")
        return False
    
    # Quick URL validation
    if not image_url.lower().startswith(('http://', 'https://')) or len(image_url) > 2000:
        logger.debug(f"Invalid URL format: {image_url[:100]}...")
        return False

    # Global timeout for entire operation
    total_timeout = min(20.0, timeout * retries * 2)
    
    try:
        result = await asyncio.wait_for(
            _check_image_existence_internal(image_url, httpx_client, retries, timeout),
            timeout=total_timeout
        )
        
        # Record success/failure for circuit breaker
        if result:
            _record_url_success(image_url)
        else:
            _record_url_failure(image_url)
            
        return result
        
    except asyncio.TimeoutError:
        logger.warning(f"Total timeout ({total_timeout}s) exceeded for image existence check: {image_url}")
        _record_url_failure(image_url)
        return False
    except Exception as e:
        logger.warning(f"Unexpected error checking image existence: {e}")
        _record_url_failure(image_url)
        return False


async def _check_image_existence_internal(image_url: str, httpx_client: httpx.AsyncClient, retries: int, timeout: int) -> bool:
    """Internal implementation without global timeout wrapper."""
    
    for attempt in range(1, retries + 1):
        try:
            # Try HEAD first (faster)
            response = await httpx_client.head(image_url, timeout=float(timeout))
            if response.status_code == 200:
                return True
            elif response.status_code in (403, 405):  
                # HEAD не поддерживается, пробуем GET
                response = await httpx_client.get(image_url, timeout=float(timeout))
                return response.status_code == 200
            elif response.status_code in (404, 410):
                # Definitely doesn't exist, no point retrying
                logger.debug(f"Image not found (HTTP {response.status_code}): {image_url}")
                return False
            else:
                logger.debug(f"Attempt {attempt}/{retries} failed for {image_url}: HTTP {response.status_code}")
        except Exception as e:
            error_str = str(e).lower()
            logger.debug(f"Attempt {attempt}/{retries} failed for {image_url}: {str(e)[:100]}")
            
            # Fast-fail on certain network errors
            if any(keyword in error_str for keyword in ['name resolution failed', 'connection refused', 'ssl error']):
                logger.debug(f"Fast-failing on network error: {e}")
                return False
        
        # Retry logic - только если это не последняя попытка
        if attempt < retries:
            # Reduced backoff delay
            delay = min(2 ** attempt, 4)  # Максимум 4 секунды
            await asyncio.sleep(delay)

    logger.debug(f"Image not accessible at {image_url} after {retries} attempts")
    return False
    



def _detect_format_from_magic(data: bytes) -> Optional[str]:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if data.startswith(b"\xFF\xD8"):
        return "jpeg"
    if data.startswith(b"BM"):
        return "bmp"
    if data[0:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    # TIFF: II*\x00 or MM\x00*
    if data.startswith(b"II*\x00") or data.startswith(b"MM\x00*"):
        return "tiff"
    return None

def _parse_png_size(data: bytes) -> Optional[Tuple[int,int]]:
    # IHDR chunk at fixed offset: bytes 8..24 contain IHDR
    try:
        if len(data) < 24:
            return None
        # IHDR chunk type at offset 12..16
        if data[12:16] != b'IHDR':
            return None
        width, height = struct.unpack(">II", data[16:24])
        return width, height
    except Exception:
        return None

def _parse_gif_size(data: bytes) -> Optional[Tuple[int,int]]:
    try:
        if len(data) < 10:
            return None
        w, h = struct.unpack("<HH", data[6:10])
        return w, h
    except Exception:
        return None

def _parse_bmp_size(data: bytes) -> Optional[Tuple[int,int]]:
    try:
        if len(data) < 26:
            return None
        # BITMAPINFOHEADER starts at offset 14, width/height at 18 and 22 (little endian)
        width, height = struct.unpack("<ii", data[18:26])
        return abs(width), abs(height)
    except Exception:
        return None

def _parse_webp_size(data: bytes) -> Optional[Tuple[int,int]]:
    try:
        # minimal checks for VP8/VP8L/VP8X variants
        if len(data) < 30:
            return None
        # VP8X: at offset 12 chunk "VP8X", then canvas size at 24..30 (3 bytes each little-endian)
        if data[12:16] == b'VP8X' and len(data) >= 30:
            # canvas size stored as 3 bytes minus 1
            cw = int.from_bytes(data[24:27], 'little') + 1
            ch = int.from_bytes(data[27:30], 'little') + 1
            return cw, ch
        # VP8 (lossy): chunk "VP8 " contains frame header starting a bit later; parse width/height from frame (needs more bytes)
        # For reliability, fallback to Pillow if not VP8X
        return None
    except Exception:
        return None

def _parse_jpeg_size(data: bytes) -> Optional[Tuple[int,int]]:
    # Scan markers for SOF0/1/2... as per JPEG spec.
    # Need variable amount of data; return None if not enough bytes.
    try:
        if not data.startswith(b'\xFF\xD8'):
            return None
        idx = 2
        L = len(data)
        while idx + 4 <= L:
            # find next 0xFF marker
            if data[idx] != 0xFF:
                # skip until next 0xFF
                idx += 1
                continue
            # marker byte
            marker = data[idx + 1]
            idx += 2
            # markers without length (e.g. 0xD0..0xD9) have no length field
            if marker == 0xDA:  # Start of Scan: image data starts — size likely not found
                break
            if 0xD0 <= marker <= 0xD9:
                continue
            if idx + 2 > L:
                return None
            seg_len = struct.unpack(">H", data[idx:idx+2])[0]
            if seg_len < 2:
                return None
            # Check SOF markers
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                # segment payload starts after len bytes
                if idx + 2 + 5 > L:
                    return None
                # precision = data[idx+2]; height = next two; width = next two
                # But segment length includes these, so safe to read if present
                height = struct.unpack(">H", data[idx+3:idx+5])[0]
                width = struct.unpack(">H", data[idx+5:idx+7])[0]
                return width, height
            # skip segment
            idx += seg_len
        return None
    except Exception:
        return None

async def _fetch_prefix(httpx_client: httpx.AsyncClient, url: str, n_bytes: int, timeout: float):
    """
    Fetch image bytes with global timeout protection and better error handling.
    """
    # Добавляем глобальный таймаут на всю операцию (в 2 раза больше локального)
    global_timeout = max(timeout * 2, 30.0)
    
    try:
        # Оборачиваем всю операцию в asyncio.wait_for для принудительного таймаута
        return await asyncio.wait_for(
            _fetch_prefix_internal(httpx_client, url, n_bytes, timeout),
            timeout=global_timeout
        )
    except asyncio.TimeoutError:
        logger.warning(f"Global timeout ({global_timeout}s) exceeded for URL: {url}")
        raise Exception(f"Global timeout exceeded: {global_timeout}s")
    except Exception as e:
        logger.warning(f"Failed to fetch prefix from {url}: {e}")
        raise


async def _fetch_prefix_internal(httpx_client: httpx.AsyncClient, url: str, n_bytes: int, timeout: float):
    """Internal fetch implementation without global timeout wrapper."""
    # Защита от чрезмерно больших запросов
    if n_bytes > 10 * 1024 * 1024:  # 10MB max
        logger.warning(f"Requested too many bytes ({n_bytes}) for URL: {url}")
        raise Exception(f"Requested bytes too large: {n_bytes}")
    
    headers = {"Range": f"bytes=0-{max(0, n_bytes-1)}"}
    
    try:
        async with httpx_client.stream("GET", url, headers=headers, timeout=timeout) as resp:
            if resp.status_code not in (200, 206):
                logger.debug(f"Bad status code {resp.status_code} for URL: {url}")
                resp.raise_for_status()
            
            buf = bytearray()
            chunk_count = 0
            max_chunks = 1000  # Защита от бесконечного цикла
            
            async for chunk in resp.aiter_bytes():
                chunk_count += 1
                if chunk_count > max_chunks:
                    logger.warning(f"Too many chunks ({chunk_count}) for URL: {url}")
                    break
                    
                if not chunk:
                    break
                    
                buf.extend(chunk)
                if len(buf) >= n_bytes:
                    break
                    
            # Принудительно закрываем соединение
            await resp.aclose()
            
            if len(buf) == 0:
                raise Exception("No data received")
                
            return bytes(buf)
            
    except httpx.ReadTimeout:
        raise Exception(f"Read timeout after {timeout}s")
    except httpx.ConnectTimeout:
        raise Exception(f"Connection timeout after {timeout}s")
    except httpx.HTTPStatusError as e:
        raise Exception(f"HTTP error {e.response.status_code}")
    except Exception as e:
        # Логируем и пробрасываем дальше
        raise Exception(f"Network error: {str(e)}")

async def get_image_size(url: str, httpx_client: httpx.AsyncClient) -> Tuple[str, Union[Tuple[int,int], Exception]]:
    """
    Optimized: tries to download minimal bytes and parse header for dimensions.
    Returns (url, (w,h)) or (url, Exception)
    
    Improved with:
    - Global timeout protection (max 60 seconds total)
    - Fast-fail for obviously bad URLs
    - Reduced retry attempts for faster failure
    - Circuit breaker for frequently failing URLs
    """
    # Quick validation
    if not url or not isinstance(url, str):
        return url, Exception("Invalid URL")
    
    # Check circuit breaker
    if _is_url_circuit_broken(url):
        logger.debug(f"Circuit breaker: skipping frequently failing URL: {url}")
        return url, Exception("Circuit breaker: URL frequently fails")
    
    # Check for obviously problematic URLs
    if len(url) > 2000:  # URLs longer than 2000 chars are suspicious
        return url, Exception("URL too long")
    
    # Protocol check
    if not url.lower().startswith(('http://', 'https://')):
        return url, Exception("Invalid protocol")
    
    # Global timeout for entire operation
    total_timeout = 60.0
    
    try:
        # Wrap entire operation in global timeout
        result = await asyncio.wait_for(
            _get_image_size_internal(url, httpx_client),
            timeout=total_timeout
        )
        
        # Record success if we got a valid size
        if isinstance(result, tuple) and len(result) == 2:
            _, size_or_error = result
            if isinstance(size_or_error, (tuple, list)) and len(size_or_error) >= 2:
                _record_url_success(url)
        
        return result
        
    except asyncio.TimeoutError:
        logger.warning(f"Total timeout ({total_timeout}s) exceeded for image size check: {url}")
        _record_url_failure(url)
        return url, Exception(f"Total timeout exceeded: {total_timeout}s")
    except Exception as e:
        _record_url_failure(url)
        return url, e


async def _get_image_size_internal(url: str, httpx_client: httpx.AsyncClient) -> Tuple[str, Union[Tuple[int,int], Exception]]:
    """Internal implementation without global timeout wrapper."""
    
    # Try to guess format from URL extension first
    ext_match = re.search(r"\.([a-zA-Z0-9]{1,5})(?:[?#]|$)", url)
    ext = ext_match.group(1).lower() if ext_match else None

    # pick initial size
    def bytes_for_fmt(fmt: Optional[str]) -> int:
        if fmt and fmt in BYTES_BY_FORMAT:
            return BYTES_BY_FORMAT[fmt]
        return SMALL_HEADER

    # Reduced retry attempts for faster failure on bad URLs
    max_retries = 2  # Было RETRY_ATTEMPTS (обычно 3-5)
    last_exc: Optional[Exception] = None
    
    for attempt in range(max_retries):
        try:
            # Step 1: small probe if extension unknown
            if ext is None:
                probe = await _fetch_prefix(httpx_client, url, SMALL_HEADER, TIMEOUT)
                fmt = _detect_format_from_magic(probe)
                # decide how many bytes we actually need
                need = BYTES_BY_FORMAT.get(fmt, BYTES_BY_FORMAT["default"])
                # if probe already contains enough bytes, use it; else fetch more
                if len(probe) >= need:
                    data = probe[:need]
                else:
                    # fetch full needed bytes in a ranged request
                    data = await _fetch_prefix(httpx_client, url, need, TIMEOUT)
            else:
                # extension known: request corresponding bytes directly
                need = bytes_for_fmt(ext)
                data = await _fetch_prefix(httpx_client, url, need, TIMEOUT)
                fmt = _detect_format_from_magic(data) or ext

            # Try fast parsers
            size = None
            if fmt == "png":
                size = _parse_png_size(data)
            elif fmt == "gif":
                size = _parse_gif_size(data)
            elif fmt in ("jpg", "jpeg", "jpeg2000", "jpe", "jfif") or (fmt is None and data.startswith(b'\xFF\xD8')):
                size = _parse_jpeg_size(data)
            elif fmt == "bmp":
                size = _parse_bmp_size(data)
            elif fmt == "webp":
                size = _parse_webp_size(data)
            elif fmt == "tiff":
                # TIFF parsing is complex; let Pillow try
                size = None

            # If fast parse succeeded:
            if size:
                return url, size

            # If not enough bytes detected — try to progressively increase for JPEG/webp/tiff
            # attempt doubling up to default max
            wanted = BYTES_BY_FORMAT.get(fmt, BYTES_BY_FORMAT["default"])
            if len(data) < wanted and wanted <= MAX_BYTES_DEFAULT:
                # fetch full wanted
                data = await _fetch_prefix(httpx_client, url, wanted, TIMEOUT)
                # retry parsers
                if fmt == "png":
                    size = _parse_png_size(data)
                elif fmt == "gif":
                    size = _parse_gif_size(data)
                elif fmt in ("jpg", "jpeg") or data.startswith(b'\xFF\xD8'):
                    size = _parse_jpeg_size(data)
                elif fmt == "bmp":
                    size = _parse_bmp_size(data)
                elif fmt == "webp":
                    size = _parse_webp_size(data)

                if size:
                    return url, size

            # Last fallback: try Pillow on what we have (Pillow may require more bytes; if so, it will error)
            try:
                img = Image.open(io.BytesIO(data))
                img.verify()  # light verify
                # reopen to get size (verify may close file)
                img = Image.open(io.BytesIO(data))
                return url, img.size
            except Exception:
                # if Pillow failed and we haven't yet tried large download, try larger fetch up to default max
                if len(data) < MAX_BYTES_DEFAULT:
                    data_full = await _fetch_prefix(httpx_client, url, MAX_BYTES_DEFAULT, TIMEOUT)
                    try:
                        img = Image.open(io.BytesIO(data_full))
                        img.verify()
                        img = Image.open(io.BytesIO(data_full))
                        return url, img.size
                    except Exception as e:
                        last_exc = e
                        raise e
                else:
                    raise

        except Exception as e:
            last_exc = e
            logger.debug(f"Attempt {attempt + 1}/{max_retries} failed for {url}: {str(e)[:100]}")
            
            # Быстрое завершение для определенных типов ошибок
            error_str = str(e).lower()
            if any(keyword in error_str for keyword in ['timeout', 'connection refused', 'name resolution failed', 'ssl error']):
                logger.warning(f"Fast-failing on network error for {url}: {e}")
                return url, e
            
            # retry/backoff только если не последняя попытка
            if attempt == max_retries - 1:
                return url, e
            
            # Уменьшенная задержка для более быстрого завершения
            backoff_delay = min(2.0 * (attempt + 1), 5.0)  # Максимум 5 секунд задержки
            await asyncio.sleep(backoff_delay)
            continue

    return url, last_exc or Exception("All attempts failed")
            

async def process_images(urls: list[str], httpx_client: httpx.AsyncClient):
    """
    Validate multiple images asynchronously and check their dimensions.

    Improved version with:
    - Global timeout protection (max 120 seconds total)
    - Limited parallelism to prevent resource exhaustion
    - Fast-fail on too many URLs
    - Better error tracking

    Args:
        urls (list[str]): List of image URLs to process.
        httpx_client (httpx.AsyncClient): Asynchronous HTTP client instance.

    Returns:
        dict: Dictionary containing:
            - sizes (dict): Mapping {url: (width, height)} for valid images.
            - errors (list): List of (url, error) tuples for invalid or small images.
    """
    if not urls:
        return {"sizes": {}, "errors": []}
    
    # Защита от слишком большого количества изображений
    if len(urls) > 50:
        logger.warning(f"Too many URLs to process ({len(urls)}), limiting to first 50")
        urls = urls[:50]
    
    # Global timeout for entire batch processing
    total_timeout = min(120.0, len(urls) * 10.0)  # 10 seconds per URL max
    
    try:
        return await asyncio.wait_for(
            _process_images_internal(urls, httpx_client),
            timeout=total_timeout
        )
    except asyncio.TimeoutError:
        logger.error(f"Batch image processing timeout ({total_timeout}s) for {len(urls)} URLs")
        # Return all URLs as errors
        return {
            "sizes": {},
            "errors": [(url, "batch_timeout") for url in urls]
        }
    except Exception as e:
        logger.error(f"Unexpected error in batch image processing: {e}")
        return {
            "sizes": {},
            "errors": [(url, f"batch_error: {e}") for url in urls]
        }


async def _process_images_internal(urls: list[str], httpx_client: httpx.AsyncClient):
    """Internal implementation without global timeout wrapper."""
    
    if len(urls) > 1:
        # Ограничиваем параллелизм для предотвращения перегрузки сервера
        semaphore = asyncio.Semaphore(min(5, len(urls)))  # Максимум 5 одновременных запросов
        
        async def bounded_get_image_size(url):
            async with semaphore:
                return await get_image_size(url, httpx_client)
        
        tasks = [bounded_get_image_size(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.debug(f"Batch processing results for {len(urls)} URLs")

        sizes = {}
        errors = []

        for i, result in enumerate(results):
            url = urls[i]
            
            if isinstance(result, Exception):
                logger.debug(f"Error processing {url}: {result}")
                errors.append((url, result))
            elif isinstance(result, tuple) and len(result) == 2:
                # result is (url, (w,h) or Exception)
                actual_url, size_or_error = result
                if isinstance(size_or_error, Exception):
                    errors.append((actual_url, size_or_error))
                elif isinstance(size_or_error, (tuple, list)) and len(size_or_error) >= 2:
                    w, h = size_or_error[0], size_or_error[1]
                    if w < settings.min_image_width or h < settings.min_image_height:
                        errors.append((actual_url, f"too_small_{w}x{h}"))
                    else:
                        sizes[actual_url] = (w, h)
                else:
                    errors.append((actual_url, f"invalid_size_format: {size_or_error}"))
            else:
                errors.append((url, f"unexpected_result_format: {result}"))

        logger.info(f"Batch processed: {len(sizes)} valid images, {len(errors)} errors")
        
        return {
            "sizes": sizes,   # dictionary {url: (width, height)}
            "errors": errors  # list [(url, "error")]
        }
    else:
        # Single URL processing
        url = urls[0]
        result = await get_image_size(url, httpx_client)
        errors = []
        sizes = {}
        
        # result is (url, (w,h) or Exception)
        if isinstance(result, tuple) and len(result) == 2:
            actual_url, size_or_error = result
            if isinstance(size_or_error, Exception):
                errors.append((actual_url, size_or_error))
            elif isinstance(size_or_error, (tuple, list)) and len(size_or_error) >= 2:
                w, h = size_or_error[0], size_or_error[1]
                if w < settings.min_image_width or h < settings.min_image_height:
                    errors.append((actual_url, f"too_small_{w}x{h}"))
                else:
                    sizes[actual_url] = (w, h)
            else:
                errors.append((actual_url, f"invalid_size_format: {size_or_error}"))
        else:
            errors.append((url, f"unexpected_result_format: {result}"))
        
        return {
            "sizes": sizes,   # dictionary {url: (width, height)}
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
    removed: bool = False
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

            if removed:
                return f"{settings.image_base_url}/removed_bg/{ean}/{filename_only}"
                
            return f"{settings.image_base_url}/resized/{ean}/{filename_only}"

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
async def file_exists_on_ftp(
    filename: str,
    remote_dir: str, 
    ean: str, 
    ftp_client: aioftp.Client,
    removed: bool = False
) -> bool:
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
            if removed:
                return f"{settings.image_base_url}/removed_bg/{ean}/{candidate}"
            
            return f"{settings.image_base_url}/resized/{ean}/{candidate}"
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
    
    # 1. Form filename: decode basename and set correct extension
    path = urlparse(url).path
    orig_file_name = normalize_basename(path)
    
    # 2. Check existence (file_exists_on_ftp now considers variants)
    existing_url = await file_exists_on_ftp(
        filename=orig_file_name,
        remote_dir=f"{settings.ftp_base_dir}/resized/{ean}",
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

    # 3. Download bytes
    img_bytes, err = await download_image_bytes(url, httpx_client)
    if img_bytes is None:
        logger.error(f"Error occurred while downloading image: {url}, error: {err}")
        raise Exception(f"While downloading image: {url}, error: {err}")

    # 4. Resize
    resized_bytes, ext_or_arr = resize_image_bytes(img_bytes)
    if resized_bytes is None:
        logger.error(f"Resize error: {ext_or_arr}")
        raise Exception(f"While resizing image: {url}, error: {ext_or_arr}")
    
    logger.debug(f"Image {orig_file_name} does not exist in ftp server, importing there")

    # 5. FTP upload — logic unchanged, pass normalized name
    ftp_url = await upload_to_ftp(
        data=resized_bytes,
        filename=orig_file_name,
        remote_dir=f"{settings.ftp_base_dir}/resized/{ean}",
        ean=ean,
        ftp_client=ftp_client
    )
    if test:
        return {
            "ftp_url" : ftp_url,
            "sizes": await process_images([ftp_url], httpx_client=httpx_client)
        }
    return ftp_url


async def remove_image_bg_and_upload(
    url: str,
    ean: str,
    ftp_client: aioftp.Client,
    httpx_client: httpx.AsyncClient
) -> str:
    
    # 1. Form filename: decode basename and set correct extension
    path = urlparse(url).path
    orig_file_name = normalize_basename(path)
    
    # 2. Check existence (file_exists_on_ftp now considers variants)
    existing_url = await file_exists_on_ftp(
        filename=orig_file_name,
        remote_dir=f"{settings.ftp_base_dir}/removed_bg/{ean}",
        ean=ean,
        ftp_client=ftp_client,
        removed=True
    )
    
    if existing_url:
        logger.info(f"Image {orig_file_name} already exists in ftp server remove bg, returning its address")
        return existing_url

    # 3. Download bytes
    img_bytes, err = await download_image_bytes(url, httpx_client)
    if img_bytes is None:
        logger.error(f"Error occurred while downloading image for remove bg: {url}, error: {err}")
        raise Exception(f"While downloading image for remove bg: {url}, error: {err}")

    # 4. Remove bg
    removed_bg_bytes, ext_or_arr = await remove_img_bg(img_bytes=img_bytes, httpx_client=httpx_client)
    if removed_bg_bytes is None:
        logger.error(f"Remove bg error: {ext_or_arr}")
        raise Exception(f"While removing image bg: {url}, error: {ext_or_arr}")
    
    logger.debug(f"Image {orig_file_name} does not exist in ftp server remove bg, importing there")

    # 5. FTP upload — logic unchanged, pass normalized name
    ftp_url = await upload_to_ftp(
        data=removed_bg_bytes,
        filename=orig_file_name,
        remote_dir=f"{settings.ftp_base_dir}/removed_bg/{ean}",
        ean=ean,
        ftp_client=ftp_client,
        removed=True
    )
    return ftp_url


async def remove_img_bg(img_bytes: bytes, httpx_client: httpx.AsyncClient) -> tuple[bytes | None, str | None]:
    """
    Отправляет байты изображения на сервис удаления фона и возвращает:
    - (processed_bytes, None) при успехе
    - (None, error_message) при ошибке
    """
    try:
        # определяем формат через Pillow
        try:
            with Image.open(io.BytesIO(img_bytes)) as im:
                fmt = im.format
                fmt = fmt.lower() if fmt else None
        except Exception:
            fmt = None

        mime = MIME_MAP.get(fmt, "application/octet-stream")
        filename = f"image.{fmt if fmt else 'bin'}"

        headers = {"x-api-key": settings.remove_bg_api_key}
        files = {"image_file": (filename, img_bytes, mime)}

        resp = await httpx_client.post(settings.remove_bg_url, headers=headers, files=files, timeout=30.0)

        if resp.status_code != 200:
            logger.error("remove-bg service returned %s: %s", resp.status_code, resp.text)
            return None, f"remove-bg error: {resp.status_code} - {resp.text}"

        return resp.content, None

    except httpx.RequestError as exc:
        logger.exception("HTTP request error while calling remove-bg service")
        return None, f"request error: {exc}"
    except Exception as exc:
        logger.exception("Unexpected error in remove_img_bytes")
        return None, str(exc)