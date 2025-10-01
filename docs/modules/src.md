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

Module for managing global shared resources used across the application.  
Provides centralized initialization and access to HTTP clients and LLM-related objects.

- **Global Resource Management:**  
  Central place to create and reuse shared objects instead of instantiating them per request.  

- **Shared Resources:**  
  - `client`: Global `httpx.AsyncClient` for making external API calls (reused to avoid overhead).  
  - `openai_client`: Global `AsyncOpenAI` instance, initialized on application startup.  
  - `llm_agent`: `pydantic_ai.Agent` for handling LLM requests.  
  - `llm_semaphore`: `asyncio.Semaphore` to control concurrency of simultaneous LLM calls.  

- **Usage:**  
  Import resources where needed and ensure proper initialization/cleanup during application startup/shutdown.