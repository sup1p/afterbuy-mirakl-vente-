# src/utils Module

This module provides utility functions for data formatting, image processing, and attribute manipulation. Each file supports a specific aspect of product data normalization and integration.

# vente_utils:

## - format_attr.py
Functions for checking and formatting product quantity and other attributes.
- **Example:** `product_quantity_check(value)` validates and normalizes quantity values.

## - format_little.py
EAN validation and getting delivery days of chosen fabric.
- **Example:** `is_valid_ean(ean)` checks if an EAN is valid for product import.

## - format_html.py
HTML parsing and extraction utilities for product descriptions and properties.
- **Example:** `extract_product_properties_from_html(html)` extracts structured data from HTML descriptions.

## - image_worker.py
Image processing functions, including resizing, validation, and FTP upload support.
- **Example:** `resize_image_and_upload(url, ean, httpx_client, ftp_client, test)` resizes images and uploads them to FTP.

## - substitute_formatter.py
Attribute substitution and string formatting helpers for dynamic mapping and normalization.
- **Example:** `substitute_attr(template, values)` replaces placeholders in attribute templates with actual values.


# lutz_utils:
## - csv_tools.py
Creates CSV by given mapping for uploading it to mirakl.
- **Example:** `write_csv(fieldnames: list, rows: list)` creates csv file in python memory.
## - image_processing.py
Edits incorrect images and sends it to the FTP server - also removes background of the image.
- **Example:** `process_single_image(url: str, ean: str, ftp_client: aioftp.Client, httpx_client: httpx.AsyncClient)` contains all other functions and fully processes image - downloads/resizes/uploads to ftp.
## - mapping_tools.py
Maps all the attributes fetched from afterbuy to mirakl attributes.