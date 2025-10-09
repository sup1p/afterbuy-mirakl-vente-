"""
Модуль конфигурации настроек приложения.
Управляет переменными окружения и конфигурацией приложения с использованием Pydantic.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()


class Settings(BaseSettings):
    """
    Класс настроек приложения.
    Управляет всеми параметрами конфигурации для коннектора Mirakl-Afterbuy.
    """

    # Общие настройки проекта
    PROJECT_NAME: str = "mirakl - afterbuy connector"  # Название проекта
    DEBUG: bool = False  # Режим отладки

    # Настройки API Afterbuy
    afterbuy_url: str  # URL для подключения к API Afterbuy
    afterbuy_login: str  # Логин для аутентификации в Afterbuy
    afterbuy_password: str  # Пароль для аутентификации в Afterbuy
    image_base_url: str  # Базовый URL для изображений из Afterbuy

    # Настройки API Mirakl для vente
    mirakl_url_vente: str  # URL API Mirakl для платформы vente-unique
    mirakl_api_key_vente: str  # API-ключ для аутентификации в Mirakl vente
    mirakl_shop_id_vente: int  # ID магазина в Mirakl для vente
    mirakl_connect_vente: str  # Строка подключения для Mirakl vente

    # Настройки API Mirakl для Lutz
    mirakl_url_lutz: str  # URL API Mirakl для платформы Lutz
    mirakl_price_url_lutz: str  # URL для загрузки цен в Mirakl Lutz
    mirakl_api_key_lutz: str  # API-ключ для аутентификации в Mirakl Lutz
    shop_id_lutz: int  # ID магазина в Mirakl для Lutz

    # Информация о дистрибьюторе для Lutz (юридические данные)
    distributor_name_lutz: str  # Название дистрибьютора
    distributor_street_lutz: str  # Улица дистрибьютора
    distributor_zip_lutz: int  # Почтовый индекс дистрибьютора
    distributor_city_lutz: str  # Город дистрибьютора
    distributor_country_lutz: str  # Страна дистрибьютора

    # Настройки FTP-сервера для загрузки данных
    ftp_host: str  # Хост FTP-сервера
    ftp_port: int  # Порт FTP-сервера
    ftp_user: str  # Пользователь FTP
    ftp_password: str  # Пароль FTP
    ftp_base_dir: str  # Базовая директория на FTP

    # Настройки для удаления фона изображений
    remove_bg_url: str  # URL сервиса для удаления фона
    remove_bg_api_key: str  # API-ключ для сервиса удаления фона

    # Настройки поведения приложения
    use_image_bg_remover: bool = False  # Включить удаление фона изображений
    use_ai_description_generator: bool = False  # Включить генерацию описаний с помощью ИИ

    # Специальные слова и ограничения
    special_quantity_word: str  # Специальное слово для количества товаров

    # Ограничения на изображения
    min_image_height: int  # Минимальная высота изображения
    min_image_width: int  # Минимальная ширина изображения
    max_description_chars: int  # Максимальное количество символов в описании

    # Специфичные настройки для Lutz
    enable_image_resize_lutz: bool = True  # Включить изменение размера изображений для Lutz

    # Настройки безопасности (JWT-токены)
    secret_key: str  # Секретный ключ для подписи JWT
    algorithm: str  # Алгоритм шифрования JWT
    access_token_expire_minutes: int  # Время жизни access-токена в минутах
    refresh_token_expire_days: int  # Время жизни refresh-токена в днях

    # Настройки ИИ (LLM)
    llm_model: str  # Модель LLM для генерации текста
    openai_api_key: str  # API-ключ OpenAI

    # Настройки базы данных PostgreSQL
    postgres_user: str  # Пользователь базы данных
    postgres_password: str  # Пароль базы данных
    postgres_db: str  # Название базы данных
    db_host: str  # Хост базы данных
    db_port: int  # Порт базы данных
    database_url: str  # Полный URL подключения к базе данных
    admin_username: str  # Имя администратора
    admin_password: str  # Пароль администратора

    # Конфигурация Pydantic для загрузки из .env файла
    model_config = SettingsConfigDict(
        env_file=".env",
    )


# Глобальный экземпляр настроек
settings = Settings()
