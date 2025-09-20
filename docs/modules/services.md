# src/services Module

This module contains the business logic and integration services for Afterbuy and Mirakl platforms, as well as data mapping and CSV conversion utilities. Each file is responsible for a specific aspect of the integration pipeline.

## afterbuy_api_calls.py
Handles all interactions with the Afterbuy API, including:
- **Authentication:** Obtains and manages access tokens for API requests.
- **Product Data Retrieval:** Fetches product details, brand, and fabric information from Afterbuy.
- **Retry Logic:** Implements robust error handling and retry mechanisms for network/API failures.
- **Example functions:**
  - `async def get_access_token(httpx_client)`: Authenticates and returns an access token.
  - `async def get_product_data(ean, httpx_client)`: Retrieves product data by EAN.
  - `async def get_products_by_fabric(afterbuy_fabric_id, httpx_client)`: Gets products by fabric ID.

## mirakl_api_calls.py
Manages all communication with the Mirakl API, including:
- **Product Import:** Uploads product data (CSV) to Mirakl for import.
- **Error Checking:** Retrieves error reports and import statuses.
- **Platform Configuration:** Fetches Mirakl platform settings and integration health.
- **Example functions:**
  - `async def import_product(csv_content, httpx_client)`: Imports products to Mirakl.
  - `async def check_offer_import_error(import_parameter, httpx_client)`: Gets error report for a specific import.
  - `async def check_platform_settings(httpx_client)`: Returns platform settings.

## mapping.py
Transforms and normalizes product data from Afterbuy to Mirakl format:
- **Attribute Mapping:** Maps Afterbuy attributes to Mirakl attributes using constants.
- **Image Processing:** Handles product image validation, resizing, and FTP upload.
- **Category Normalization:** Ensures product categories are correctly mapped.
- **Example functions:**
  - `async def map_attributes(data, httpx_client)`: Maps and normalizes product data for Mirakl.
  - Helper functions for image and attribute processing.

## csv_converter.py
Converts product data structures to CSV format for Mirakl import:
- **CSV Generation:** Serializes mapped product data to CSV, ensuring correct encoding and formatting.
- **Batch Support:** Handles both single and bulk product exports.
- **Example functions:**
  - `def make_csv(data)`: Converts a single product to CSV.
  - `def make_big_csv(data)`: Converts multiple products to a single CSV file.