

# XXLmebel API — Project Overview

## Purpose

XXLmebel API is an asynchronous FastAPI backend service for automating the migration and synchronization of large volumes of product data between the Afterbuy platform and the Mirakl marketplace (vente-unique, Lutz). The service provides integration, transformation, CSV generation, error handling, user management, and centralized logging.

## Architecture & Main Components

- **FastAPI** — main web framework.
- **src/** — application source code:
  - **main.py** — entry point, router registration, resource initialization.
  - **models.py** — ORM models (e.g., User).
  - **resources.py** — global objects (HTTP client, LLM agent).
  - **core/** — settings, dependencies, security.
  - **const/** — constants, attributes, YAML/JSON/mappings for data transformation.
  - **routers/** — API routers:
   - **vente/** — product import, errors, Mirakl settings.
   - **lutz/** — separate routers for Lutz integration.
   - **user_router.py** — authentication and user management.
  - **services/** — business logic:
   - **vente_services/** — Afterbuy/Mirakl integration, mapping, CSV generation.
   - **lutz_services/** — similar for Lutz.
  - **schemas/** — Pydantic schemas for data validation and serialization.
  - **utils/** — utilities for image processing, attributes, HTML, CSV.
- **alembic/** — database migrations.
- **logs/** — logging configuration and log files.

## Main Processes

1. **Authentication & User Management**
  - OAuth2, JWT, roles (admin/user).
  - Routes: `/auth/create-user`, `/auth/login`.

2. **Product Import**
  - Fetching data from Afterbuy (by EAN, by fabric_id).
  - Attribute mapping and normalization for Mirakl/Lutz.
  - CSV generation for import.
  - Image upload to FTP, processing and resizing.
  - Product import to Mirakl/Lutz via API.

3. **Error Handling & Reporting**
  - Getting import status, errors, non-integrated products.
  - Endpoints for reports and platform status.

4. **Attributes & Constants Handling**
  - Mapping, validation, value translation, multilingual support.
  - YAML/JSON/py files for attribute correspondence.

5. **Logging**
  - All operations are logged in `logs/logs.log` with rotation.

## Configuration

- All parameters (keys, passwords, URLs) are set via `.env` and used through `core/settings.py`.
- Alembic — for migrations and DB schema management.

## Extensibility

- Modular structure: easy to add new routers, services, utilities.
- Constants and mappings are separated into dedicated files for easy maintenance.
- Support for multiple marketplaces (vente-unique, Lutz).

## Usage

- REST API for all operations (import, errors, management).
- Swagger UI (`/docs`) for interactive testing.
- Request examples — see `README.md`.

## Tests

- Tests are located in `tests/unit/` and `tests/integration/`.

## Quick Workflow

1. User authenticates.
2. Imports products (by EAN, list, by fabric_id).
3. Service fetches data from Afterbuy, transforms, generates CSV, processes images.
4. Imports products to Mirakl/Lutz, returns status and errors.
5. All actions are logged.

## Deployment
- Requires Python 3.11+
- Environment setup via `.env` and `uv`
- Can be run with `uv run uvicorn src.main:app`

For details on endpoint usage and setup, see the main README.md and API documentation.
