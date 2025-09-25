import yaml
import json
import os
import unicodedata

BASE_DIR = os.path.dirname(__file__)


def _norm_key(s: str) -> str:
    if s is None:
        return ""
    return unicodedata.normalize("NFKC", str(s)).strip().lower()


# mapping.yaml
with open(os.path.join(BASE_DIR, "mapping.yaml"), encoding="utf-8") as f:
    mapping = yaml.safe_load(f)

# category_mapping
with open(os.path.join(BASE_DIR, "real_mapping_v12.json"), encoding="utf-8") as f:
    real_mapping_v12 = json.load(f)

# color_mapping.yaml
with open(os.path.join(BASE_DIR, "color_mapping.yaml"), encoding="utf-8") as f:
    color_mapping = yaml.safe_load(f)

# material_mapping.yaml
with open(os.path.join(BASE_DIR, "material_mapping.yaml"), encoding="utf-8") as f:
    material_mapping = yaml.safe_load(f)

# other_mapping.yaml (опционально)
_other = {}
_other_path = os.path.join(BASE_DIR, "other_mapping.yaml")
if os.path.exists(_other_path):
    with open(_other_path, encoding="utf-8") as f:
        _other = yaml.safe_load(f) or {}
other_mapping = _other

# brand_mapping.yaml — нормализуем ключи
with open(os.path.join(BASE_DIR, "brand_mapping.yaml"), encoding="utf-8") as f:
    _raw_brand = yaml.safe_load(f) or {}
brand_mapping = {_norm_key(k): v for k, v in _raw_brand.items()}