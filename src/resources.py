"""
Global resource management module.
Stores shared HTTP and FTP client instances for the application.
"""

import httpx
import aioftp

# Global HTTP client instance for API calls
client: httpx.AsyncClient | None = None


