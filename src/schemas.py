from pydantic import BaseModel
from typing import List

class ProductEan(BaseModel):
    ean_list: List[str]

class TestImageResize(BaseModel):
    url: str
    ean: str