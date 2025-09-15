from bs4 import BeautifulSoup

from logs.config_logs import setup_logging
import logging
import re

setup_logging()
logger = logging.getLogger(__name__)


def extract_product_description_from_html(html: str) -> str:
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


def extract_product_properties_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    tab1 = soup.find("div", {"id": "tab-content1"})
    if not tab1:
        return ""

    details = []

    # Убираем пустые и "nbsp"
    paragraphs = [
        p.get_text(" ", strip=True)
        for p in tab1.find_all(["p", "font"])
        if p.get_text(strip=True) and p.get_text(strip=True) != "\xa0"
    ]

    for text in paragraphs:
        clean_text = re.sub(r"\s+", " ", text).strip()

        if ":" in clean_text:
            # Разбиваем по первому двоеточию
            key, value = clean_text.split(":", 1)
            details.append(f"{key.strip()}: {value.strip()}")
        else:
            # Добавляем как есть (например "oder ca: 202 x 287 cm")
            details.append(clean_text)

    return " ".join(details)