from src.core.settings import settings
from pydantic import BaseModel, Field

class ProductDescriptionAIVente(BaseModel):
    description_de: str = Field(..., description=f"Clean, solid product descrition in human language for marketplace in German, maximum {settings.max_description_chars} characters, minimum 100 characters")
    description_fr: str = Field(..., description=f"Clean, solid product descrition in human language for marketplace in French, maximum {settings.max_description_chars} characters, minimum 100 characters")
    
class ProductDescriptionAILutz(BaseModel):
    description_de: str = Field(..., description=f"Clean, solid product descrition in human language for marketplace in German, maximum {settings.max_description_chars} characters, minimum 100 characters")
    description_en: str = Field(..., description=f"Clean, solid product descrition in human language for marketplace in English, maximum {settings.max_description_chars} characters, minimum 100 characters")