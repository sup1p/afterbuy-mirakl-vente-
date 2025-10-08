# XXLmebel 1 API

## Project Description
XXLmebel 1 API is a FastAPI-based backend application designed for automated transfer of large volumes of product data from the Afterbuy platform to the Mirakl (vente-unique) marketplace. The service provides integration, transformation, CSV export, error handling, and logging.

## Purpose
- Automate product transfer between Afterbuy and Mirakl
- Generate and export CSV files for import
- Check integration errors and display status
- Centralized operation logging

## Project Structure
- `src/` — application source code
  - `main.py` — FastAPI entry point
  - `routers/` — API route definitions
  - `services/` — business logic and integrations
  - `core/` — application settings
  - `const/` — constants and attributes
  - `utils/` — utility functions
- `logs/` — logging configuration and log files
- `.env` — environment variables (keys, passwords)
- `pyproject.toml`, `uv.lock` — dependencies and build configuration
- `product_samples.json` — sample product data

## Installation and Launch
### Requirements
- Python >= 3.11
- [uv](https://github.com/astral-sh/uv) utility for dependency management

### Installation Steps
1. Clone the repository:
   ```bash
   git clone <repository_url>
   cd xxlmebel_1_api
   ```
2. Create and activate a virtual environment:
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   uv sync
   ```
   Or using PEP 621/pyproject.toml:
   ```bash
   uv pip install .
   ```
4. Copy the `.env` file and specify the required parameters for Afterbuy and Mirakl.

5. Add the fabric_id.json

### Server Launch
```bash
uv run uvicorn src.main:app
```

## Usage Examples
### 1. Check server status
```bash
curl http://localhost:8000/
```
Response:
```json
{"status": "ok"}
```

### 2. Import large CSV based on fabric id
```bash
curl -X POST http://localhost:8000/import-products-by-fabric/{fabric_id}
```

### 3. Get import errors
```bash
curl http://localhost:8000/import-product-error/{import_parameter}
```

### 4. Get Mirakl platform settings
```bash
curl http://localhost:8000/mirakl-platform-settings
```

### 5. Swagger UI
For interactive API testing, open in your browser:
```
http://localhost:8000/docs
```

## Additional Notes
- All environment variables must be correctly specified in `.env` before starting the application.
- For production deployments, it is recommended to configure security and access control.
- Operation logs are saved in `logs/logs.log` with rotation enabled.

## Contacts
For technical questions and support, contact the project developer.
