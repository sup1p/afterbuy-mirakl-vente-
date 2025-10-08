from pydantic import BaseModel, Field
from typing import List, Union, Optional, Dict, Literal

class ProductRequest(BaseModel): # lutz
    product_id: str

class FabricRequest(BaseModel): # lutz
    fabric_id: int

class EansWithDeliveryRequest(BaseModel):
    ean_list: List[str]
    delivery_days: int


class FabricWithDeliveryRequest(BaseModel):
    afterbuy_fabric_id: int
    delivery_days: int
    
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
    

    class Config:
        validate_by_name = True
        extra = "allow"  # позволяет Pydantic принимать любые дополнительные поля
        
class FabricMappedProducts(BaseModel):
    not_added_eans: List[str]
    total_not_added: int
    fabric_name: str
    delivery_days: int
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
    mirakl_answer: MiraklImportResponse
    not_added_eans: List[str]
    total_not_added: int
    delivery_days: str
    total_eans_in_fabric: int
    

# crud

class FabricWithDeliveryAndMarketRequest(BaseModel):
    afterbuy_fabric_id: int
    delivery_days: int
    market: Literal["xl", "jv"]

class saveUploadedFabric(BaseModel):
    afterbuy_fabric_id: int
    status: Literal["pending", "processed", "error"] = "pending"
    market: Literal["xl", "jv"] 
    user_id: int

class saveUploadedEan(BaseModel):
    ean: str
    afterbuy_fabric_id: int
    title: str
    image_1: str
    image_2: Optional[str] = ""
    image_3: Optional[str] = ""
    user_id: int
    uploaded_fabric_id: int
    status: Literal["pending", "processed", "error"] = "pending"
    
class eansByFabricRequest(BaseModel):
    afterbuy_fabric_id: int

class fabricsByStatusRequest(BaseModel):
    status: Literal["pending", "processed", "error"]
    
class eansByStatusRequest(BaseModel):
    afterbuy_fabric_id: int
    status: Literal["pending", "processed", "error"]
    
class fabricsByUserRequest(BaseModel):
    user_id: int

class changeEanStatusRequest(BaseModel):
    id: int
    new_status: Literal["pending", "processed", "error"]
    
class changeFabricStatusRequest(BaseModel):
    afterbuy_fabric_id: int
    new_status: Literal["pending", "processed", "error"]
    
class fabricsByMarketPlaceRequest(BaseModel):
    marketplace: Literal["xl", "jv"]  # xxxlutz, venteunique