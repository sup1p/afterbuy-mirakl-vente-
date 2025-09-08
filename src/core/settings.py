from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings."""

    PROJECT_NAME: str = "mirakl - afterbuy connector"
    DEBUG: bool = False

    afterbuy_url: str
    afterbuy_login: str
    afterbuy_password: str
    mirakl_url: str
    mirakl_api_key: str
    mirakl_shop_id: int
    mirakl_connect: str
    check_image_existence: bool = False
    use_real_html_desc: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
    )


settings = Settings()
