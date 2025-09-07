import io
import csv
import logging
from logs.config_logs import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

def make_csv(data):
    """Конвертирует JSON (dict | list[dict]) → CSV (строка в памяти)."""
    if not data:  # пустое значение
        logger.warning("make_csv получил пустые данные")
        return ""

    output = io.StringIO()

    # Определяем список словарей
    rows = data if isinstance(data, list) else [data]

    # Собираем все ключи (на случай разнородных словарей)
    fieldnames = set()
    for row in rows:
        if isinstance(row, dict):
            fieldnames.update(row.keys())
        else:
            logger.error(f"Ожидался dict, а пришло: {type(row)} → {row}")
            return ""

    fieldnames = list(fieldnames)

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for row in rows:
        writer.writerow(row)

    # Берём id/ean из первой строки (если есть)
    first = rows[0]
    logger.info(
        f"Converted to CSV with product-id: {first.get('product-id')}, ean: {first.get('ean')}"
    )

    return output.getvalue()


def make_big_csv(data):
    """Конвертирует список JSON-объектов → CSV (строка в памяти)."""
    if not data or not isinstance(data, list):
        logger.error("make_big_csv получил пустые или некорректные данные")
        return ""

    output = io.StringIO()

    # Собираем все ключи (на случай разнородных словарей)
    fieldnames = set()
    for row in data:
        if isinstance(row, dict):
            fieldnames.update(row.keys())
        else:
            logger.error(f"Ожидался dict, а пришло: {type(row)} → {row}")
            return ""

    fieldnames = list(fieldnames)

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for row in data:
        writer.writerow(row)
        
    
    eans = [row.get("ean") for row in data if row.get("ean")]
    logger.info(
        f"Converted big CSV with eans: {eans}"
    )

    return output.getvalue()
