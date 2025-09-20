# src/utils Module

This module provides utility functions for data formatting, image processing, and attribute manipulation. Each file supports a specific aspect of product data normalization and integration.

## format_attr.py
Functions for checking and formatting product quantity and other attributes.
- **Example:** `product_quantity_check(value)` validates and normalizes quantity values.

## format_ean.py
EAN validation and formatting utilities.
- **Example:** `is_valid_ean(ean)` checks if an EAN is valid for product import.

## format_html.py
HTML parsing and extraction utilities for product descriptions and properties.
- **Example:** `extract_product_properties_from_html(html)` extracts structured data from HTML descriptions.

## image_worker.py
Image processing functions, including resizing, validation, and FTP upload support.
- **Example:** `resize_image_and_upload(url, ean, httpx_client, ftp_client, test)` resizes images and uploads them to FTP.

## substitute_formatter.py
Attribute substitution and string formatting helpers for dynamic mapping and normalization.
- **Example:** `substitute_attr(template, values)` replaces placeholders in attribute templates with actual values.
