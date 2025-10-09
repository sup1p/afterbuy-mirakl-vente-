"""
CSV conversion utilities module.
Converts JSON data structures to CSV format for Mirakl API integration.
"""

import io
import csv
import logging
from logs.config_logs import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

def make_csv(data: dict):
    """
    Преобразует JSON-объект или список JSON-объектов в строку CSV.

    Функция принимает либо один словарь, либо список словарей,
    динамически определяет имена полей (для поддержки гетерогенных структур)
    и записывает данные в строку CSV в памяти.

    Аргументы:
        data (dict | list[dict]): Входные JSON-данные.

    Возвращает:
        str: CSV-представление данных в виде строки. Возвращает пустую строку, если входные данные недействительны.

    Исключения:
        Не выбрасывает исключений явно, но логирует ошибку, если встречаются объекты, не являющиеся словарями.
    """
    
    # Проверяем, что данные не пустые
    if not data:
        logger.warning("make_csv получил пустые данные")
        return ""

    output = io.StringIO()

    # Определяем, является ли входной объект списком словарей
    rows = data if isinstance(data, list) else [data]

    # Собираем все ключи (для поддержки гетерогенных словарей)
    fieldnames = set()
    for row in rows:
        if isinstance(row, dict):
            fieldnames.update(row.keys())
        else:
            logger.error(f"Ожидался словарь, но получен: {type(row)} → {row}")
            return ""

    fieldnames = list(fieldnames)

    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()

    for row in rows:
        writer.writerow(row)

    # Получаем id/ean из первой строки (если доступно)
    first = rows[0]
    logger.info(
        f"Преобразовано в CSV с product-id: {first.get('product-id')}, ean: {first.get('ean')}"
    )

    return output.getvalue()


def make_big_csv(data):
    """
    Преобразует список JSON-объектов в строку CSV.

    В отличие от `make_csv`, эта функция принимает только список словарей.
    Она собирает все ключи из списка для поддержки гетерогенных структур данных
    и записывает данные в строку CSV в памяти.

    Аргументы:
        data (list[dict]): Список JSON-объектов.

    Возвращает:
        str: CSV-представление данных в виде строки. Возвращает пустую строку, если входные данные недействительны.

    Исключения:
        Не выбрасывает исключений явно, но логирует ошибку, если встречаются объекты, не являющиеся словарями.
    """
    # Проверяем, что данные не пустые и являются списком
    if not data or not isinstance(data, list):
        logger.error("make_big_csv получил пустые или недействительные данные")
        return ""

    output = io.StringIO()

    # Собираем все ключи (для поддержки гетерогенных словарей)
    fieldnames = set()
    for row in data:
        if isinstance(row, dict):
            fieldnames.update(row.keys())
        else:
            logger.error(f"Ожидался словарь, но получен: {type(row)} → {row}")
            return ""

    fieldnames = list(fieldnames)

    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()

    for row in data:
        writer.writerow(row)

    # Логируем список EAN из данных
    eans = [row.get("ean") for row in data if row.get("ean")]
    logger.info(
        f"Преобразован большой CSV с eans: {eans}"
    )

    return output.getvalue()
