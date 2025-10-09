"""
Модуль интеграции с Mirakl API.
Обрабатывает импорт продуктов, проверку ошибок и настройку платформы с помощью Mirakl API.
"""

from src.core.settings import settings
from logs.config_logs import setup_logging

from io import BytesIO
import pandas as pd
import logging
import httpx


setup_logging()
logger = logging.getLogger(__name__)



async def check_offer_import_error(import_parameter: str, httpx_client: httpx.AsyncClient):
    """
    Получает и анализирует отчёт об ошибках импорта предложений в Mirakl.

    Функция запрашивает отчёт об ошибках для конкретного импорта предложений
    и извлекает EAN (если доступны) и связанные сообщения об ошибках.

    Аргументы:
        import_parameter (str): Идентификатор импорта, предоставленный Mirakl.
        httpx_client (httpx.AsyncClient): Асинхронный HTTP-клиент.

    Возвращает:
        dict: Словарь с ключами:
            - status (int): HTTP-подобный индикатор статуса.
            - ean (list[str] | None): Список EAN, извлечённых из отчёта (если доступны).
            - errors (list[str] | None): Список сообщений об ошибках (если доступны).
            - message (str, optional): Возвращается, если ошибки не найдены или при сбое.

    Исключения:
        Exception: Если запрос к Mirakl завершился ошибкой.
    """
    # Логируем начало проверки ошибок импорта
    logger.info(f"Проверка ошибок импорта предложений для параметра: {import_parameter}")

    headers = {
        "Authorization": settings.mirakl_api_key_vente,
    }
    url = f"{settings.mirakl_url_vente}/api/offers/imports/{import_parameter}/error_report"

    try:
        # Выполняем запрос к API Mirakl
        response = await httpx_client.get(url, headers=headers, timeout=40.0)
    except Exception as e:
        # Логируем исключение, если запрос завершился ошибкой
        logger.error(f"Ошибка при запросе отчёта об ошибках импорта предложений: {e}")
        raise Exception("Ошибка при запросе отчёта об ошибках импорта предложений в Mirakl") from e

    if response.status_code == 200:
        df = pd.read_csv(BytesIO(response.content), sep=";")
        logger.info(f"Отчёт об ошибках предложений успешно получен: {import_parameter}")

        # Извлекаем EAN (из product-id, если product-id-type == 'EAN')
        eans = None
        if "product-id" in df.columns and "product-id-type" in df.columns:
            eans_list = (
                df.loc[df["product-id-type"].str.upper() == "EAN", "product-id"]
                .dropna()
                .astype(str)
                .tolist()
            )
            eans = eans_list if eans_list else None
            logger.debug(f"EAN для {import_parameter}: {eans}")

        # Извлекаем ошибки
        errors = None
        if "error-message" in df.columns:
            errors_list = df["error-message"].dropna().astype(str).tolist()
            errors = errors_list if errors_list else None
            logger.info(f"Ошибки для {import_parameter}: {errors}")

        return {"status": 200, "ean": eans, "errors": errors}

    elif response.status_code == 404:
        # Логируем, если отчёт об ошибках не найден
        logger.debug(f"Ответ: {response.status_code} - {response.text}")
        return {"status": 200, "message": "Не найдено, вероятно, нет ошибок"}

    else:
        # Логируем другие ошибки
        logger.error(f"Ошибка: {response.status_code} - {response.text}")
        try:
            error_json = response.json()
        except Exception:
            error_json = {"message": response.text}
        return {"status": response.status_code, "message": error_json.get("message", "Неизвестная ошибка")}


