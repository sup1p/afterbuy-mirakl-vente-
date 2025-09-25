import re
import unicodedata
import json
import ast
import logging
from src.utils.lutz_utils.html_parser import extract_productdetails
from src.core.settings import settings
from logs.config_logs import setup_logging

setup_logging()

logger = logging.getLogger(__name__)

# --------------------- Глобальный флаг ---------------------
ENABLE_DEFAULTS = True  # <-- закомментируй или поставь False чтобы отключить автозаглушки


def _norm_key(s: str) -> str:
    if s is None:
        return ""
    return unicodedata.normalize("NFKC", str(s)).strip().lower()


def get_value(d: dict, path: str):
    keys = path.split(".")
    current = d
    for k in keys:
        if not isinstance(current, dict) or k not in current:
            return ""
        current = current[k]
    return current


def get_prop_first(d: dict, prop_key: str) -> str:
    props = d.get("properties")
    if not isinstance(props, dict):
        return ""
    val = props.get(prop_key)
    if isinstance(val, list) and val:
        return str(val[0]).strip()
    if isinstance(val, str):
        return val.strip()
    return ""


def _ensure_props_dict(data: dict):
    props = data.get("properties")
    if props is None:
        data["properties"] = {}
        return
    if isinstance(props, dict):
        return
    if isinstance(props, str):
        try:
            parsed = json.loads(props)
            if isinstance(parsed, dict):
                data["properties"] = parsed
                return
        except Exception:
            pass
        try:
            parsed = ast.literal_eval(props)
            if isinstance(parsed, dict):
                data["properties"] = parsed
                return
        except Exception:
            pass
    data["properties"] = {}


def _extract_number_from_text(s: str):
    if s is None:
        return None
    s = str(s)
    s = s.replace("ca:", " ").replace("ca", " ").replace("≈", " ").replace("~", " ")
    s = s.replace(",", ".")
    s = re.sub(r"\bcm\b", " ", s, flags=re.IGNORECASE)
    m = re.search(r"[-+]?\d+(\.\d+)?", s)
    if not m:
        return None
    try:
        num = float(m.group(0))
    except Exception:
        return None
    rounded = round(num, 2)
    if rounded.is_integer():
        return str(int(rounded))
    text = f"{rounded:.2f}".rstrip("0").rstrip(".")
    return text


def normalize_value(val, numeric=False):
    if val is None:
        return ""
    if isinstance(val, list) and val:
        val = val[0]
    if numeric:
        num = _extract_number_from_text(val)
        return num or ""
    s = str(val)
    s = s.replace("cm", "").replace("ca:", "").replace("ca", "").strip()
    return s


def split_lying_surface(val: str):
    if not val:
        return "", ""
    s = str(val)
    s = s.replace("Maße:", "").replace("Maße", "")
    parts = re.split(r"\s*[x×*]\s*", s)
    nums = []
    for p in parts:
        n = _extract_number_from_text(p)
        if n:
            nums.append(n)
    if len(nums) >= 2:
        length = nums[0]
        width = nums[1]
        return width, length
    m_all = re.findall(r"[-+]?\d+(\.\d+)?", s.replace(",", "."))
    if len(m_all) >= 2:
        length = m_all[0]
        width = m_all[1]
        return width, length
    cleaned = s.strip()
    return cleaned, cleaned


def to_code(prefix: str, label: str) -> str:
    """Обычная генерация кода"""
    if not label:
        return ""
    code = label.lower()
    code = re.sub(r"[^a-z0-9]+", "_", code)
    code = re.sub(r"_+", "_", code).strip("_")
    return f"{prefix}_{code}" if code else ""


def to_color_code(label: str) -> str:
    """Генерация кода для цветов: color_grayBrown"""
    if not label:
        return ""
    parts = re.split(r"[^a-zA-Z0-9]+", label)
    parts = [p for p in parts if p]
    if not parts:
        return ""
    base = parts[0].lower()
    rest = [p.capitalize() for p in parts[1:]]
    return "color_" + base + "".join(rest)


