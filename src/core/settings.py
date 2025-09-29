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
    mirakl_url_vente: str
    mirakl_api_key_vente: str
    mirakl_shop_id_vente: int
    mirakl_connect_vente: str
    
    mirakl_url_lutz: str
    mirakl_price_url_lutz: str
    mirakl_api_key_lutz: str
    shop_id_lutz: int
    
    # === lawyer typ shi Lutz ===
    distributor_name_lutz: str
    distributor_street_lutz: str
    distributor_zip_lutz: int
    distributor_city_lutz: str
    distributor_country_lutz: str
    
    # FTP server configuration
    ftp_host: str
    ftp_port: int
    ftp_user: str
    ftp_password: str
    ftp_base_dir: str
    
    remove_bg_url: str
    remove_bg_api_key: str
    
    # Application behavior settings
    check_image_existence: bool = False
    use_real_html_desc: bool = False
    use_ean_validator: bool = True  
    special_quantity_word: str
    min_image_height: int
    min_image_width: int
    max_description_chars: int
    
    enable_image_resize_lutz: bool = True
    
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
    admin_username: str
    admin_password: str

    model_config = SettingsConfigDict(
        env_file=".env",
    )


# Global settings instance
settings = Settings()