async def check_import_error(import_parameter: str, httpx_client: httpx.AsyncClient):
    """
    Проверяет ошибки импорта продуктов в системе Mirakl.
    Возвращает EAN, ошибки и предупреждения из отчёта об ошибках трансформации.
    """
    # Логируем начало проверки ошибок импорта продуктов
    logger.info(f"Проверка ошибок импорта для параметра: {import_parameter}")

    headers = {
        "Authorization": settings.mirakl_api_key_vente,
    }
    url = (
        f"{settings.mirakl_url_vente}/api/products/imports/"
        + import_parameter
        + "/transformation_error_report"
    )

    try:
        # Выполняем запрос к API Mirakl
        response = await httpx_client.get(url, headers=headers, timeout=40.0)
    except Exception as e:
        # Логируем исключение, если запрос завершился ошибкой
        logger.error(f"Ошибка при запросе отчёта об ошибках импорта: {e}")
        raise e("Ошибка при запросе отчёта об ошибках импорта из Mirakl")

    if response.status_code == 200:
        df = pd.read_csv(
            BytesIO(response.content), sep=";"
        )  
        
        logger.info(f"Отчёт об ошибках успешно получен: {import_parameter}")

        errors = None
        warnings = None
        if "errors" in df.columns:
            errors_list = df["errors"].dropna().tolist()
            errors = errors_list if errors_list else None
            logger.info(f"Ошибки для {import_parameter}: \n{errors}")
            
        if "warnings" in df.columns:
            warnings_list = df["warnings"].dropna().tolist()
            warnings = warnings_list if warnings_list else None
            logger.info(f"Предупреждения для {import_parameter}: \n{warnings}")

        if "ean" in df.columns:
            eans_list = df["ean"].dropna().tolist()
            eans = eans_list if eans_list else None
            logger.debug(f"EAN для {import_parameter}: \n{eans}")
            
        return {"status": 200, "ean": eans, "errors": errors, "warnings": warnings}
    
    elif response.status_code == 404:
        # Логируем, если отчёт об ошибках не найден
        logger.debug(f"Ответ: {response.status_code} - {response.text}")
            
        return {"status": 200, "message": "Не найдено, вероятно, нет ошибок/предупреждений"}
    
    else:
        # Логируем другие ошибки
        logger.error(f"Ошибка: {response.status_code} - {response.text}")
        try:
            error_json = response.json()
        except Exception:
            error_json = {"message": response.text}
            
        return {"status": response.status_code, "message": error_json.get("message", "Неизвестная ошибка")}


async def check_non_integrated_products(import_parameter: str, httpx_client: httpx.AsyncClient):
    """
    Получает и анализирует отчёт об ошибках для неинтегрированных продуктов в Mirakl.

    Функция проверяет продукты, которые не были успешно интегрированы
    в процессе импорта, и извлекает EAN, ошибки и предупреждения.

    Аргументы:
        import_parameter (str): Идентификатор импорта, предоставленный Mirakl.
        httpx_client (httpx.AsyncClient): Асинхронный HTTP-клиент.

    Возвращает:
        dict: Словарь с ключами:
            - status (int): HTTP-подобный индикатор статуса.
            - ean (list[str] | None): Список EAN (если доступны).
            - errors (list[str] | None): Список сообщений об ошибках (если доступны).
            - warnings (list[str] | None): Список предупреждений (если доступны).
            - message (str, optional): Возвращается, если ошибки/предупреждения не найдены или при сбое.

    Исключения:
        Exception: Если запрос к Mirakl завершился ошибкой.
    """
    # Логируем начало проверки неинтегрированных продуктов
    logger.info(f"Проверка неинтегрированных продуктов для параметра: {import_parameter}")

    headers = {
        "Authorization": settings.mirakl_api_key_vente,
    }
    url = (
        f"{settings.mirakl_url_vente}/api/products/imports/"
        + import_parameter
        + "/error_report"
    )

    try:
        # Выполняем запрос к API Mirakl
        response = await httpx_client.get(url, headers=headers, timeout=40.0)
    except Exception as e:
        # Логируем исключение, если запрос завершился ошибкой
        logger.error(f"Ошибка при запросе неинтегрированных продуктов: {e}")
        raise e("Ошибка при запросе неинтегрированных продуктов из Mirakl")
        

    if response.status_code == 200:
        df = pd.read_csv(
            BytesIO(response.content), sep=";"
        ) 
        
        logger.info(f"Отчёт о неинтегрированных продуктах успешно получен: {import_parameter}")
        
        errors = None
        warnings = None
        if "errors" in df.columns:
            errors_list = df["errors"].dropna().tolist()
            errors = errors_list if errors_list else None
            logger.info(f"Ошибки для {import_parameter}: \n{errors}")
            
        if "warnings" in df.columns:
            warnings_list = df["warnings"].dropna().tolist()
            warnings = warnings_list if warnings_list else None
            logger.info(f"Предупреждения для {import_parameter}: \n{warnings}")
        
        if "ean" in df.columns:
            eans_list = df["ean"].dropna().tolist()
            eans = eans_list if eans_list else None
            logger.debug(f"EAN для {import_parameter}: \n{eans}")
            
        return {"status": 200, "ean": eans, "errors": errors, "warnings": warnings}
    
    elif response.status_code == 404:
        # Логируем, если отчёт об ошибках не найден
        logger.debug(f"Ответ: {response.status_code} - {response.text}")
            
        return {"status": 200, "message": "Не найдено, вероятно, нет ошибок/предупреждений"}
    
    else:
        # Логируем другие ошибки
        logger.error(f"Ошибка: {response.status_code} - {response.text}")
        try:
            error_json = response.json()
        except Exception:
            error_json = {"message": response.text}
        return {"status": response.status_code, "message": error_json.get("message", "Неизвестная ошибка")}