# --------------------- Material Mapper ---------------------
def map_material(data: dict, material_mapping: dict):
    for key in ["Material", "Gestellmaterial", "Füllmaterial", "Polsterstoff"]:
        val = get_prop_first(data, key)
        if val:
            lookup = val.lower()
            if material_mapping and lookup in material_mapping:
                en_mat = material_mapping[lookup]
                if en_mat:
                    mat_code = "material_" + (en_mat[0].lower() + en_mat[1:] if len(en_mat) > 0 else en_mat)
                else:
                    mat_code = to_code("material", en_mat)
                return en_mat, mat_code, key, val
            else:
                en_mat = val
                mat_code = to_code("material", en_mat)
                return en_mat, mat_code, key, val
    return "", "", "", ""


# --------------------- Extra Dimensions Parser ---------------------
def extract_dimensions(properties: dict) -> dict:
    result = {}
    if not isinstance(properties, dict):
        return result
    pattern = re.compile(r"(\d+)\s*[x×]\s*(\d+)\s*[x×]\s*(\d+)", re.I)
    for key, values in properties.items():
        if not values or not isinstance(values, list):
            continue
        for val in values:
            match = pattern.search(str(val))
            if match:
                length, width, height = match.groups()
                result["specifications.length_depth_cm"] = length
                result["specifications.width_cm"] = width
                result["specifications.height_cm"] = height
                return result
    return result


# --------------------- Special material overrides ---------------------
SPECIAL_MATERIALS = {
    "acryl": ("Acryl", "material_plastic"),
    "mdf/spanplatte": ("MDF/Spanplatte", "materialImitation_MDF"),
}


# --------------------- Quantity check ---------------------
def product_quantity_check(article: str) -> int:
    """Если в article встречается 'swofort', то quantity = 1, иначе = 20"""
    if not article:
        return 20
    if "swofort" in article.lower():
        return 1
    return 20


def safe_get(arr, idx, default=""):
    """Безопасное получение из списка"""
    try:
        return arr[idx]
    except Exception:
        return default


