"""
Global resource management module.
Stores shared HTTP and FTP client instances for the application.
"""
import asyncio
from typing import Optional

import httpx
from pydantic_ai import Agent
from openai import AsyncOpenAI 
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIChatModel

# Global HTTP client instance for API calls
client: httpx.AsyncClient | None = None

# LLM ресурсы (инициализируются при стартапе приложения)
openai_client: Optional[AsyncOpenAI] = None
llm_agent: Optional[Agent] = None

# семафор для ограничения одновременных вызовов к LLM
llm_semaphore: Optional[asyncio.Semaphore] = None
ftp_semaphore: Optional[asyncio.Semaphore] = None