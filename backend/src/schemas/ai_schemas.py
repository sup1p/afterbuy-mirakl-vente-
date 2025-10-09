from src.core.settings import settings
from pydantic import BaseModel, Field

# Схема для описаний продуктов, генерируемых AI для магазина Vente
class ProductDescriptionAIVente(BaseModel):
    # Описание продукта на немецком языке для маркетплейса
    description_de: str = Field(..., description=f"Clean, solid product descrition in human language for marketplace in German, maximum {settings.max_description_chars} characters, minimum 100 characters")
    # Описание продукта на французском языке для маркетплейса
    description_fr: str = Field(..., description=f"Clean, solid product descrition in human language for marketplace in French, maximum {settings.max_description_chars} characters, minimum 100 characters")
    
# Схема для описаний продуктов, генерируемых AI для магазина Lutz
class ProductDescriptionAILutz(BaseModel):
    # Описание продукта на немецком языке для маркетплейса
    description_de: str = Field(..., description=f"Clean, solid product descrition in human language for marketplace in German, maximum {settings.max_description_chars} characters, minimum 100 characters")
    # Описание продукта на английском языке для маркетплейса
    description_en: str = Field(..., description=f"Clean, solid product descrition in human language for marketplace in English, maximum {settings.max_description_chars} characters, minimum 100 characters")