# --------------------- Main Mapper ---------------------
async def map_product(data: dict, mapping: dict, fieldnames: list,
                      real_mapping_v12: dict, color_mapping: dict,
                      material_mapping: dict, other_mapping: dict, brand_mapping: dict) -> dict:
    result = {}
    _ensure_props_dict(data)

    # 1) Базовый проход по YAML-мэппингу
    for src, dst in mapping.items():
        value = get_value(data, src)

        # --- Special: images — сохраняем оригинальные ссылки как есть и НЕ нормализуем/тримим 'ca' и т.д. ---
        # src в mapping.yaml — это ключ из source, например "pic_main" или "pics"
        if src in ("pic_main", "pics"):
            if value:
                if src == "pic_main":
                    # пишем в поля, которые ожидает csv/mapping
                    result["images.main_image"] = value
                    result["main_picture"] = value
                else:
                    # приводим пробельные последовательности к одному пробелу, но НЕ изменяем содержание ссылок
                    sec = " ".join(str(value).split())
                    result["images.secondary_image"] = sec
            continue

        if src == "html_description":
            value = extract_productdetails(value)

            # ⚡ Ограничиваем описание максимум 3000 символами
            if value and len(value) > 3000:
                value = value[:2997] + "..."

            result["product_description"] = value
            result["description [de]"] = value
            continue

        if isinstance(dst, list) and (
            "specifications.lying_surface_width_cm" in dst
            or "specifications.lying_surface_length_cm" in dst
        ):
            w, l = split_lying_surface(value)
            result["specifications.lying_surface_width_cm"] = w
            result["specifications.lying_surface_length_cm"] = l
            continue

        if isinstance(dst, list):
            for d in dst:
                if d in fieldnames:
                    # numeric fields keep numeric normalization
                    if d.endswith("_cm") or (d.startswith("specifications.") and "_cm" in d):
                        result[d] = normalize_value(value, numeric=True)
                    else:
                        result[d] = normalize_value(value)
        else:
            if dst in fieldnames:
                if dst.endswith("_cm") or (dst.startswith("specifications.") and "_cm" in dst):
                    result[dst] = normalize_value(value, numeric=True)
                else:
                    result[dst] = normalize_value(value)

    # 2) Категория
    category_id = str(data.get("category", "")).strip()
    result["category"] = real_mapping_v12.get(category_id, {}).get("target_id", "")

    # 3) Цвет
    de_color = get_prop_first(data, "Farbe")
    if de_color:
        en_color = color_mapping.get(de_color.lower(), de_color)
        result["specifications.color"] = en_color
        result["Color"] = to_color_code(en_color)

    # 4) Материал
    en_mat, mat_code, mat_key, mat_orig = map_material(data, material_mapping)
    if en_mat:
        special = SPECIAL_MATERIALS.get(en_mat.lower()) or SPECIAL_MATERIALS.get(mat_orig.lower())
        if special:
            result["specifications.main_material"], result["Material"] = special
        else:
            result["specifications.main_material"] = en_mat
            result["Material"] = mat_code

    # 5) Бренд
    de_brand = get_prop_first(data, "Marke")
    if not de_brand:
        de_brand = data.get("collection", "")

    mapped_brand = None
    key = _norm_key(de_brand)
    if key:
        mapped_brand = brand_mapping.get(key)
        if not mapped_brand:
            alt = (key
                   .replace("ö", "o")
                   .replace("ü", "u")
                   .replace("ä", "a")
                   .replace("ß", "ss"))
            mapped_brand = brand_mapping.get(alt)

    final_brand = mapped_brand or de_brand or ""
    if "brand" in fieldnames:
        result["brand"] = final_brand
    if "Brand" in fieldnames:
        result["Brand"] = final_brand
    if "Brand-root-class" in fieldnames:
        result["Brand-root-class"] = final_brand

    # 6) Дополнительные размеры
    extra_dims = extract_dimensions(data.get("properties", {}))
    for k, v in extra_dims.items():
        if v and not result.get(k):
            result[k] = v

    # 7) Размеры (зеркально)
    if result.get("specifications.width_cm"):
        result["specifications.width_cm"] = normalize_value(result["specifications.width_cm"], numeric=True)
        result["DimensionWidth"] = result["specifications.width_cm"]
    if result.get("specifications.length_depth_cm"):
        result["specifications.length_depth_cm"] = normalize_value(result["specifications.length_depth_cm"], numeric=True)
        result["DimensionDepthLength"] = result["specifications.length_depth_cm"]
    if result.get("specifications.height_cm"):
        result["specifications.height_cm"] = normalize_value(result["specifications.height_cm"], numeric=True)
        result["DimensionHeight"] = result["specifications.height_cm"]

    # 8) Дистрибьютор
    result["DistributorName"] = settings.distributor_name_lutz
    result["DistributorStreet"] = settings.distributor_street_lutz
    result["DistributorZip"] = settings.distributor_zip_lutz
    result["DistributorCity"] = settings.distributor_city_lutz
    result["DistributorCountry"] = settings.distributor_country_lutz

    # 9) Заголовок DE
    if result.get("title"):
        result["name [de]"] = result["title"]

    # 10) EAN fallback
    if not result.get("ean") and result.get("gtin"):
        result["ean"] = result["gtin"]

    # 11) Главная картинка fallback
    if result.get("images.main_image") and not result.get("main_picture"):
        result["main_picture"] = result["images.main_image"]

    # 12) Дополнительные оффер-поля
    article_val = data.get("article", "")
    result["price"] = str(data.get("price", "0.00"))
    result["state"] = 11
    result["quantity"] = product_quantity_check(article_val)

    # --- Финальный проход: автозаполнение заглушками ---
    if ENABLE_DEFAULTS:
        for field in fieldnames:
            if not result.get(field):
                if field.endswith("_cm") or "Dimension" in field:
                    result[field] = "1"
                elif "color" in field.lower():
                    result[field] = "color_black"
                elif "material" in field.lower():
                    result[field] = "material_plastic"

    return {field: result.get(field, "") for field in fieldnames}