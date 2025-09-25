# src/ai/ai_agent.py
from src import resources
from src.core.settings import settings
import httpx
from openai import AsyncOpenAI
from pydantic_ai import Agent
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIChatModel


def get_agent() -> Agent:
    """
    Возвращает глобальный LLM-агент.
    """
    if resources.llm_agent is None:
        raise RuntimeError("LLM agent not initialized")
    return resources.llm_agent


async def create_agent_with_httpx(
    httpx_client: httpx.AsyncClient,

) -> Agent:
    """
    Создаёт новый агент, используя переданный httpx.AsyncClient.
    """
    resources.openai_client = AsyncOpenAI(api_key=settings.openai_api_key, http_client=httpx_client)
    provider = OpenAIProvider(openai_client=resources.openai_client)
    model = OpenAIChatModel(settings.llm_model, provider=provider)

    # сохраняем в resources, чтобы использовать глобально
    resources.llm_agent = Agent(model)
    return resources.llm_agent
