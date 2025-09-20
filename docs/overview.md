# XXLmebel 1 API — Project Overview

## Purpose
XXLmebel 1 API is a backend service designed to automate the migration and synchronization of large volumes of product data from the Afterbuy platform to the Mirakl (vente-unique) marketplace. It streamlines product management, data transformation, error reporting, and integration between e-commerce systems.

## Architecture
- **Framework:** FastAPI (asynchronous Python web framework)
- **API Routers:**
  - `product_router`: Endpoints for importing products (single, batch, by fabric ID)
  - `mirakl_system_router`: Endpoints for Mirakl platform settings, error reports, and system checks
  - `test_router`: Development/testing endpoints for product mapping and image processing
- **Services:**
  - `afterbuy_api_calls`: Handles authentication and product data retrieval from Afterbuy
  - `mirakl_api_calls`: Manages product import, error checking, and platform configuration for Mirakl
  - `mapping`: Transforms Afterbuy product data into Mirakl-compatible format
  - `csv_converter`: Converts product data to CSV for Mirakl import
- **Utilities:**
  - Image processing and FTP upload
  - EAN validation and formatting
  - Attribute mapping and HTML description generation
- **Configuration:**
  - `.env` for credentials, API keys, and environment settings
  - Logging with rotation (`logs/logs.log`)

## Main Packages & Technologies
- `fastapi` — API framework
- `httpx` — Asynchronous HTTP client
- `aioftp` — Asynchronous FTP client for image uploads
- `pandas` — CSV and error report parsing
- `logging` — Centralized logging with rotation
- `uv` — Dependency management and environment setup

## Data Flow
1. **Product Retrieval:**
   - Products are fetched from Afterbuy via authenticated API calls.
2. **Data Mapping:**
   - Raw product data is mapped to Mirakl format, including attribute transformation and image handling.
3. **CSV Generation:**
   - Mapped data is converted to CSV for Mirakl import.
4. **Import & Error Handling:**
   - Products are imported to Mirakl; error reports and platform settings are accessible via dedicated endpoints.

## Extensibility
- Modular service and router structure allows for easy extension and maintenance.
- Environment variables and configuration files support flexible deployment.

## Usage
- RESTful API endpoints for product import, error checking, and platform management
- Interactive API documentation via Swagger UI (`/docs`)

## Deployment
- Requires Python 3.11+
- Environment setup via `.env` and `uv`
- Can be run with `uv run uvicorn src.main:app`

For details on endpoint usage and setup, see the main README.md and API documentation.
