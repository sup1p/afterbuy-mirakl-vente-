# src/core Module

This module provides core configuration and dependency management for the application. Each file is responsible for a specific aspect of application setup and resource management.

## settings.py
Defines application-wide settings and configuration logic.
- **Environment Loading:** Loads credentials, API keys, and runtime parameters from environment variables or `.env` files.
- **Centralized Configuration:** Makes settings available throughout the application for consistent access.
- **Example usage:**
  - `settings.afterbuy_url`: Access Afterbuy API URL from settings.

## dependencies.py
Implements dependency injection for FastAPI endpoints.
- **HTTP Client Management:** Provides shared HTTP client instances for API calls.
- **Resource Initialization:** Ensures resources are properly initialized and available for endpoints.
- **Example function:**
  - `async def get_httpx_client()`: Returns a global HTTP client instance for use in endpoints.