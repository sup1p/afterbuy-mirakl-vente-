"""
Модуль для обработки HTML.
Извлекает описания и свойства продуктов из HTML-контента.
"""

from bs4 import BeautifulSoup

from logs.config_logs import setup_logging
import logging
import re

setup_logging()
logger = logging.getLogger(__name__)


def extract_product_description_from_html(html: str) -> str:
    """
    Извлекает текстовое описание из блока 'Produktbeschreibung'.
    Если блок или описание отсутствуют, возвращает пустую строку.
    """
    logger.debug(f"Извлечение описания продукта из HTML длиной {len(html) if html else 0}")

    soup = BeautifulSoup(html, "html.parser")

    # Ищем заголовок "Produktbeschreibung"
    heading = soup.find("div", class_="panel-heading", string="Produktbeschreibung")
    if not heading:
        return ""

    # Блок описания сразу после заголовка
    description_block = heading.find_next("div", class_="text-section")
    if not description_block:
        return ""

    # Удаляем теги <img>, <script>, <style> и очищаем пробелы
    for tag in description_block.find_all(["img", "script", "style"]):
        tag.decompose()

    text = description_block.get_text(separator=" ", strip=True)
    return " ".join(text.split())


def extract_product_properties_from_html(html: str) -> str:
    """
    Извлекает свойства продукта из содержимого вкладки HTML и возвращает их в виде строки.
    Пример вывода:
    "Höhe: 2066 mm Tiefe: 626 mm Breite: 1300 mm Farbe: Farbwahl Material: Holzwerkstoff Lieferzustand: Zerlegt"
    """
    clean_html = re.sub(r"^<!\[CDATA\[|\]\]>$", "", html.strip())
    soup = BeautifulSoup(clean_html, "html.parser")
    tab1 = soup.find("div", {"id": "tab-content1"})
    if not tab1:
        logger.warning("Содержимое tab1 не найдено в HTML")
        return ""

    details = []

    # Разбиваем содержимое по тегу <br/> внутри абзацев
    for p in tab1.find_all("p"):
        parts = p.decode_contents().split("<br/>")
        for part in parts:
            clean_text = BeautifulSoup(part, "html.parser").get_text(" ", strip=True)
            if not clean_text or clean_text == "\xa0":
                continue
            clean_text = re.sub(r"\s+", " ", clean_text).strip()
            details.append(clean_text)

    # Логируем извлеченные свойства
    logger.info(f"Свойства продукта, извлеченные из HTML: {details}")
    return "\n".join(details)