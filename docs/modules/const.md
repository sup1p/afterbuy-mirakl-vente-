# src/const Module

This module contains constant data and attribute mappings essential for product data normalization and transformation between Afterbuy and Mirakl platforms. Each file supports attribute translation, value validation, and multilingual support.

# constantas_vente:

## - constants.py
Defines dictionaries and mappings for attribute correspondence between Mirakl and Afterbuy.
- **mapping_attr:** Main dictionary mapping Mirakl attribute codes (e.g., `ATTR_175`) to Afterbuy attribute names or lists of possible names.
- **NO MAPPING:** Indicates missing or unsupported attributes.
- **Usage:** Used in mapping logic to translate and validate product attributes during import/export.

## - attrs/
Contains individual files for Mirakl attributes (e.g., `ATTR_106.py`, `ATTR_175.py`).
- **Format:** Each file defines a list of allowed values for the attribute, including:
  - `code`: Mirakl attribute code
  - `label`: Main label (usually in French)
  - `values`: List of possible values, each with its own code, label, and translations (German, English, etc.)
- **Usage:**
  - Validates and normalizes incoming product data
  - Provides translation and value mapping for multilingual support
  - Ensures only allowed values are used for Mirakl imports

## - Adding new:
If you have found mistakes just replace keywords or codes, or if you want to add extra keys just change default `str` to `list` and just keep increasing it.

# constantas_lutz:

## - yaml files

This YAML fileы define field mappings between Afterbuy product data and the target marketplace (Mirakl) schema.
The mapping ensures that product attributes are correctly transferred and normalized during data synchronization.

**Structure:**

- Top-level fields: represent product attributes (e.g., category, ean, article, pic_main, pics).

- Nested properties.* fields: represent product specifications or characteristics.

**Each entry specifies either:**

- A string → direct mapping to a single field in the target schema.

- A list of strings → multiple possible fields; the first non-empty value will be used.

# prompts.py
This module defines prompt builder functions used to generate structured requests for an AI model (e.g., OpenAI, via Pydantic-AI based schemas).
The purpose is to create clean, marketplace-ready product descriptions in multiple languages, based on raw product data and offer details.

**Functions**

- `build_description_prompt_vente`:

- - Generates a prompt instructing the AI to return two product descriptions:

- - - `description_de`: German, focused on the product itself (design, dimensions, materials, usage, style).

- - - `description_fr`: French, focused on the commercial offer (price, delivery time, warranty, advantages for the buyer).

- - Ensures compliance with marketplace requirements: min/max characters, no HTML tags, no technical clutter.

- - Input data: raw text, product properties, article title, price, and delivery days.

- `build_description_prompt_lutz`

- - Similar structure, but outputs:

- - - `description_de`: German, product-focused.

- - - `description_en`: English, offer-focused.

- - Otherwise follows the same rules and formatting logic.

**Common Rules for Both**

- Output must respect a fixed schema (description_de, description_fr or description_en).

- Maximum length per description: 2250 characters (configured via settings.max_description_chars).

- Cleaning rules: remove HTML, special characters, editor artifacts.

- Writing style: fluent, natural, customer-friendly, without redundant technical jargon.

*Usage in the System*

- These functions are called before sending a request to the AI.

- They return a well-structured prompt string, ready to be passed to the model.

- The resulting AI output can then be validated/parsed with Pydantic models (ensuring schema compliance).