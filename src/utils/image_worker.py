from logs.config_logs import setup_logging
from src.core.settings import settings
from src.core.dependencies import get_client

import httpx
import logging

client = get_client()
setup_logging()
logger = logging.getLogger(__name__)


async def check_image_existence(image_url: str) -> bool:
    if settings.check_image_existence is False:
        return True
    
    if not image_url:
        return False
    
        
    try:
        response = await client.head(image_url)
    except Exception as e:
        logger.error(f"Error while checking image at {image_url}: {e}")
        return False
    
    if response.status_code == 200:
        logger.debug(f"Image found at {image_url}")
        return True
    else:
        logger.warning(f"Image not found at {image_url}, status code: {response.status_code}")
        return False
    

def image_resize():
    pass