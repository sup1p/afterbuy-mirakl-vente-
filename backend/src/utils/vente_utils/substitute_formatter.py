"""
Модуль для подстановки форматтеров атрибутов.
Направляет запросы на форматирование атрибутов к соответствующим функциям на основе кодов атрибутов.
"""

from src.utils.vente_utils.format_attr import (
    format_2,
    format_3,
    format_5,
    format_7,
    format_8,
    format_17,
    format_19,
    format_32,
    format_48,
    format_56,
    format_58,
    format_61,
    format_68,
    format_73,
    format_82,
    format_106,
    format_163,
    format_175,
    format_183,
    format_259,
    format_267,
    format_287,
    format_391,
    format_433,
    format_435,
    format_557,
    format_585,
    format_693,
    format_717,
    format_723,
    format_741,
    format_745,
    format_747,
    format_767,
    format_769,
    format_779,
    format_795,
    format_805,
    format_875,
    format_927,
    format_928,
    format_150_151_152,
)
from logs.config_logs import setup_logging 

import logging

setup_logging()
logger = logging.getLogger(__name__)

def substitute_attr(attr_code, filled_attrs, value):
    """
    Подставляет значение атрибута, используя соответствующую функцию форматирования.

    Аргументы:
        attr_code: Код атрибута (например, "ATTR_2").
        filled_attrs: Словарь, куда записываются отформатированные значения.
        value: Исходное значение атрибута.
    """
    match attr_code:
        case "ATTR_2":
            logger.debug(f"Совпадение для кода: {attr_code}")
            filled_attrs[attr_code] = format_2(value)

        case "ATTR_3":
            logger.debug(f"Совпадение для кода: {attr_code}")
            filled_attrs[attr_code] = format_3(value)

        case "ATTR_5":
            logger.debug(f"Совпадение для кода: {attr_code}")
            filled_attrs[attr_code] = format_5(value)

        case "ATTR_7":
            logger.debug(f"Совпадение для кода: {attr_code}")
            filled_attrs[attr_code] = format_7(value)

        case "ATTR_8":
            logger.debug(f"Совпадение для кода: {attr_code}")
            filled_attrs[attr_code] = format_8(value)

        case "ATTR_17":
            logger.debug(f"Совпадение для кода: {attr_code}")
            filled_attrs[attr_code] = format_17(value)

        case "ATTR_19":
            logger.debug(f"Совпадение для кода: {attr_code}")
            filled_attrs[attr_code] = format_19(value)

        case "ATTR_32":
            logger.debug(f"Совпадение для кода: {attr_code}")
            filled_attrs[attr_code] = format_32(value)

        case "ATTR_48":
            logger.debug(f"Совпадение для кода: {attr_code}")
            filled_attrs[attr_code] = format_48(value)

        case "ATTR_56":
            logger.debug(f"Совпадение для кода: {attr_code}")
            filled_attrs[attr_code] = format_56(value)

        case "ATTR_58":
            logger.debug(f"Совпадение для кода: {attr_code}")
            filled_attrs[attr_code] = format_58(value)
            
        case "ATTR_61":
            logger.debug(f"Совпадение для кода: {attr_code}")
            filled_attrs[attr_code] = format_61(value)

        case "ATTR_68":
            logger.debug(f"Совпадение для кода: {attr_code}")
            filled_attrs[attr_code] = format_68(value)

        case "ATTR_73":
            logger.debug(f"Совпадение для кода: {attr_code}")
            filled_attrs[attr_code] = format_73(value)

        case "ATTR_82":
            logger.debug(f"Совпадение для кода: {attr_code}")
            filled_attrs[attr_code] = format_82(value)
            
        case "ATTR_106":
            logger.debug(f"Совпадение для кода: {attr_code}")
            filled_attrs[attr_code] = format_106(value)

        case "ATTR_163":
            logger.debug(f"Совпадение для кода: {attr_code}")
            filled_attrs[attr_code] = format_163(value)

        case "ATTR_175":
            logger.debug(f"Совпадение для кода: {attr_code}")
            filled_attrs[attr_code] = format_175(value)

        case "ATTR_183":
            logger.debug(f"Совпадение для кода: {attr_code}")
            filled_attrs[attr_code] = format_183(value)

        case "ATTR_259":
            logger.debug(f"Совпадение для кода: {attr_code}")
            filled_attrs[attr_code] = format_259(value)

        case "ATTR_267":
            logger.debug(f"Совпадение для кода: {attr_code}")
            filled_attrs[attr_code] = format_267(value)

        case "ATTR_287":
            logger.debug(f"Совпадение для кода: {attr_code}")
            filled_attrs[attr_code] = format_287(value)

        case "ATTR_391":
            logger.debug(f"Совпадение для кода: {attr_code}")
            filled_attrs[attr_code] = format_391(value)

        case "ATTR_433":
            logger.debug(f"Совпадение для кода: {attr_code}")
            filled_attrs[attr_code] = format_433(value)

        case "ATTR_435":
            logger.debug(f"Совпадение для кода: {attr_code}")
            filled_attrs[attr_code] = format_435(value)
            
        case "ATTR_557":
            logger.debug(f"Совпадение для кода: {attr_code}")
            filled_attrs[attr_code] = format_557(value)

        case "ATTR_585":
            logger.debug(f"Совпадение для кода: {attr_code}")
            filled_attrs[attr_code] = format_585(value)
            
        case "ATTR_693":
            logger.debug(f"Совпадение для кода: {attr_code}")
            filled_attrs[attr_code] = format_693(value)  # Прямое присвоение без форматирования

        case "ATTR_717":
            logger.debug(f"Совпадение для кода: {attr_code}")
            filled_attrs[attr_code] = format_717(value)

        case "ATTR_723":
            logger.debug(f"Совпадение для кода: {attr_code}")
            filled_attrs[attr_code] = format_723(value)

        case "ATTR_741":
            logger.debug(f"Совпадение для кода: {attr_code}")
            filled_attrs[attr_code] = format_741(value)
            
        case "ATTR_745":
            logger.debug(f"Совпадение для кода: {attr_code}")
            filled_attrs[attr_code] = format_745(value)

        case "ATTR_747":
            logger.debug(f"Совпадение для кода: {attr_code}")
            filled_attrs[attr_code] = format_747(value)

        case "ATTR_767":
            logger.debug(f"Совпадение для кода: {attr_code}")
            filled_attrs[attr_code] = format_767(value)

        case "ATTR_769":
            logger.debug(f"Совпадение для кода: {attr_code}")
            filled_attrs[attr_code] = format_769(value)
            
        case "ATTR_779":
            logger.debug(f"Совпадение для кода: {attr_code}")
            filled_attrs[attr_code] = format_779(value)

        case "ATTR_795":
            logger.debug(f"Совпадение для кода: {attr_code}")
            filled_attrs[attr_code] = format_795(value)

        case "ATTR_805":
            logger.debug(f"Совпадение для кода: {attr_code}")
            filled_attrs[attr_code] = format_805(value)

        case "ATTR_875":
            logger.debug(f"Совпадение для кода: {attr_code}")
            filled_attrs[attr_code] = format_875(value)

        case "ATTR_927":
            logger.debug(f"Совпадение для кода: {attr_code}")
            filled_attrs[attr_code] = format_927(value)

        case "ATTR_928":
            logger.debug(f"Совпадение для кода: {attr_code}")
            filled_attrs[attr_code] = format_928(value)

        case "ATTR_150" | "ATTR_151" | "ATTR_152":
            logger.debug(f"Совпадение для кода: {attr_code}")
            mapping = {
                "ATTR_150": 0,
                "ATTR_151": 2,
                "ATTR_152": 1,
            }
            index = mapping.get(attr_code, 1)
            filled_attrs[attr_code] = format_150_151_152(value, index)

        case _:
            logger.warning(f"Неизвестный код атрибута: {attr_code}")
            filled_attrs[attr_code] = None

    return filled_attrs
