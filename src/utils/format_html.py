from bs4 import BeautifulSoup

from logs.config_logs import setup_logging
import logging

setup_logging()
logger = logging.getLogger(__name__)


def extract_product_description(html: str) -> str:
    logger.debug(f"Extracting product description from HTML of length {len(html) if html else 0}")
    """
    Извлекает текстовое описание из блока 'Produktbeschreibung'.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Находим заголовок "Produktbeschreibung"
    heading = soup.find("div", class_="panel-heading", string="Produktbeschreibung")
    if not heading:
        return ""

    # Блок с описанием сразу после заголовка
    description_block = heading.find_next("div", class_="text-section")
    if not description_block:
        return ""

    # Убираем теги <img>, пустые параграфы и пробелы
    for tag in description_block.find_all(["img", "script", "style"]):
        tag.decompose()

    text = description_block.get_text(separator=" ", strip=True)
    return " ".join(text.split())