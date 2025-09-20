# src/routers Module

This module defines all API route handlers for the XXLmebel 1 API service. Each router is responsible for a specific set of endpoints and business logic.

## mirakl_system_router.py
Handles Mirakl platform status, error reporting, and system configuration endpoints.
- **Endpoints:**
  - `/import-product-error/{import_parameter}`: Returns error reports for product imports to Mirakl.
  - `/mirakl-platform-settings`: Returns current Mirakl platform settings.
  - `/mirakl-product-non-integrated/{import_parameter}`: Checks for products not integrated into Mirakl.
- **Example function:**
  ```python
  @router.get("/mirakl-platform-settings")
  async def get_mirakl_settings(...):
      # Returns Mirakl platform settings as a dict
  ```
- **Responsibilities:**
  - Aggregates error and status information from Mirakl.
  - Provides system configuration for integration health checks.

## product_router.py
Manages product import endpoints from Afterbuy to Mirakl.
- **Endpoints:**
  - `/import-product/{ean}`: Imports a single product by EAN.
  - `/import-products`: Imports multiple products by a list of EANs.
  - `/import-products-by-fabric/{afterbuy_fabric_id}`: Imports products by Afterbuy fabric ID.
- **Example function:**
  ```python
  @router.post("/import-product/{ean}")
  async def import_product(ean: int, ...):
      # Fetches product from Afterbuy, maps attributes, generates CSV, imports to Mirakl
  ```
- **Responsibilities:**
  - Fetches product data from Afterbuy.
  - Maps and normalizes product attributes for Mirakl.
  - Generates CSV and triggers import to Mirakl.
  - Handles batch imports and error reporting.

## test_router.py
Provides development and debugging endpoints for product mapping and image processing.
- **Endpoints:**
  - `/test-import-product/{ean}`: Returns mapped data for a single product (no import).
  - `/test-import-products-by-fabric/{afterbuy_fabric_id}`: Returns mapped data for all products in a fabric (no import).
  - `/test-resize-image`: Tests image resizing and FTP upload.
- **Example function:**
  ```python
  @router.post("/test-resize-image")
  async def test_resize_image(data: TestImageResize, ...):
      # Resizes image and uploads to FTP for testing
  ```
- **Responsibilities:**
  - Allows developers to validate mapping logic and image processing.
  - Useful for troubleshooting integration issues before production import.