# XXLmebel 1 API

## Project Overview
XXLmebel 1 API is a backend service built with FastAPI that acts as a connector between the Afterbuy and Mirakl platforms. It provides endpoints for product data retrieval, CSV generation, and integration error checking, facilitating automated product management and synchronization between e-commerce systems.

## Features
- RESTful API built with FastAPI
- Product data retrieval from Afterbuy
- Product data mapping and CSV export
- Mirakl platform integration and error reporting
- Logging with rotation and persistent log files

## Requirements
- Python 3.11 or higher

## Installation
1. Clone the repository:
   ```bash
   git clone <repository_url>
   cd xxlmebel_1_api
   ```
2. Create and activate a virtual environment:
   ```bash
   python3.13 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies using uv:
   ```bash
   uv sync
   ```
   Alternatively, if using PEP 621/pyproject.toml:
   ```bash
   uv pip install .
   ```
4. Configure environment variables:
   - Copy `.env` file and set the required credentials for Afterbuy and Mirakl platforms.

## Usage
1. Run the API server:
   ```bash
   uv run uvicorn src.main:app
   ```
2. Access the API:
   - The root endpoint (`/`) returns a live status.
   - Product and Mirakl-related endpoints are available under `/create_big_csv`, `/import-product-error/{import_parameter}`, `/mirakl-platform-settings`, and `/mirakl-product-non-integrated/{import_parameter}`.
3. Logging:
   - Logs are stored in `logs/logs.log` with rotation enabled.

## Project Structure
- `src/` - Main application code
  - `main.py` - FastAPI application entry point
  - `routers/` - API route definitions
  - `services/` - Business logic and integrations
  - `core/` - Application settings
  - `const/` - Constants and attribute mappings
  - `utils/` - Utility functions
- `logs/` - Logging configuration and log files
- `.env` - Environment variables for credentials and API keys

## Additional Notes
- Ensure all required environment variables are set in `.env` before launching the application.
- For production deployments, configure proper security and access controls.
