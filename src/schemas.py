from pydantic import BaseModel, Field
from typing import List, Union, Optional, Dict

class ProductEan(BaseModel):
    ean_list: List[str]

class TestImageResize(BaseModel):
    url: str
    ean: str
    
class MappedProduct(BaseModel):
    sku: Union[int,str]
    product_id: str | int = Field(..., alias="product-id")
    product_id_type: str = Field(..., alias="product-id-type")
    price: float
    state: int
    quantity: int
    brand: Optional[str] = ""
    internal_description: Optional[str] = Field(None, alias="internal-description")
    title_de: str
    image_1: str
    image_2: Optional[str] = ""
    image_3: Optional[str] = ""
    image_4: Optional[str] = ""
    image_5: Optional[str] = ""
    image_6: Optional[str] = ""
    image_7: Optional[str] = ""
    image_8: Optional[str] = ""
    image_9: Optional[str] = ""
    image_10: Optional[str] = ""
    category: Union[str, int]
    ean: Union[str, int]
    description: str
    description_de: str
    
    # все остальные динамические поля
    extra_attrs: Optional[Dict[str, Union[str, int, float]]] = {}

    class Config:
        validate_by_name = True
        extra = "allow"  # позволяет Pydantic принимать любые дополнительные поля
        
class FabricMappedProducts(BaseModel):
    not_added_eans: List[str]
    total_not_added: int
    total_eans_in_fabric: int
    data_for_csv_by_fabric: List[MappedProduct]

    class Config:
        validate_by_name = True
    
class ProductResult(BaseModel):
    import_id: int
    product_import_id: int

class MiraklImportResponse(BaseModel):
    status: str
    results: List[Dict[str, ProductResult]]

class ImportManyEanResponse(BaseModel):
    mirakl_response: MiraklImportResponse
    not_added_eans: List[str]
    total_not_added: int

class ImportFabricProductsResponse(BaseModel):
    mirakl_response: MiraklImportResponse
    not_added_eans: List[str]
    total_not_added: int
    total_eans_in_fabric: int