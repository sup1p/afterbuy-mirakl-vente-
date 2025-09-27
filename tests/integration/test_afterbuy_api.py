import pytest
import httpx
from src.services.vente_services.afterbuy_api_calls import get_access_token, get_product_data, get_products_by_fabric

pytest_plugins = "pytest_asyncio"

@pytest.mark.asyncio
async def test_get_access_token():
    async with httpx.AsyncClient() as client:
        token = await get_access_token(client)
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        
        
@pytest.mark.asyncio
async def test_get_product_data_integration():
    """
    Интеграционный тест функции get_product_data с реальным запросом к Afterbuy.
    Требует корректных логина, пароля и доступного сервиса.
    """

    async with httpx.AsyncClient() as client:
        ean = 4069424997217
        product = await get_product_data(ean=ean, httpx_client=client)

        # Проверки структуры возвращаемого объекта
        assert isinstance(product, dict)
        assert "id" in product
        assert "ean" in product
        assert product["ean"] == str(ean)
        assert "html_description" in product
        assert product["html_description"].startswith("<!DOCTYPE html>")
            
@pytest.mark.asyncio
async def test_get_products_by_fabric_integration():
    """
    Интеграционный тест функции get_products_by_fabric.
    Проверяет полный цикл получения продуктов по fabric_id с Afterbuy API.
    Требует реальных рабочих credentials и доступного сервиса Afterbuy.
    """

    async with httpx.AsyncClient() as client:
        # Реальный fabric_id для теста
        afterbuy_fabric_id = 500490

        # Получение данных
        result = await get_products_by_fabric(afterbuy_fabric_id, httpx_client=client)

        # Проверяем структуру возвращаемого объекта
        assert isinstance(result, dict), "Результат должен быть словарём"
        assert "products" in result, "Отсутствует ключ 'products'"
        assert "not_added_eans" in result, "Отсутствует ключ 'not_added_eans'"
        assert isinstance(result["products"], list), "'products' должен быть списком"
        assert isinstance(result["not_added_eans"], list), "'not_added_eans' должен быть списком"

        # Если есть продукты — проверяем обязательные поля
        if result["products"]:
            product = result["products"][0]
            assert "id" in product, "Отсутствует ключ 'id' в первом продукте"
            assert "ean" in product, "Отсутствует ключ 'ean' в первом продукте"
            assert "html_description" in product, "Отсутствует ключ 'html_description' в первом продукте"
