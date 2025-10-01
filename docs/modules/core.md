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
- **Database Session:** Provides a managed database connection for each request.
- **Checking user authentication:** Verifies that the user is logged in.
- **Checking user auth level:** Checks user’s access rights.
- **Initilizing LLM agent:** Prepares the AI agent for handling requests.
- **Example function:**
  - `async def get_httpx_client()`: Returns a global HTTP client instance for use in endpoints.