async def check_platform_settings(httpx_client: httpx.AsyncClient):
    """
    Получает настройки конфигурации платформы Mirakl.

    Функция запрашивает данные конфигурации на уровне платформы,
    такие как включённые модули и системные параметры.

    Аргументы:
        httpx_client (httpx.AsyncClient): Асинхронный HTTP-клиент.

    Возвращает:
        dict: JSON-ответ, содержащий конфигурацию платформы.

    Исключения:
        Exception: Если запрос завершился ошибкой или Mirakl вернул некорректные/пустые данные.
    """
    
    logger.info("Проверка настроек платформы Mirakl")
    url = f"{settings.mirakl_url_vente}/api/platform/configuration"

    headers = {
        "Authorization": settings.mirakl_api_key_vente,
        "Accept": "application/json",
    }
    
    try:
        # Выполняем запрос к API Mirakl
        response = await httpx_client.get(url, headers=headers, timeout=40.0)
    except Exception as e:
        # Логируем исключение, если запрос завершился ошибкой
        logger.error(f"Ошибка при запросе настроек платформы Mirakl: {e}")
        raise e("Ошибка при запросе настроек платформы Mirakl")
    
    if response.status_code != 200:
        # Логируем ошибку, если статус ответа не 200
        logger.error(f"Не удалось получить настройки платформы: {response.status_code} - {response.text}")
        raise Exception("Не удалось получить настройки платформы от Mirakl")
    
    data = response.json()
    
    if not data:
        # Логируем ошибку, если данные пустые
        logger.error("Не получены данные при получении настроек платформы")
        raise Exception("Не получены данные при получении настроек платформы от Mirakl")
    
    logger.info("Настройки платформы успешно получены")

    return data


async def import_product(csv_content, httpx_client: httpx.AsyncClient):
    """
    Импортирует данные о продуктах в Mirakl через загрузку CSV.

    Функция отправляет CSV-файл с данными о продуктах в Mirakl API
    и инициирует процесс импорта. Настройки импорта включают обогащение AI
    и параметры перезаписи, а также формат оператора.

    Аргументы:
        csv_content (bytes): Содержимое CSV-файла для загрузки.
        httpx_client (httpx.AsyncClient): Асинхронный HTTP-клиент.

    Возвращает:
        dict: Словарь с ключами:
            - status (str): "done", если запрос выполнен успешно, "error" в противном случае.
            - results (list[dict]): Список результатов или ошибок из процесса импорта.

    Исключения:
        Exception: Не вызывается явно, но сбои запросов регистрируются и возвращаются в результатах.
    """
    
    results = []
    files = {"file": ("products.csv", csv_content, "text/csv")}
    payload = {
        "conversion_options[ai_enrichment][status]": "ENABLED",
        "conversion_options[ai_rewrite][status]": "ENABLED",
        "operator_format": "true",
        "shop": settings.mirakl_shop_id_vente,
        
        "import_mode": "NORMAL",
        "with_products": "true",
    }

    headers = {
        "Authorization": settings.mirakl_api_key_vente,
        "Accept": "application/json",
    }
    
    url = f"{settings.mirakl_url_vente}/api/offers/imports"
    
    try:
        # Выполняем запрос к API Mirakl для импорта продуктов
        response = await httpx_client.post(url=url, data=payload, files=files, headers=headers, timeout=40.0)
    except Exception as exc:
        # Логируем исключение, если запрос завершился ошибкой
        logger.error(f"Ошибка запроса при импорте продукта: {exc}")
        results.append({"product error": str(exc)})
        return {"status": "error", "results": results}

    if response.status_code != 201:
        # Логируем ошибку, если статус ответа не 201
        logger.error(f"Не удалось импортировать продукт: {response.status_code} - {response.text}")
        results.append({"product {product_num} error": response.text})
    else:
        # Логируем успешный импорт
        logger.info(f"Импорт продукта инициирован успешно: {response.json()}")
        results.append({"product {product_num} result": response.json()})

    return {"status": "done", "results": results}