"""
HTML processing utilities module.
Extracts product descriptions and properties from HTML content.
"""

from bs4 import BeautifulSoup

from logs.config_logs import setup_logging
import logging
import re

setup_logging()
logger = logging.getLogger(__name__)


def extract_product_description_from_html(html: str) -> str:
    """
    Extracts text description from 'Produktbeschreibung' block.
    """
    logger.debug(f"Extracting product description from HTML of length {len(html) if html else 0}")
    
    soup = BeautifulSoup(html, "html.parser")

    # Find "Produktbeschreibung" heading
    heading = soup.find("div", class_="panel-heading", string="Produktbeschreibung")
    if not heading:
        return ""

    # Description block immediately after heading
    description_block = heading.find_next("div", class_="text-section")
    if not description_block:
        return ""

    # Remove <img>, <script>, <style> tags and clean up whitespace
    for tag in description_block.find_all(["img", "script", "style"]):
        tag.decompose()

    text = description_block.get_text(separator=" ", strip=True)
    return " ".join(text.split())


def extract_product_properties_from_html(html: str) -> str:
    """
    Extracts product properties from HTML tab content and returns them as a single string.
    Example output:
    "Höhe: 2066 mm Tiefe: 626 mm Breite: 1300 mm Farbe: Farbwahl Material: Holzwerkstoff Lieferzustand: Zerlegt"
    """
    clean_html = re.sub(r"^<!\[CDATA\[|\]\]>$", "", html.strip())
    soup = BeautifulSoup(clean_html, "html.parser")
    tab1 = soup.find("div", {"id": "tab-content1"})
    if not tab1:
        logger.warning("No tab1-content found in html")
        return ""

    details = []

    # Разбиваем по <br/> внутри абзацев
    for p in tab1.find_all("p"):
        parts = p.decode_contents().split("<br/>")
        for part in parts:
            clean_text = BeautifulSoup(part, "html.parser").get_text(" ", strip=True)
            if not clean_text or clean_text == "\xa0":
                continue
            clean_text = re.sub(r"\s+", " ", clean_text).strip()
            details.append(clean_text)

    # Соединяем в одну строку

    logger.info(f"Product extracted from html properties: {details}")
    return " ".join(details)