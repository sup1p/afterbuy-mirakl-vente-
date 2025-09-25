"""
Application settings configuration module.
Manages environment variables and application configuration using Pydantic.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """
    Application settings class.
    Manages all configuration parameters for the Mirakl-Afterbuy connector.
    """

    PROJECT_NAME: str = "mirakl - afterbuy connector"
    DEBUG: bool = False

    # Afterbuy API configuration
    afterbuy_url: str
    afterbuy_login: str
    afterbuy_password: str
    image_base_url: str
    
    # Mirakl API configuration
    mirakl_url: str
    mirakl_api_key: str
    mirakl_shop_id: int
    mirakl_connect: str
    
    # FTP server configuration
    ftp_host: str
    ftp_port: int
    ftp_user: str
    ftp_password: str
    
    # Application behavior settings
    check_image_existence: bool = False
    use_real_html_desc: bool = False
    use_ean_validator: bool = True  
    special_quantity_word: str
    min_image_height: int
    min_image_width: int
    max_description_chars: int
    
    # Security
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    # AI
    llm_model: str
    openai_api_key: str

    # Database:
    postgres_user: str
    postgres_password: str
    postgres_db: str
    db_host: str
    db_port: int
    database_url: str

    model_config = SettingsConfigDict(
        env_file=".env",
    )


# Global settings instance
settings = Settings()
