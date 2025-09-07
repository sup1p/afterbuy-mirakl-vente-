from pydantic import BaseModel
from typing import List

class ProductEan(BaseModel):
    ean_list: List[int]
    
class ProductId(BaseModel):
    product_id_list: List[int]