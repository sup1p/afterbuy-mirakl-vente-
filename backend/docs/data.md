# Data Constants Overview

## Purpose
The `src/const` directory contains constant data definitions used for attribute mapping, value translation, and product data normalization between Afterbuy and Mirakl platforms. These constants ensure consistent transformation and validation of product attributes during import and export operations.

## Main Files
### constants.py
- Defines the main attribute mapping dictionary (`mapping_attr`), which links Mirakl attribute codes (e.g., `ATTR_175`) to Afterbuy attribute names or lists of possible names.
- Some mappings are set to `NO MAPPING` to indicate missing or unsupported attributes.
- Used throughout the mapping and data transformation logic to ensure correct attribute correspondence.

### attrs/
- Contains individual Python files for specific Mirakl attributes (e.g., `ATTR_106.py`, `ATTR_175.py`, `ATTR_7.py`, etc.).
- Each file defines a list of possible values for the attribute, including:
  - `code`: Mirakl attribute code
  - `label`: Main label (usually in French)
  - `values`: List of possible values, each with its own code, label, and translations (German, English, etc.)
- These files are used to:
  - Validate and normalize incoming product data
  - Provide translation and value mapping for multilingual support
  - Ensure only allowed values are used for Mirakl imports

## Data Format
- All attribute files use Python lists of dictionaries for easy programmatic access.
- Value translations are provided for each supported locale, enabling internationalization and correct mapping for Mirakl requirements.

## Example Usage
- During product import, the mapping logic uses `mapping_attr` to find the correct Mirakl attribute for each Afterbuy property.
- For attributes with enumerated values (e.g., number of seats, size), the corresponding file in `attrs/` is loaded to validate and translate the value.
- If a product property does not match any allowed value, it may be skipped or flagged for manual review.

## Extensibility
- New attributes or value sets can be added by creating new files in `attrs/` and updating `constants.py`.
- The structure supports easy updates for new Mirakl requirements or additional languages.

## Summary
The constants in `src/const` are essential for robust, accurate, and scalable product data integration between Afterbuy and Mirakl, supporting attribute mapping, value validation, and multilingual translation.
