"""
Product attribute formatting utilities module.
Contains functions for formatting various product attributes according to Mirakl specifications.
"""

import logging
import re
import unicodedata
from typing import Union, List, Optional, Any
from src.const.attrs import ATTR_175, ATTR_2, ATTR_795, ATTR_927, ATTR_7, ATTR_106
from src.const.constants import mapping_format_85
from src.core.settings import settings
from logs.config_logs import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


class FormatterError(Exception):
    """Custom exception for formatting errors"""
    pass


def safe_execute(func_name: str, _input_value: Any):
    """Decorator for safe function execution with logging"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            real_input_value = args[0] if args else kwargs.get('input_value', _input_value)
            try:
                logger.debug(f"Executing {func_name} with input: {real_input_value}")
                result = func(*args, **kwargs)
                if result is None:
                    logger.warning(f"{func_name}: No matching result found for input '{real_input_value}'")
                else:
                    logger.info(f"{func_name}: Successfully mapped {real_input_value} -> '{result}'")
                return result
            except Exception as e:
                logger.error(f"{func_name}: Error processing '{real_input_value}': {str(e)}")
                return None
        return wrapper
    return decorator

def validate_input(input_value: Any, expected_type: type = None) -> bool:
    """Validates input data"""
    if input_value is None:
        logger.warning("Input value is None")
        return False
    
    if expected_type and not isinstance(input_value, expected_type):
        logger.warning(f"Expected type {expected_type.__name__}, got {type(input_value).__name__}")
        return False
    
    if isinstance(input_value, list) and len(input_value) == 0:
        logger.warning("Input list is empty")
        return False
    
    return True


def get_first_value(input_value: Union[List, Any]) -> Any:
    """Safely extracts first value from list or returns the value itself"""
    if isinstance(input_value, list) and input_value:
        return input_value[0]
    return input_value


@safe_execute("format_2", "input_value")
def format_2(input_value: List[str], locale: str = "de") -> Optional[str]:
    """Formatting for attribute 2 with localization"""
    if not validate_input(input_value, list):
        logger.warning("Invalid input for format_2, returning default value")
        return  "9"
    
    color_map = {
        "Türkis": "13089",
        "Beige-Golb": "7",
        "Weiß,Schwarz": "9",
        "Silber-Transparent": "5",
        "Matt Chrome": "5",
        "White Patina": "9",
        "Lila": "19",
        "Orange": "35",
        "White - chrome": "9",
        "Golden": "17",
        "Koralle": "118529",
        "Silber": "5",
        "Hell beige": "7",
        "Beige-Braun": "7",
        "Warmweiß": "9",
        "Kaltweiß": "9",
        "Schwarz / Braun": "33",
        "Braun-Beige": "15",
        "Transparent-Weiß": "43",
        "Weiß/Grau/Braun": "9",
        "grün": "101",
        "Purple": "19",
        "Schwarz / Grau": "33",
        "Silber Matt": "5",
        "Grau / Schwarz": "21",
        "Schwarz/Weiß": "33",
        "Violett": "19",
        "Ultraviolett": "19",
        "Beige-matt": "7",
        "Bizzotto": "5",
        "Grau - Blau": "21",
        "Silber-Matt": "5",
        "Smoke": "43",
        "Matt-Gold": "17",
        "Braun / Mehrfarbig": "15",
        "French Gold": "17",
        "Zweifarbig": "43",
        "Schwarz-Weiß": "33",
        "Braun/Grau": "15",
        "Grau-Gold": "21",
        "Grau": "21",
        "Dunkelbraun": "15",
        "Gelb": "23",
        "Azurblau": "11",
        "Braun/Weiß": "15",
        "Beige-Gold": "7",
        "Schwarz/Rot": "33",
        "Red": "39",
        "Matt": "5",
        "Black": "33",
        "Brown": "15",
        "208 cm": "5",
        "Opal Honig": "7",
        "Schwarz-Silber": "33",
        "Flieder": "61",
        "Grau / Braun": "21",
        "Beige": "7",
        "Rot": "39",
        "Blau-Weiß": "11",
        "Chrome-Black": "5",
        "Pink": "37",
        "Bordeaux": "53",
        "Gold-matt": "17",
        "Weiß-Golb": "9",
        "Rosa": "37",
        "Hellgrau": "93",
        "Transparent-Rot": "43",
        "weißen": "9",
        "Weiß,Pink,Blau": "9",
        "Weiß / Grün": "9",
        "Graue": "21",
        "Beige/ Braun": "7",
        "Transparent-Beige": "43",
        "weiß": "9",
        "Hellbraun": "15",
        "Rot-Blau": "39",
        "Braun": "15",
        "Braun / Gelb": "15",
        "Braun / Weiß": "15",
        "Hell-Braun": "15",
        "Transparent-Grün": "43",
        "Dunkelgrau": "21",
        "Beige/ Mehrfarbig": "7",
        "Burgund": "53",
        "Weiß-Gold": "9",
        "grau - blau": "21",
        "Weiß / Hellgrau": "9",
        "Gelb - Rosa": "23",
        "Champagner": "17",
        "Weiß/Grau": "9",
        "cream": "13063",
        "Amber -Transparent": "43",
        "Transparent-Amber": "43",
        "Messing": "17",
        "Weiß-Blau": "9",
        "Transparent, Gold, Weiß": "43",
        "Transparent-Schwarz": "43",
        "Braun / Grau": "15",
        "Champagner-Transparent": "43",
        "Purpur": "19",
        "Matt-Blau": "11",
        "Dunkelblau": "11",
        "Weiß-Silber": "9",
        "Schwarz-Golb": "33",
        "Taupe": "41",
        "Grün": "101",
        "Dunkellila": "19",
        "White - Gold": "9",
        "Mehrfarbig": "87",
        "Grau/Weiß": "21",
        "Oval": "5",
        "Weiß/Braun": "9",
        "Grau/Braun": "21",
        "Weiß / Grau": "9",
        "Turkis": "13089",
        "Transparent-Blau": "43",
        "Schwarz/Grau": "33",
        "Polyester": "5",
        "Weiß-Schwarz": "9",
        "Quadrat": "5",
        "Dunkelgrün": "101",
        "Chrome": "5",
        "Schwarz": "33",
        "Gold matt": "17",
        "Transparent-Gold": "43",
        "Gold-Weiß": "17",
        "Amber": "43",
        "Weiß": "9",
        "Weiß/Schwarz": "9",
        "Gold": "17",
        "Hellgrün": "51",
        "Blau": "11",
        "Transparent-Smoke": "43",
        "102 cm": "5",
        "Schwarz/Gelb": "33",
        "Transparent": "43",
        "Weiß / Schwarz": "9",
        "schwarz": "33",
        "Braun / Schwarz": "15",
        "Weiß-Transparent": "43",
        "Natürlich": "29",
        "Beige / Braun": "7",
        "Weiß / Braun": "9",
        "Creme": "13063",
        "wie abgebildet": "5",
        "Bronze": "79",
        "White": "9",
        "Weiß-Grau": "9"
    }
    
    second_mapping = {
        "Grau": "21",
        "Turkis": "13089",
        "Violett": "19",
        "Hellgrau": "93",
        "Blau": "11",
        "Bordeaux": "53",
        "Braun": "15",
        "Beige": "7",
        "Schwarz": "33",
        "Gold": "17",
        "Weiß": "9",
        "Gelb": "23",
        "Silber": "5",
        "Hell beige": "7",
        "Dunkelbraun": "15",
        "Grün": "101",
        "Orange": "35",
        "Mehrfarbig": "87",
        "Rot": "39",
        "Rosa": "37",
        "Gelb - Rosa": "23",
        "Polsterung": "5",        # в color_map нет, но у тебя "Polyester": "5" → беру как ближайшее
        "Hellbraun": "15",
        "Dunkelgrau": "21",
        "Polyester": "5",
        "Hellgrün": "51",
        "Lila": "19",
        "Burgund": "53",
        "Türkis": "13089"
    }
    
    third_mapping = {
        "Marmoriert": "21",          # сероватый/мраморный -> Gris
        "Zebramuster": "33",         # черно-белый -> Noir
        "Abstraktes Muster": "87",   # разноцветный/абстрактный -> Multicolore
        "Dreifarbig": "87",          # несколько цветов -> Multicolore
        "Modern/Zeitgenössisch": None, # это стиль, не цвет
        "Modern": None,
        "Zweifardig": "87",          # ошибка в слове, но явно -> Multicolore
        "Naturmuster": "29",         # ближе всего к Naturfarben hell
        "Zweifarbig": "87",          # два цвета -> Multicolore
        "Einfarbig": "9",            # одноцветный -> Blanc (условно, базовый цвет)
        "Damast": "87",              # узорчатый, обычно многотональный -> Multicolore
        "Fischgrätmuster": "21",     # чаще серый/нейтральный -> Gris
        "Schottenmuster": "87",      # клетчатый, многоцветный -> Multicolore
        "ca. 203 cm": None,          # это размер, не цвет
        "4067282150416": None,       # это EAN, не цвет
        "Geblümt": "87",             # цветочный -> Multicolore
        "Mehrfarbig": "87",          # явное попадание -> Multicolore
        "Gemustert": "87",           # общий узор -> Multicolore
        "Freie Farbwahl": None
    }
    if color_map.get(get_first_value(input_value)) is None:
        logger.info(f"Color '{get_first_value(input_value)}' not found in primary mapping, returning secondary mapping")
        
        if second_mapping.get(get_first_value(input_value)) is None:
            logger.info(f"Color '{get_first_value(input_value)}' not found in second mapping, returning third mapping")
            
            if third_mapping.get(get_first_value(input_value)) is None:
                logger.info(f"Color '{get_first_value(input_value)}' not found in third mapping, returning '9'")
                return "9"
            return third_mapping.get(get_first_value(input_value))
        
        return second_mapping.get(get_first_value(input_value))
    
    return color_map.get(get_first_value(input_value))



@safe_execute("format_3", "input_value")
def format_3(input_value: str) -> Optional[str]:
    """Material formatting"""
    if not validate_input(input_value):
        logger.warning("Invalid input for format_3, returning default value")
        return "107"
        
    if isinstance(input_value, list):
        input_value = get_first_value(input_value).strip()    
        
    material_mapping = {
        "Textile": "107",
        "Acrylic": "121", 
        "Glass": "133",
        "Leather": "105",
        "Solid wood": "161",
        "Metal": "163",
        "Wood-based material": "12835",
    }
    
    material_mapping_extra = {
        "Polsterung": "107",        # Fabric and velvet
        "Leder": "105",             # Leather
        "Lackleder": "105",         # Patent leather → Leather
        "Nylon": "143",              # Нет прямого маппинга
        "Stoff/Textil": "107",      # Fabric and velvet
        "Textil": "107",            # Fabric and velvet
        "Samt": "107",              # Fabric and velvet
        "Leinen": "107",            # Fabric and velvet
        "Stoff": "107",             # Fabric and velvet
        "Polsterstoff": "107",      # Fabric and velvet
        "Kunstleder": "143",        # Imitation
        "Polybaumwolle": "107",     # Fabric and velvet
        "Leinenmischung": "107",    # Fabric and velvet
        "Polyester": "107",         # Fabric and velvet
        "Holzstuhl": "161",         # Wood
        "Pointelle": "107",         # Fabric and velvet
        "100% Polyester": "107"     # Fabric and velvet
    }
    
    logger.debug(f"Available materials: {list(material_mapping.keys())}")
    if material_mapping.get(input_value) is None:
        logger.debug(f"Material '{input_value}' not found in primary mapping, returning extra mapping")
        if material_mapping_extra.get(input_value) is None:
            logger.warning(f"Material '{input_value}' not found in extra mapping, returning default '107'")
            return "107"
        return material_mapping_extra.get(input_value)
    return material_mapping.get(input_value)


@safe_execute("format_5", "input_value")
def format_5(input_value: str) -> Optional[str]:
    """Size formatting based on volume"""
    if not validate_input(input_value):
        logger.warning("Invalid input for format_5, returning default value")
        return None
    
    try:
        nums = list(map(int, re.findall(r"\d+", input_value)))
        logger.debug(f"Extracted numbers: {nums}")
        
        if len(nums) < 3:
            logger.warning(f"Insufficient dimensions found: {len(nums)} (need 3), returning default value")
            return "203"
            
        volume = nums[0] * nums[1] * nums[2]
        logger.info(f"Calculated volume: {volume}")
        
        # Size determination based on volume
        size_thresholds = [
            (381652, "Petit modèle"),
            (660409, "Moyen modèle"), 
            (1187175, "Grand modèle"),
            (2769480, "XL"),
            (float('inf'), "XXL")
        ]
        
        mapping = {
            "Petit modèle": "201",
            "Moyen modèle": "203",
            "Grand modèle": "205",
            "XL": "207",
            "XXL": "209"
        }
        
        for threshold, size in size_thresholds:
            if volume < threshold:
                logger.info(f"Volume {volume} classified as: {size}")
                if mapping.get(size):
                    return mapping.get(size)
                else:
                    logger.warning(f"No mapping found for size '{size}', returning default '203'")
                    return "203"
                
    except ValueError as e:
        logger.error(f"Error parsing dimensions: {e}, returning default value")
        return "203"


@safe_execute("format_7", "input_value")  
def format_7(input_value: str) -> Optional[str]:
    """Size formatting in feet"""
    if not validate_input(input_value):
        logger.warning("Invalid input for format_7, returning default value")
        return "213"
    
    value = get_first_value(input_value).strip()
    
        
    def find_closest_size(input_size: str, ref_sizes: list[str]) -> str:
        # Parse numbers from string and take first two
        nums_in = list(map(int, re.findall(r"\d+", input_size)))[:2]

        closest = min(
            ref_sizes,
            key=lambda ref: sum(
                (a - b) ** 2 for a, b in zip(
                    nums_in,
                    list(map(int, re.findall(r"\d+", ref)))[:2]
                )
            )
        )
        return closest

    attr_7_dict = {val["label"]: val["code"] for val in ATTR_7.attr_7[0]["values"]}
    
    attr_7_values = [key for key in attr_7_dict.keys()]
    attr_7_codes = [vals for vals in attr_7_dict.values()]
    
    closest_value = find_closest_size(value, attr_7_values)
    logger.debug(f"Closest size for '{value}' is '{closest_value}'")
    closest_code = attr_7_codes[attr_7_values.index(closest_value)]
    
    if closest_code is None:
        logger.warning(f"No code found for closest size '{closest_value}', returning default '213'")
        return "213"
    return closest_code


@safe_execute("format_8", "input_value")
def format_8(input_value: str) -> Optional[str]:
    """Firmness formatting"""
    if not validate_input(input_value):
        logger.warning("Invalid input for format_8, returning default value")
        return "313"
        
    firmness_mapping = {
        "Mittelweich": "313", 
        "Mittel": "60615"
    }   
    
    if firmness_mapping.get(get_first_value(input_value)) is None:
        logger.warning(f"Firmness '{get_first_value(input_value)}' not found in mapping, returning default '313'")
        return "313"
    return firmness_mapping.get(get_first_value(input_value))


@safe_execute("format_17", "input_value")
def format_17(input_value: List[str]) -> Optional[str]:
    """Shape formatting"""
    if not validate_input(input_value, list):
        logger.warning("Invalid input for format_17, returning default value")
        return "375"
        
    shape_mapping = {
        "78 cm": None,
        "Rechteck": "377",
        "Rund": "379", 
        "Rechteckig": "377",
        "Quadratisch": "375",
        "Oval": "381",
        "Quadrat": "375",
    }
    if shape_mapping.get(get_first_value(input_value)) is None:
        logger.warning(f"Shape '{get_first_value(input_value)}' not found in mapping, returning default '375'")
        return "375"
    
    return shape_mapping.get(get_first_value(input_value))


@safe_execute("format_19", "input_value")
def format_19(input_value: List[str]) -> Optional[str]:
    """Style formatting"""
    if not validate_input(input_value, list):
        logger.warning("Invalid input for format_19, returning default value")
        return "393"
        
    style_mapping = {
        "Klassisch": "393",                # default Modern
        "Moddern": "393",
        "Empire": "393",
        "Modern": "393",
        "Italienisch": "393",
        "Pop Art": "393",
        "Art dėko": "10073",
        "Antik": "397",                     # Vintage as closest
        "Art Deco-Stil": "10073",
        "Barock/Rokoko": "395",             # Zeitlos as neutral
        "Arts & Crafts/Mission": "395",
        "Klassish": "393",
        "Art Deco": "10073",
        "Zeitgenössisch": "395",
        "Modern/Zeitgenössisch": "393",
        "Art déco": "10073",
        "Moderne": "393",
        "Landhaus": "127332",               # Rustikal
        "Mid-Century Modern": "393",
        "Kasachisch": "393",
        "Polyester": "393",
        "Moderner Stil": "393",
        "Mitte Jahrhundert Modern": "393",
        "Retro": "393",
        "Designer": "391"
    }
    
    value = get_first_value(input_value)
    if style_mapping.get(value) is None:
        logger.warning(f"Style '{value}' not found in mapping, returning default '393'")
        return "393"
    
    return style_mapping.get(value)


@safe_execute("format_32", "input_value")
def format_32(input_value: List[str]) -> Optional[str]:
    """Boolean value formatting (Yes/No)"""
    if not validate_input(input_value, list):
        logger.warning("Invalid input for format_32, returning default value")
        return "24961"
        
    type_pose_map = {
        "Wandmontage": "24961",   # A fixer au mur (wall-mounted)
        "Vorhang": "24961",       # Also wall-mounted (if meant "wall-mounted")
        "Einbau": "24967",        # à encastrer (built-in)
        "Freistehend": "40371",   # Autoportant (freestanding)
        "Ja": "40371",               # boolean, not related to pose type
        "Nein": "24961"              # boolean, not related to pose type
    }
    
    extra_map = {
        "Boden": "24965",
        "Auf dem Boden": "24965",
        "Auf Sockel": "40371"
    }
    
    if type_pose_map.get(get_first_value(input_value)) is not None:
        logger.info(f"Type/Pose '{get_first_value(input_value)}' found in mapping")
        
        if type_pose_map.get(get_first_value(input_value)) is not None:
            return type_pose_map.get(get_first_value(input_value))
        
        logger.info(f"Type/Pose '{get_first_value(input_value)}' not found in mapping, returning '24961'")
        return "24961"
    
    if extra_map.get(get_first_value(input_value)) is not None:
        logger.info(f"Type/Pose '{get_first_value(input_value)}' found in extra mapping")
        found_map = extra_map.get(get_first_value(input_value))
        
        if found_map is not None:
            return found_map
        
        logger.info(f"Type/Pose '{get_first_value(input_value)}' not found in extra mapping, returning '24961'")
        return "24961"
    
    value = get_first_value(input_value)
    return "40371" if value == "Nein" else "50845"


@safe_execute("format_48", "input_value")
def format_48(input_value: List[str]) -> Optional[str]:
    """Форматирование специальных значений"""
    if not validate_input(input_value, list):
        logger.warning("Invalid input for format_48, returning default value")
        return "755"
        
    value = get_first_value(input_value)
    return "757" if value in ["42", "20"] else "755"


@safe_execute("format_56", "input_value")
def format_56(input_value: List[str]) -> Optional[str]:
    """Форматирование длины с диапазонами"""
    if not validate_input(input_value, list):
        logger.warning("Invalid input for format_56, returning default value")
        return "803"
        
    try:
        value = get_first_value(input_value)
        # Очистка строки от лишних символов
        cleaned_value = value.replace("ca:", "").replace("Länge:", "").replace("\\", "").strip()
        logger.debug(f"Cleaned value: '{value}' -> '{cleaned_value}'")
        
        match = re.match(r"(\d+)", cleaned_value)
        if not match:
            logger.warning(f"No numeric value found in '{cleaned_value}', returning default value")
            return "803"
            
        number = int(match.group(1))
        logger.info(f"Extracted number: {number}")
        
        # Определение диапазона
        length_ranges = [
            (60, 803),
            (80, 805), 
            (100, 807),
            (121, 809),
            (float('inf'), 811)
        ]
        
        for threshold, code in length_ranges:
            if number < threshold:
                logger.info(f"Length {number} mapped to code: {code}")
                return str(code)
                
    except (ValueError, AttributeError) as e:
        logger.error(f"Error parsing length value: {e}, returning default value")
        return "803"


@safe_execute("format_58", "input_value")
def format_58(input_value: List[str]) -> Optional[str]:
    """Форматирование Да/Нет с другими кодами"""
    if not validate_input(input_value, list):
        logger.warning("Invalid input for format_58, returning default value")
        return "823"
        
    value = get_first_value(input_value)
    return "825" if value == "Ja" else "823"

@safe_execute("format_61", "input_value")
def format_61(input_value: List[str]) -> Optional[str]:
    """Форматирование Да/Нет с другими кодами"""
    if not validate_input(input_value, list):
        logger.warning("Invalid input for format_61, returning default value")
        return "11189"
        
    value = get_first_value(input_value)
    return "833" if value == "Ja" else "831"


@safe_execute("format_68", "input_value") 
def format_68(input_value: List[str]) -> Optional[str]:
    """Форматирование инвертированного Да/Нет"""
    if not validate_input(input_value, list):
        logger.warning("Invalid input for format_68, returning default value")
        return "879"
    
    mapping = {
        "Mehr als 8": "24977",   # ближе всего "Lot de 8"
        "5": "24973",            # Lot de 5
        "3": "871",              # Lot de 3
        "4": "873",              # Lot de 4
        "9": "24979",            # Lot de 9
        "8": "24977",            # Lot de 8
        "Mehr als 6": "875",     # ближе всего "Lot de 6"
        "7": "24975",            # Lot de 7
        "4-teilig": "873",       # Lot de 4
        "1": "879",              # A l'unité
        "Einteilig": "879",      # A l'unité
        "Dreiteilig": "871",     # Lot de 3
        "11": "75445",           # Lot de 11
        "Zweiteilig": "869",     # Lot de 2
        "2": "869",              # Lot de 2
        "6": "875",              # Lot de 6
        "10": "877"              # Lot de 10
    }
    value = get_first_value(input_value)
    if mapping.get(value):
        return mapping.get(value)
    return "879"


@safe_execute("format_73", "input_value")
def format_73(input_value: List[str]) -> Optional[str]:
    """Форматирование типа освещения"""
    if not validate_input(input_value, list):
        logger.warning("Invalid input for format_73, returning default value")
        return "927"
        
    value = get_first_value(input_value)
    return "925" if value == "LED" else "927"


@safe_execute("format_82", "input_value")
def format_82(input_value: List[str]) -> Optional[str]:
    """Форматирование численных значений с обработкой 'Mehr als'"""
    if not validate_input(input_value, list):
        logger.warning("Invalid input for format_82, returning default value")
        return "977"
        
    try:
        value = get_first_value(input_value).replace("Mehr als", "").strip()
        logger.debug(f"Processed value: {value}")
        
        number_mapping = {
            "1": "977", "2": "979", "3": "981", "4": "983", "5": "985",
            "6": "987", "7": "989", "8": "991", "16": "993", "9": "9787",
            "10": "9789", "11": "9791", "12": "9793", "13": "9795",
            "14": "9797", "15": "9799",
        }
        
        if value.isdigit() and int(value) == 0:
            return "977"
            
        result = number_mapping.get(value)
        
        if result:
            logger.debug(f"Number mapping: {value} -> {result}")
            return result
        
        return "977"
        
    except AttributeError as e:
        logger.error(f"Error processing numerical value: {e}, retnurning default value")
        return "977"
    
@safe_execute("format_106", "input_value")
def format_106(input_value: List[str]) -> Optional[str]:
    """Форматирование по атрибуту 106 (Nombre total de jets).
    - Если в значении есть число → ищем ближайшее совпадение с 'jets' в справочнике attr_106.
    - Если число не найдено или пришёл текст → возвращаем дефолтное значение.
    """
    DEFAULT_CODE = "1369"  # дефолт, например "6 jets"

    if not validate_input(input_value, list):
        logger.warning("Invalid input for format_106, returning default value")
        return DEFAULT_CODE

    try:
        value = get_first_value(input_value)
        match = re.search(r"\d+", value)
        if not match:
            logger.warning(f"No number found in '{value}', returning default value")
            return DEFAULT_CODE

        number = int(match.group())
        reference = ATTR_106.attr_106[0]["values"]
        logger.debug(f"Searching nearest match for number {number} in attr_106")

        # Собираем числа из label
        candidates = []
        for val in reference:
            jets_match = re.search(r"(\d+)", val["label"])
            if jets_match:
                jets_num = int(jets_match.group(1))
                candidates.append((jets_num, val["code"]))

        if not candidates:
            logger.warning("No numeric labels in attr_106 reference, returning default")
            return DEFAULT_CODE

        # Ищем ближайшее значение
        closest_num, closest_code = min(candidates, key=lambda x: abs(x[0] - number))
        logger.info(f"Closest match for {number} jets -> {closest_num} jets (code={closest_code})")
        return closest_code

    except (ValueError, KeyError, IndexError) as e:
        logger.error(f"Error processing ATTR_106 lookup: {e}, returning default value")
        return DEFAULT_CODE

@safe_execute("format_163", "input_value")
def format_163(input_value: List[str]) -> Optional[str]:
    """Форматирование энергетического класса"""
    if not validate_input(input_value, list):
        logger.warning("Invalid input for format_163, returning default value")
        return 
        
    value = get_first_value(input_value)
    if value is None:
        logger.warning(f"Energy class '{value}' is None, returning default '6772'")
        return "6772"
    return "99899" if value == "A+++" else "6772"


@safe_execute("format_183", "input_value")
def format_183(input_value: List[str]) -> Optional[str]:
    """Форматирование типа дротиков"""
    if not validate_input(input_value, list):
        logger.warning("Invalid input for format_183, returning default value")
        return "11189"
    
    dest_mapping = {
        "Jungen, Kinder, Mädchen": "11187",   # Kind
        "Kinder": "11187",                   # Kind
        "Erwachsene": "11189",               # Adult
        "Jugendliche": "11187",              # Kind
        "Unisex Baby & Kleinkind": "25129",  # Baby
        "Damen": "11189",                    # Adult
        "Unisex Kinder": "11187",            # Kind
        "Baby": "25129",                     # Baby
        "Kinder, Jungen, Mädchen": "11187",  # Kind
        "Unisex Erwachsene": "11189",        # Adult
        "Jungen": "11187",                   # Kind
        "Mädchen": "11187",                  # Kind
        "Unisex": "11187"                    # Kind (по умолчанию отнесём к детям)
    }

        
    value = get_first_value(input_value)
    if dest_mapping.get(value) is None:
        logger.warning(f"Type '{value}' not found in mapping, returning default '11189'")
        return "11189"
    return dest_mapping.get(value)

@safe_execute("format_259", "input_value")
def format_259(input_value: List[str]):
    if not validate_input(input_value, list):
        logger.warning("Invalid input for format_259, returning default value")
        return "24117"
    
    mapping = {
        "copper": None,
        "Gelb": "24117",
        "Ultraviolett": "24113",
        "Braun": None,
        "Stecker/Kabel": None,
        "Warmweiß": "24107",
        "Weiß": "24107",
        "Rosa": "24111",
        "Kaltweiß": "24107",
        "Beige": None,
        "Blau": "24101",
        "Gold": None,
    }
    
    value = get_first_value(input_value)
    
    if mapping.get(value) is None:
        logger.warning(f"Attr_259 '{value}' not found in mapping, returning default '24107'")
        return "24107"
    
    return mapping.get(value)
    


@safe_execute("format_267", "input_value")
def format_267(input_value: List[str]) -> Optional[int]:
    """Форматирование стиля мебели"""
    if not validate_input(input_value, list):
        logger.warning("Invalid input for format_267, returning default value")
        return "24135"
        
    style_mapping = {
        "Chesterfield": "24135",
        "Polster Arm": "24135",
        "Barock/Rokoko": "24135", 
        "Art déco": "24137",
    }
    
    value = get_first_value(input_value)
    
    if style_mapping.get(value) is None:
        logger.warning(f"Furniture style '{value}' not found in mapping, returning default '24135'")
        return "24135"
    
    return style_mapping.get(value)


@safe_execute("format_287", "input_value")
def format_287(input_value: List[str]) -> Optional[int]:
    """Форматирование особенностей мебели"""
    if not validate_input(input_value, list):
        logger.warning("Invalid input for format_287, returning default value")
        return "24249"
        
    feature_mapping = {
        "Mit Schiebe-/Schwebetüren": "24249",  # Sliding doors
        "LED": "24243",  # No option
        "Mit Schubfächern": '24249',  # With drawers
        "Mit Knöpfen": '24243',  # With buttons
        "Verstellbare Rückenlehne": '114476',  # Adjustable backrest
        "elektr. Zähler": '24243',  # Electric counter
        "Mit Regal": '24243',  # With shelf
        "Münzbehälter": '24243',  # Coin container
        "Mit Armlehnen": '114476',  # With armrests
        "Mit Kissen": '114476',  # With pillows
        "Verstellbare Kopfstütze": '114476',  # Adjustable headrest
        "mit Spiegel": '114013',  # With mirror
        "Ausziehbar": '24249',  # Extendable
        "Glas-Regalböden": '24243',  # Glass shelves
        "Mit Beleuchtung": '24243',  # With lighting
        "Münzprüfer": '24243',  # Coin validator
        "Mit Schubladen": '24249',  # With drawers
        "Mit Sideboard": '24243',  # With sideboard
        "Ohne Armlehne": '24243',  # Without armrest
        "Mit Glastüren": '24243',  # With glass doors
        "LED beleuchtet": '24243',  # LED illuminated
        "Mit Schrank": '24243',  # With cabinet
        "Mit Spiegel": '114013',  # With mirror
        "Chesterfield": '114476',  # Chesterfield style
        "Mit Kleiderstange": '24243',  # With clothes rail
        "LED-Streifen": '24243',  # LED strips
        "Hocker inklusive": '103829',  # Stool included
        "Mit Regalen": '24243',  # With shelves
    }
    
    value = get_first_value(input_value)
    
    if feature_mapping.get(value) is None:
        logger.warning(f"Furniture feature '{value}' not found in mapping, returning default '24249'")
        return "24249"
    return feature_mapping.get(value)


@safe_execute("format_391", "input_value")
def format_391(input_value: List[str]) -> Optional[str]:
    """Форматирование оригинальности"""
    if not validate_input(input_value, list):
        logger.warning("Invalid input for format_319, returning default value")
        return "29239"
        
    value = get_first_value(input_value)
    return "29237" if value == "Original" else "29239"


@safe_execute("format_433", "input_value") 
def format_433(input_value: List[str]) -> Optional[str]:
    """Форматирование количества частей"""
    if not validate_input(input_value, list):
        logger.warning("Invalid input for format_433, returning default value")
        return "39801"
        
    try:
        value = get_first_value(input_value)
        
        if value == "Einteilig":
            return "39785"
            
        # Попытка преобразовать в число
        try:
            num_value = int(value)
            if num_value > 10:
                return "39801"
        except ValueError:
            logger.warning(f"Could not convert '{value}' to integer, returning default value")
            return "39801"
        
        parts_mapping = {
            "1": "39783", "2": "39785", "3": "39787", "4": "39789", "5": "39791",
            "6": "39793", "7": "39795", "8": "39797", "9": "39799", "10": "39801",
        }
        
        return parts_mapping.get(value)
        
    except Exception as e:
        logger.error(f"Error processing parts count: {e}, returning default value")
        return "39801"


@safe_execute("format_435", "input_value")
def format_435(input_value: List[str]) -> str:
    """Форматирование гарантии (всегда возвращает 1 год)"""
    logger.info("Returning default warranty value")
    return "39919"  # 1 year


@safe_execute("format_557", "input_value")
def format_557(input_value: List[str]) -> Optional[str]:
    """Форматирование наличия опции"""
    if not validate_input(input_value, list):
        logger.warning("Invalid input for format_557, returning default value")
        return "40187"
        
    value = get_first_value(input_value)
    has_option = "ohne" not in value.lower()
    result = "40185" if has_option else "40187"
    logger.debug(f"Option check: '{value}' -> has_option: {has_option} -> {result}")
    return result


@safe_execute("format_585", "input_value")
def format_585(input_value: List[str]) -> Optional[str]:
    """Форматирование с использованием внешнего маппинга"""
    if not validate_input(input_value, list):
        logger.warning("Invalid input for format_585, returning default value")
        return 41687
        
    try:
        value = get_first_value(input_value)
        match = re.search(r"\d+", value)
        if not match:
            logger.warning(f"No number found in '{value}', returning default value")
            return 41687
            
        number = int(match.group())
        result = mapping_format_85.get(number)
        logger.debug(f"External mapping: {number} -> {result}")
        return result
        
    except ValueError as e:
        logger.error(f"Error extracting number from '{value}': {e}, returning default value")
        return 41687
    
@safe_execute("format_693", "input_value")
def format_693(input_value: List[str]) -> Optional[str]:
    """Форматирование типа мебели"""
    if not validate_input(input_value, list):
        logger.warning("Invalid input for format_693, returning default value")
        return "73335"
        
    mapping = {
        "Schuhregal": "73331",
        "Schuhschrank": "73333"
    }

        
    value = get_first_value(input_value)
    if mapping.get(value) is None:
        logger.info(f"Type mebel(ATTR_693) '{value}' not found in mapping, returning '73335'")
        return "73335"
    return mapping.get(value)


@safe_execute("format_717", "input_value")
def format_717(input_value: List[str]) -> Optional[str]:
    """Форматирование паттерна/узора"""
    if not validate_input(input_value, list):
        logger.warning("Invalid input for format_717, returning default value")
        return "76295"
        
    pattern_mapping = {
        "Modern/Zeitgenössisch": "76291",  # Contemporary
        "Gemustert": "111067",  # Patterned
        "Zweifarbig": "76283",  # Two-colored
        "Mehrfarbig": "111059",  # Multi-colored
        "Einfarbig": "76295",  # Solid color
        "Damast": "111071",  # Damask
    }
    
    motif_mapping = {
        "Weiß/Grau/Braun": "111059",  # Patchwork/Mehrfarbig
        "Quadrat": "76281",  # Carreau/Karo
        "208 cm": "76293",  # Sonstiges (не мотив, не цвет)
        "Bizzotto": "76293",
        "Oval": "76293",  # форма, не мотив
        "Polyester": "76293",
        "Transparent, Gold, Weiß": "111059",  # Patchwork/Mehrfarbig
        "Braun / Mehrfarbig": "111059",  # Patchwork
        "Mehrfarbig": "111059",
        "wie abgebildet": "111059",
        "Beige/ Mehrfarbig": "111059",
        "102 cm": "76293",
        "Weiß,Pink,Blau": "111059",
        "Zweifarbig": "111059",
        "Schwarz": "76295",
    }
    
    if pattern_mapping.get(get_first_value(input_value)) is None:
        logger.info(f"Pattern '{get_first_value(input_value)}' not found in primary mapping, returning motif mapping")
        
        if motif_mapping.get(get_first_value(input_value)) is None:
            logger.info(f"Pattern '{get_first_value(input_value)}' not found in motif mapping, returning '76295'")
            return "76295"
        return motif_mapping.get(get_first_value(input_value))
    
    value = get_first_value(input_value)
    return pattern_mapping.get(value)


@safe_execute("format_723", "input_value")
def format_723(input_value: List[str]) -> Optional[str]:
    """Форматирование типа подключения"""
    if not validate_input(input_value, list):
        logger.warning("Invalid input for format_723, returning default value")
        return "77047"
        
    value = get_first_value(input_value)
    return "77049" if value == "Stecker/Kabel" else "77047"


@safe_execute("format_741", "input_value")
def format_741(input_value: Any) -> str:
    """Форматирование с фиксированным значением"""
    logger.warning("Returning default fixed value for format_741")
    return "82913"

safe_execute("format_745", "input_value")
def format_745(input_value: List[str]):
    if not validate_input(input_value, list):
        logger.warning("Invalid input for format_745, returning default value")
        return "89827"
    
    mapping = {
        "Metall": None,
        "Glass, Painted": None,
        "Optional": None,
        "Matt/Edelstahl": "89827",  # Mat (Matt)
        "Holz Effeck": "105209",    # Woodgrain (Holzeffekt)
        "Stainless": None,
        "Gebürstet": "89803",       # Brossé (Brushed)
        "Lacquer": "89837",         # Laqué (Lacquered)
        "Chrome": "89805",          # Chromé (Chrome-plated)
        "Matt gebürstet": "89803",  # близко к Brushed + Matt
        "Walnuss hell": "103827",   # Placage noyer (Walnut veneer) – ближайшее
        "Walnut Dark": "103827",    # то же, т.к. только Walnut veneer
        "Verchromt": "89805",       # Chromé
        "Glas": None,
        "Lacquered": "89837",
        "Halbglanz": "89847",       # Brillant (Glossy)
        "Doppelbett": None,
        "Mate": "89827",            # Mat
        "Laminated": "89845",       # Stratifié
        "Gebeizt": None,
        "Glossy + Painted": "89847",  # Glossy → Brillant
        "Nein": None,
        "Natural": None,
        "Stainless Platinum": None,
        "Walnuss": "103827",        # Walnut veneer
        "Gewachst": None,
        "Vergoldet": None,
        "Semi-Gloss": "89847",      # Glossy близко
        "Finished": None,
        "Holz-Effekt": "105209",    # Woodgrain
        "Leather Fiber": "114884",  # Effet cuir
        "Wandpaneel": None,
        "Bemalt": None,
        "Glänzend": "89847",        # Brillant
        "Gold": None,
        "Lackiert": "89837",        # Laqué
        "Wandpaneelen": None,
        "Stone": None,
        "Maple": None,
        "4067282875029": None,
        "Oiled": "89793",           # Huilé
        "Oak": "103825",            # Placage chêne
        "Gelackt": "89837",         # Laqué (Lackiert)
        "Marble": "114011",         # Effet marbre
        "Hochglanz": "89847",       # Brillant
        "Polished": "89811",        # Poli
        "Holzeffekt": "105209",     # Woodgrain
        "Furnier": "103825",        # Oak veneer ближайшее
        "Oil-Rubbed": "89793",      # Oiled ближайшее
        "Schiefer": None,
        "Antikes Gold": None,
        "Holz- Effect": "105209",   # Woodgrain
        "Wood Effect": "105209",    # Woodgrain
        "Lack": "89837",            # Laqué
        "Laminiert": "89845",       # Stratifié
        "High Glossy": "89847",     # Brillant
        "Laminate": "89845",
        "Eiche": "103825",          # Oak veneer
        "Glitzer": None,
        "Gloss": "89847",
        "veneered & painted": "103825",  # Oak veneer ближайшее
        "Stainless Steel": None,
        "Oak Light": "103825",      # Oak veneer
        "Polished Chrome": "89805", # Chromé
        "Smooth": "89839",          # Lisse
        "Gold-Finish": None,
        "Antique Bronze": None,
        "Dark Walnut": "103827",    # Walnut veneer
        "Oak Dark": "103825",
        "Glossy": "89847",
        "Eierschale": None,
        "Textured": "89835",        # Texturé
        "Anthrazit": None,
        "Mahogany": None,
        "L": None,
        "Antik": "89849",           # Vieilli (Aged)
        "Hochglanzpoliert": "89811",# Polished
        "Brushed": "89803",
        "Edelstahl": None,
        "Metallisch": None,
        "Chrom": "89805",           # Chromé
        "Ja": None,
        "Natürlich": None,
        "Unpainted": "89851",       # Sans finition
        "Glatt": "89839",           # Lisse
        "Solid Wood": None,
        "Poliert": "89811",         # Poli
        "Metallic": "126580",       # Gun métal ближайшее
        "Veneer": "103825",         # Oak veneer
        "Walnut": "103827",
        "Bereift": None,
        "Halbmatt": "89827",        # Mat
        "Farbwechselnd": None,
        "Glass": None,
        "Polsterbett": None,
        "Painted": None,
        "Matte": "89827",
        "Matt": "89827",
        "Lasiert": None,
    }
    
    value = get_first_value(input_value)
    
    if not mapping.get(value):
        logger.warning(f"ATTR_745 '{get_first_value(input_value)}' not found in primary mapping, returning default mapping")
        return "89827"
    
    return mapping.get(value)



@safe_execute("format_747", "input_value")
def format_747(input_value: List[str]) -> Optional[int]:
    """Форматирование материала (расширенная версия)"""
    if not validate_input(input_value, list):
        logger.warning("Invalid input for format_747, returning default value")
        return "89969"
        
    material_mapping = {
        "Textil": "89861",          # Tissu - Polyester / Stoff - Polyester
        "Glas": "89947",            # Verre / Glas
        "Timber": "89967",          # Bois, panneau - Bois / Holz, Platte - Holz
        "Massivholz": "89967",      # тоже Bois, panneau - Bois
        "Harz": "89965",            # Résine / Harz
        "Edelstahl": "89907",       # Métal - Acier inoxydable / Metall - Edelstahl
        "Hartzinn": "89941",           # Нет точного соответствия (приближённо Metall - Zinn, но отсутствует)
        "Holzwerkstoff": "89971",   # Bois, panneau - Panneau et dérivés de bois / Holzplatte und Holzderivate
        "Metall": "89969",          # Métal / Metall
        "Kunstleder": "89963",      # Simili / Kunstleder
        "Anderer Stoff": "89861",      # Нет прямого, можно fallback к Textil
        "Holzfurnier": "89971",     # ДСП/фанера ближе к Holzwerkstoff
        "Holz": "89967"             # Bois, panneau - Bois / Holz
    }
    
    value = get_first_value(input_value)
    
    if material_mapping.get(value) is None:
        logger.info(f"Material '{value}' not found in primary mapping, returning extra mapping")
        material_mapping_extra = {
            "Textil": "89873",   # Stoff - Baumwolle (или "89861" если Textile → Polyester)
            "Massiv Holz": "89967",  # Holz, Platte - Holz
            "Holz/Textil": "89967",  # смешанный → дерево + ткань (дерево как основной)
            "Holz": "89967",
            "Holz / Textil": "89967",
            "Baumwollmischung": "89873",  # Stoff - Baumwolle
            "Holzfurnier": "89971",  # Holzplatte und Holzderivate
            "Gold": "89969",  # нет в справочнике
            "Leder mit Messing": "89959",  # Leder + Metall - Messing
            "MDF": "89971",
            "Baumwolle": "89873",
            "Holz & Metall": "89967",
            "Bronze": "89969",  # нет
            "Marmor": "89867",
            "Holz mit Textil": "89967",
            "Metall + Echt Kristall": "89969",
            "Holz & Gewebe": "89967",
            "Mangoholz": "89967",
            "Mokka gebeizte Eiche.": "89967",
            "Gummibaum": "89967",
            "Holz mit Metall": "89967",
            "MDF mit Metall": "89971",
            "Kunstleder": "89963",
            "Kristall": "89857",
            "Holz / Edelstahl / Glas": "89967",
            "Messing": "89913",
            "Acryl": "89961",
            "Metall mit Textil": "89969",
            "Marble": "89867",
            "Polyester": "89861",
            "MDF/Spanplatte - Holzoptik": "89971",
            "Kiefern": "89967",
            "Stainless": "89907",
            "Holz / Glas": "89967",
            "Textilleder": "89873",  # условно
            "Edelstahl": "89907",
            "Stoff": "89873",
            "Bambus": "89951",
            "Krustal": "89857",
            "Echt Kristall": "89857",
            "Holz mit Glas": "89967",
            "Metall mit Holz": "89969",
            "Holz und Marmor": "89967",
            "Holz / Edelstahl": "89967",
            "Holz \\ Edelstahl": "89967",
            "Zinn": "89969",
            "Edelstahl / Holz": "89907",
            "Kunststoff": "89979",
            "Samt": "89897",
            "Brass": "89913",
            "Harz": "89965",
            "45 cm": "89969",  # не материал
            "Rattan": "89855",
            "Hanf": "89937",
            "Ebenholz": "89967",
            "Latex": "89969",  # нет
            "Glass": "89947",
            "Beton": "89919",
            "Zink": "89941",
            "Glas": "89947",
            "Kiefer": "89967",
            "Metall": "89969",
            "Keramik": "89859",
            "Holz mit Marmor": "89967",
            "Leder": "89959",
            "Holz & Glas": "89967",
            "MDF/Spanplatte": "89971",
            "Holz, Textil": "89967",
            "Chrom": "89969",  # нет отдельного
            "Holz / Edelstahl / Kunststoff": "89967",
            "Aluminium": "89909",
            "Holzwerkstoff": "89971",
            "Massivholz": "89967"
        }
        if material_mapping_extra.get(value) is None:
            logger.info(f"Material '{value}' not found in extra mapping, returning third mapping")
            third_mapping = {
                "Brass": "89913",
                "Edelstahl": "89907",
                "Holz": "89967",
                "Basse": None,
                "Bass": None,
                "Glas, Holz": "89967"
            }
            if third_mapping.get(value) is None:
                logger.info(f"Material '{value}' not found in third mapping, returning '89969'")
                return "89969"
            return third_mapping.get(value)
        return material_mapping_extra.get(value)
    return material_mapping.get(value)


@safe_execute("format_767", "input_value")
def format_767(input_value: Any) -> str:
    """Форматирование с фиксированным значением"""
    logger.warning("Returning default fixed value for format_767")
    return "98723"


@safe_execute("format_769", "input_value")
def format_769(input_value: List[str]) -> Optional[int]:
    """Форматирование типа фигуры"""
    if not validate_input(input_value, list):
        logger.warning("Invalid input for format_769, returning default value")
        return "98729"
        
    figure_mapping = {
        "Standard": "98729",  # Standard decorative
        "Austarierte Figuren": "98735",  # Balanced figures
    }
    
    value = get_first_value(input_value)
    if figure_mapping.get(value) is None:
        logger.warning(f"Figure type '{value}' not found in mapping, returning default '98729'")
        return "98729"
    return figure_mapping.get(value)

@safe_execute("format_779", "input_value")
def format_779(input_value: List[str]) -> Optional[str]:
    
    mapping = {
        '1': '102309',
        '2': '102311',
        '3': '102313',
        '4': '102315',
        '5': '102317',
        '6': '102319',
        '7': '102321',
    }
    
    value_str = get_first_value(input_value)
    
    if value_str is not None and mapping.get(value_str) is not None:
        return mapping.get(get_first_value(input_value))
    elif value_str.lstrip("-").isdigit():
        value = int(value_str)
        if value >= 7:
            logger.info(f"Value '{value}' greater than or equal to 7, returning '102321'")
            return '102321'
    else:
        logger.info(f"Value '{value_str}' not found in mapping, returning '102309'")
        return '102309'


@safe_execute("format_795", "input_value")
def format_795(input_value: List[str]) -> Optional[str]:
    """Форматирование по атрибуту 795 с поиском в справочнике"""
    if not validate_input(input_value, list):
        logger.warning("Invalid input for format_795, returning default value")
        return "103505"
        
    try:
        value = get_first_value(input_value)
        match = re.search(r"\d+", value)
        if not match:
            logger.warning(f"No number found in '{value}', returning default value")
            return "103505"
            
        number = int(match.group())
        reference = ATTR_795.attr_795[0]["values"]
        logger.debug(f"Searching for number {number} in reference with {len(reference)} entries")
        
        for val in reference:
            if number == val["label"]:
                logger.info(f"Found match in ATTR_795: {number} -> {val['code']}")
                return val["code"]
                
        logger.warning(f"No match found for number {number} in ATTR_795, returning default value")
        return "103505"
        
    except (ValueError, KeyError) as e:
        logger.error(f"Error processing ATTR_795 lookup: {e}, returning default value")
        return "103505"


@safe_execute("format_805", "input_value")
def format_805(input_value: Any) -> str:
    """Форматирование с фиксированным значением"""
    logger.warning("Returning default fixed value for format_805")
    return "107321"


@safe_execute("format_875", "input_value")
def format_875(input_value: Any) -> str:
    """Форматирование с фиксированным значением"""
    logger.warning("Returning default fixed value for format_875")
    return "112838"


@safe_execute("format_927", "input_value")
def format_927(input_value: List[str]) -> Optional[str]:
    """Форматирование по атрибуту 927 с поиском в справочнике"""
    if not validate_input(input_value, list):
        logger.warning("Invalid input for format_927, returning default value")
        return "118978"
        
    try:
        value = get_first_value(input_value)
        match = re.search(r"\d+", value)
        if not match:
            logger.warning(f"No number found in '{value}', returning default value")
            return "118978"
            
        number = int(match.group())
        reference = ATTR_927.attr_927[0]["values"]
        logger.debug(f"Searching for number {number} in reference with {len(reference)} entries")
        
        for val in reference:
            if number == val["label"]:
                logger.info(f"Found match in ATTR_927: {number} -> {val['code']}")
                return val["code"]
                
        logger.warning(f"No match found for number {number} in ATTR_927, returning default value")
        return "118978"
        
    except (ValueError, KeyError) as e:
        logger.error(f"Error processing ATTR_927 lookup: {e}, returning default value")
        return "118978"


@safe_execute("format_928", "input_value")
def format_928(input_value: List[str]) -> Optional[int]:
    """Форматирование размеров кровати"""
    if not validate_input(input_value, list):
        logger.warning("Invalid input for format_928, returning default value")
        return "119013"
        
    bed_size_mapping = {
        "90/180x200cm": "119013",
        "Liegefläche 60 x 180 cm": "119023",
        "150 x 90 cm": "119029", # наоборот чуть чуть
        "ca. 160cm x 200cm": "119012",
        "120x190cm": "119008",
        "160x200cm": "119012",
        "150 x 200 cm": "119053",
        "200 x 200cm": "119014",
        "80/160x200cm": "119012",
        "60 x 120 cm": "119023",
        "ca. 120cm x 200cm": "119009",
        "ca: 70 x 130 cm": "119024",
        "ca. 180cm x 200cm": "119013",
        "180cm x 200cm": "119013",
        "ca: 90  x 190 cm": "119020",
        "90 x 200 cm": "119021",
        "ca: 70  x 130 cm": "119024",
        "90x200cm": "119021",
        "160 x 200 cm": "119012",
        "160x200 oder 180x200cm": "119012",  # выбор первого размера
        "120cm x 200cm": "119009",
        "180x200cm": "119013",
        "60 x 180 cm": "119017",
        "140 x 200 cm": "119011",
        "100 x 200 cm": "119022",
        "80 x 160 cm": "119016",
        "Doppelbett": "119014",
        "ca. 60 x 180 cm": "119017",
        "180x200 cm": "119013",
        "160cm x 190cm": "119031",
        "220 x 220 cm": "119933",
        "90 x 190 cm": "119020",
        "60 x200 cm": "119004",
        "ca:100 x 200 cm": "119022",
        "160x200": "119012",
        "120 x 200 cm": "119009",
        "120x190 cm": "119008",
        "200cm x 200cm": "119014",
        "180 x 200cm": "119013",
        "ca: 90 x 190 cm": "119020",
        "120 x 190cm": "119008",
        "160 x 200cm": "119012",
        "70 x 130 cm": "119024",
        "140x200cm": "119011",
        "ca.60 x 180 cm": "119017",
        "200 x 200 cm": "119014",
        "180 x 200 cm": "119013",
        "ca: 60 x 120 cm": "119023",
        "ca: 180 x 143 x cm": "119013",
        "ca: 200 x 163 x cm": "119014",
        "ca: 224 x 180 x cm": "119933",
        "ca: 210 x 195 x cm": "119025",
        "ca: 345 x 215 x cm": "119933",
        "ca: 205 x 160 x cm": "119014",
        "ca: 265 x 225 x cm": "119933",
        "ca: 200 x 155 x cm": "119014",
        "ca: 220 x 240 x cm": "119933",
        "ca: 338 x 170 x cm": "119933",
        "ca: 227 x 49 x 225 cm": "119933",
        "ca: 210 x 200 x cm": "119025"
    }
    
    value = get_first_value(input_value)
    result = bed_size_mapping.get(value)
    if result:
        logger.debug(f"Bed size mapping: '{value}' -> {result}")
        return result
    logger.warning(f"Bed size '{value}' not found in mapping, returning default '119013'")
    return "119013"



def format_150_151_152(
    value: Union[List[str], str],
    index: Optional[int] = None
) -> Optional[float]:
    """
    Форматирование численных значений с плавающей точкой.
    Поддержка размеров '135 x 77 x 90' или 'ca. 9Ft. 248 x 157 x 80 cm'.
    Если index задан, возвращается число с этой позиции (0-based).
    """
    logger.info(f"Processing numeric value: {value}")
    
    try:
        logger.debug(f"value: {value}")
        if isinstance(value, list) and value:
            value = value[0]
            
        if not isinstance(value, str):
            logger.warning(f"Expected string, got {type(value)}, returning default value")
            return 50.0
            
        # Нормализация
        normalized_value = value.lower().replace(",", ".").replace("ca.", "").strip()
        # Удаляем числа с Ft
        normalized_value = re.sub(r"\d+\s*ft\.?", "", normalized_value)
        logger.debug(f"Normalized value: '{value}' -> '{normalized_value}'")

        # mm -> mm, cm -> cm
        normalized_value = normalized_value.replace("мм", "mm").replace("см", "cm")

        # Преобразуем "число + ед. изм."
        tokens = re.findall(r"(\d*\.?\d+)\s*(mm|cm)?", normalized_value)

        numbers = []
        for num, unit in tokens:
            try:
                val = float(num)
                if unit == "mm":
                    logger.debug(f"Converting mm to cm: {val}")
                    val = val / 10.0   # перевод мм -> см
                # если cm или unit пустой – оставляем как есть
                numbers.append(round(val, 2))
            except ValueError:
                continue

        if not numbers:
            logger.warning(f"No numeric value found in '{value}', returning default value")
            return 50.0
        
        # Возврат по индексу
        if index is not None and len(numbers) > 1:
            logger.debug(f"List of numbers: {numbers}")
            
            if 0 <= index < len(numbers):
                if len(numbers) == 2 and index == 2:
                    logger.debug(f"There is only two numbers in list, so third=second : {numbers[1]}") 
                    return numbers[1] 
                logger.debug(f"Returned value: '{value}' -> '{numbers[index]}' -> INDEX: {index}")
                return numbers[index]
            else:
                logger.warning(f"Index {index} out of range for '{value}', возвращаем numbers[0] : {numbers[0]}'")
                return numbers[0]
        
        logger.debug(f"Index is None or len(numbers) >= 1, returning numbers[0]: {numbers[0]}")
        return numbers[0]
            
    except (ValueError, AttributeError) as e:
        logger.error(f"Error parsing numeric value '{value}': {e}, returning default value")
        return 50.0


@safe_execute("format_175", "input_value")
def format_175(input_value: List[str]) -> Optional[str]:
    """Форматирование по атрибуту 175: поддержка чисел и текстов (например 'Mehr als 6')"""
    if not validate_input(input_value, list):
        logger.warning("Invalid input for format_175, returning default value")
        return 

    try:
        reference = ATTR_175.attr_175[0]["values"]
        if not reference:
            logger.error("ATTR_175 reference data is empty")
            return "11147"

        target = get_first_value(input_value).strip()
        logger.debug(f"Processing target value: '{target}'")

        # --- Попытка извлечь число из строки ---
        match = re.search(r"\d+", target)
        num = int(match.group()) if match else None

        if num is not None:
            logger.debug(f"Extracted number: {num}")

            # Спец-обработка > 12
            if num > 12:
                for val in reference:
                    if "> 12" in val["label"] or "Mehr als 12" in val["label"]:
                        logger.info(f"Number {num} > 12, mapped to {val['code']}")
                        return val["code"]

            # Поиск по точному числу в начале label
            for val in reference:
                if val["label"].startswith(str(num)):
                    logger.info(f"Found numeric match: {num} -> {val['code']}")
                    return val["code"]

                for translation in val.get("label_translations", []):
                    if translation["value"].startswith(str(num)):
                        logger.info(f"Found numeric translation match: {num} -> {val['code']}")
                        return val["code"]
        else:
            logger.warning("No number extracted, proceeding with text matching, returning default value")
            return "11147"
        
    except (KeyError, AttributeError) as e:
        logger.error(f"Error processing ATTR_175 lookup: {e}, returning default value")
        return "11147"
    
    
def product_quantity_check(product_article: str) -> int:
    """
    Product quantity check.
    Returns 1 if product is special (env), otherwise 20.
    """
    
    if not isinstance(product_article, str) or not product_article:
        logger.warning("Invalid product article for quantity check, returning default value 20")
        return 20
    
    article = unicodedata.normalize("NFKC", product_article).casefold().strip()
    special_word =  unicodedata.normalize("NFKC", settings.special_quantity_word).casefold().strip()
    
    pattern = rf"\b{re.escape(special_word)}\b"
    
    if re.search(pattern, article, flags=re.UNICODE) is not None:
        return 1
    else:
        return 20