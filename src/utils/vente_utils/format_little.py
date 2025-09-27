from src.core.settings import settings

def is_valid_ean(code: str) -> bool:
    """
    Checks if the EAN is valid or invalid
    Returns false if incorrect and True if correct
    """
    
    if not settings.use_ean_validator:
        return True
    
    if not code.isdigit() or len(code) not in (8, 13):
        return False

    digits = list(map(int, code))
    checksum = digits[-1]
    body = digits[:-1]

    if len(code) == 13:
        # EAN-13: нечётные позиции ×1, чётные ×3
        total = sum(num if i % 2 == 0 else num * 3 for i, num in enumerate(body))
    else:
        # EAN-8: наоборот — нечётные ×3, чётные ×1
        total = sum(num * 3 if i % 2 == 0 else num for i, num in enumerate(body))

    control = (10 - (total % 10)) % 10
    return control == checksum


def get_delivery_days(fabric_name: str) -> int:
    return 45 # временно заглуша