from src import resources
from src.core.settings import settings
import httpx
from openai import AsyncOpenAI
from pydantic_ai import Agent
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIChatModel

# Этот модуль предоставляет функционал для работы с LLM-агентами (Large Language Models).
# Здесь реализованы функции для получения глобального агента и создания нового агента с использованием HTTP-клиента.

def get_agent() -> Agent:
    """
    Возвращает глобальный LLM-агент.

    Если агент не был инициализирован, выбрасывается исключение.

    Возвращает:
        Agent: Глобальный агент.

    Исключения:
        RuntimeError: Если агент не был инициализирован.
    """
    # Проверяем, инициализирован ли глобальный агент
    # Если агент отсутствует, выбрасываем ошибку
    if resources.llm_agent is None:
        raise RuntimeError("LLM agent not initialized")
    return resources.llm_agent

async def create_agent_with_httpx(httpx_client: httpx.AsyncClient) -> Agent:
    """
    Создаёт новый агент, используя переданный httpx.AsyncClient.

    Функция инициализирует клиента OpenAI с использованием переданного HTTP-клиента,
    создаёт провайдера OpenAI и модель, а затем сохраняет агента в глобальных ресурсах.

    Аргументы:
        httpx_client (httpx.AsyncClient): Асинхронный HTTP-клиент для взаимодействия с API.

    Возвращает:
        Agent: Новый агент.
    """
    # Инициализируем клиента OpenAI с использованием переданного HTTP-клиента
    # Создаём провайдера OpenAI и модель
    # Сохраняем агента в глобальных ресурсах для дальнейшего использования
    # Возвращаем созданного агента
    resources.openai_client = AsyncOpenAI(api_key=settings.openai_api_key, http_client=httpx_client)
    provider = OpenAIProvider(openai_client=resources.openai_client)
    model = OpenAIChatModel(settings.llm_model, provider=provider)

    # сохраняем в resources, чтобы использовать глобально
    resources.llm_agent = Agent(model, retries=3, output_retries=3, tools=[]) 
    return resources.llm_agent