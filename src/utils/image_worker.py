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
    

async def get_image_size(url: str, httpx_client: httpx.AsyncClient):
    """
    Retrieves image dimensions by downloading first 20KB of the image.
    """
    try:
        headers = {"Range": "bytes=0-200000"}  # Read first 20KB
        resp = await httpx_client.get(url, headers=headers, timeout=10)
        resp.raise_for_status()

        try:
            img = Image.open(io.BytesIO(resp.content))
            logger.info(f"Image {url[:50]} sizes: {img.size}")
            return url, img.size
        except Exception as e:
            logger.warning(f"Image {url[:50]} error: {e}")
            return url, f"Pillow error: {e}"
        
    except Exception as e:
        logger.warning(f"Image {url[:50]} error: {e}")
        return url, e  # Return error along with url
    

async def process_images(urls: list[str], httpx_client: httpx.AsyncClient):
    """
    Asynchronously checks image dimensions for compliance with requirements using gather.
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
            elif res[0] < settings.min_image_width or res[1] < settings.min_image_height:
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
    try:
        resp = await httpx_client.get(url, timeout=30)
        resp.raise_for_status()

        # Check content type header
        ctype = resp.headers.get("Content-Type", "")
        if not ctype.startswith("image/"):
            logger.warning(f"URL did not return image: {url}, Content-Type: {ctype}")
            return None, f"URL did not return image: {url}, Content-Type: {ctype}"

        return resp.content, None
    except Exception as e:
        logger.error(f"Error downloading image {url}: {e}")
        return None, e



def resize_image_bytes(img_bytes: bytes):
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
    # Decode percent-encoding
    name = unquote(name or "")
    # Remove control characters
    name = re.sub(r'[\x00-\x1f\x7f]+', '', name)
    # Replace slashes with underscores (to avoid path issues)
    name = name.replace('/', '_').replace('\\', '_')
    # Compress multiple spaces into one
    name = re.sub(r'\s+', ' ', name).strip()
    return name


async def upload_to_ftp(data: bytes, filename: str, remote_dir: str, ean: str,ftp_client: aioftp.Client) -> str:
    """Asynchronous FTP upload via aioftp."""
    if remote_dir:
        try:
            await ftp_client.make_directory(remote_dir, parents=True)
        except aioftp.StatusCodeError as e:
            if "550" not in str(e):
                raise
        await ftp_client.change_directory(remote_dir)

    logger.debug(f"Start of file upload: {filename}")

    temp_filename = filename
    filename = os.path.basename(filename)
    current_dir = await ftp_client.get_current_directory()
    
    try:
        # Write data to temporary file
        with open(temp_filename, 'wb') as temp_file:
            temp_file.write(data)
        
        # Upload file - aioftp will see only filename without slashes
        await ftp_client.upload(temp_filename)
    finally:
        # Remove temporary file
        if os.path.exists(temp_filename):
            os.unlink(temp_filename)
    
    logger.debug("End of file upload")
    
    
    return f"{settings.image_base_url}/{ean}/{filename}"


# Modified file_exists_on_ftp: tries multiple name variants
async def file_exists_on_ftp(filename: str, remote_dir: str, ean: str, ftp_client: aioftp.Client) -> bool:
    """
    Checks if file exists on FTP. Returns URL or False.
    Tries decoded name and encoded variants (for compatibility).
    """
    if remote_dir:
        try:
            await ftp_client.change_directory(remote_dir)
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
            await ftp_client.stat(candidate)
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
    httpx_client: httpx.AsyncClient
) -> str:
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
    orig_file_name_with_ext = os.path.basename(path)
    orig_file_name_with_ext = unquote(orig_file_name_with_ext)  # convert %20 -> space
    orig_file_name, _ = os.path.splitext(orig_file_name_with_ext)
    orig_file_name = normalize_basename(orig_file_name)  # safe name
    orig_file_name = f"{orig_file_name}.{ext_or_arr}"

    # 4. Check existence (file_exists_on_ftp now considers variants)
    existing_url = await file_exists_on_ftp(
        filename=orig_file_name,
        remote_dir=f"/xlmoebel.at/image/afterbuy_resized_images_for_mirakl/{ean}",
        ean=ean,
        ftp_client=ftp_client
    )
    if existing_url:
        logger.info(f"Image {orig_file_name} already exists in ftp server, returning its address")
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

    return ftp_url