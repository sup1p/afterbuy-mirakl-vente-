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
    Extracts product properties from HTML tab content.
    """
    soup = BeautifulSoup(html, "html.parser")

    tab1 = soup.find("div", {"id": "tab-content1"})
    if not tab1:
        return ""

    details = []

    # Remove empty and "nbsp" content
    paragraphs = [
        p.get_text(" ", strip=True)
        for p in tab1.find_all(["p", "font"])
        if p.get_text(strip=True) and p.get_text(strip=True) != "\xa0"
    ]

    for text in paragraphs:
        clean_text = re.sub(r"\s+", " ", text).strip()

        if ":" in clean_text:
            # Split by first colon
            key, value = clean_text.split(":", 1)
            details.append(f"{key.strip()}: {value.strip()}")
        else:
            # Add as is (e.g., "oder ca: 202 x 287 cm")
            details.append(clean_text)

    return " ".join(details)