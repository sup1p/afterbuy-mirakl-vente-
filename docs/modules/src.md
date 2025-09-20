# src Module (Root)

This directory contains the main application entry point, shared resources, and data schemas. Each file is essential for application startup, resource management, and data validation.

## main.py
FastAPI application entry point.
- **Application Lifecycle:** Manages startup and shutdown events, including HTTP client initialization.
- **Router Registration:** Includes all API routers for product, Mirakl system, and test endpoints.
- **Health Check:** Implements a root endpoint (`/`) for service status verification.
- **Example:**
  ```python
  @app.get("/")
  def root():
      return {"status": "ok"}
  ```

## resources.py
Manages shared resources such as HTTP client instances for dependency injection.
- **Global Resource Management:** Ensures HTTP clients and other resources are available for endpoints.
- **Example:**
  - `resources.client`: Global HTTP client instance.

## schemas.py
Defines Pydantic models and data schemas for request/response validation across API endpoints.
- **Example:**
  - `class ProductEan(BaseModel)`: Model for a list of EANs for batch import.
  - `class TestImageResize(BaseModel)`: Model for image resize requests.