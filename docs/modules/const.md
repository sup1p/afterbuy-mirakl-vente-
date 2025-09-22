# src/const Module

This module contains constant data and attribute mappings essential for product data normalization and transformation between Afterbuy and Mirakl platforms. Each file supports attribute translation, value validation, and multilingual support.

## constants.py
Defines dictionaries and mappings for attribute correspondence between Mirakl and Afterbuy.
- **mapping_attr:** Main dictionary mapping Mirakl attribute codes (e.g., `ATTR_175`) to Afterbuy attribute names or lists of possible names.
- **NO MAPPING:** Indicates missing or unsupported attributes.
- **Usage:** Used in mapping logic to translate and validate product attributes during import/export.

## attrs/
Contains individual files for Mirakl attributes (e.g., `ATTR_106.py`, `ATTR_175.py`).
- **Format:** Each file defines a list of allowed values for the attribute, including:
  - `code`: Mirakl attribute code
  - `label`: Main label (usually in French)
  - `values`: List of possible values, each with its own code, label, and translations (German, English, etc.)
- **Usage:**
  - Validates and normalizes incoming product data
  - Provides translation and value mapping for multilingual support
  - Ensures only allowed values are used for Mirakl imports

## Adding new:
If you have found mistakes just replace keywords or codes, or if you want to add extra keys just change default `str` to `list` and just keep increasing it.