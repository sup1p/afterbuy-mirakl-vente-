from src.core.settings import settings

def is_valid_ean(code: str) -> bool:
    """
    Проверяет, является ли EAN-код (европейский артикул) корректным.
    Возвращает False, если код некорректен, и True, если корректен.
    """
    if not code.isdigit() or len(code) not in (8, 13):
        return False

    digits = list(map(int, code))
    checksum = digits[-1]  # Последняя цифра — контрольная сумма
    body = digits[:-1]     # Остальные цифры — тело кода

    if len(code) == 13:
        # Для EAN-13: нечётные позиции ×1, чётные ×3
        total = sum(num if i % 2 == 0 else num * 3 for i, num in enumerate(body))
    else:
        # Для EAN-8: наоборот — нечётные ×3, чётные ×1
        total = sum(num * 3 if i % 2 == 0 else num for i, num in enumerate(body))

    control = (10 - (total % 10)) % 10  # Вычисляем контрольную сумму
    return control == checksum


def get_delivery_days(fabric_name: str) -> int:
    """
    Возвращает количество дней доставки для указанной ткани.
    Временно возвращает фиксированное значение 45.
    """
    return 45 # временно заглушка

def is_set(article: str) -> bool:
    """
    Проверяет, является ли статья набором (set).
    Возвращает True, если в названии статьи есть слово "set" (регистр игнорируется).
    """
    return "set" in article.casefold()

def split_images(urls: str) -> list[str]:
    """
    Разделяет строку с URL изображений на отдельные ссылки.
    Возвращает список ссылок, исключая пустые элементы.
    """
    parts = [p for p in urls.split(";") if p]
    return parts