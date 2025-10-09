from pydantic import BaseModel, Field
from typing import List, Union, Optional, Dict, Literal

# Запрос для получения продукта по ID (для Lutz)
class ProductRequest(BaseModel):
    product_id: str

# Запрос для получения фабрики по ID (для Lutz)
class FabricRequest(BaseModel):
    fabric_id: int

# Запрос для импорта нескольких EAN с днями доставки
class EansWithDeliveryRequest(BaseModel):
    ean_list: List[str]  # Список EAN кодов для импорта
    delivery_days: int   # Количество дней доставки

# Запрос для импорта продуктов по фабрике с днями доставки
class FabricWithDeliveryRequest(BaseModel):
    afterbuy_fabric_id: int  # ID фабрики в Afterbuy
    delivery_days: int       # Количество дней доставки
    
# Запрос для тестирования изменения размера изображения
class TestImageResize(BaseModel):
    url: str  # URL изображения
    ean: str  # EAN код продукта
    
# Схема для сопоставленного продукта, готового для Mirakl
class MappedProduct(BaseModel):
    sku: Union[int,str]  # SKU продукта
    product_id: str | int = Field(..., alias="product-id")  # ID продукта
    product_id_type: str = Field(..., alias="product-id-type")  # Тип ID продукта
    price: float  # Цена продукта
    state: int    # Состояние продукта
    quantity: int  # Количество на складе
    brand: Optional[str] = ""  # Бренд продукта
    internal_description: Optional[str] = Field(None, alias="internal-description")  # Внутреннее описание
    title_de: str  # Название на немецком
    image_1: str   # Первое изображение
    image_2: Optional[str] = ""  # Второе изображение
    image_3: Optional[str] = ""  # Третье изображение
    image_4: Optional[str] = ""  # Четвертое изображение
    image_5: Optional[str] = ""  # Пятое изображение
    image_6: Optional[str] = ""  # Шестое изображение
    image_7: Optional[str] = ""  # Седьмое изображение
    image_8: Optional[str] = ""  # Восьмое изображение
    image_9: Optional[str] = ""  # Девятое изображение
    image_10: Optional[str] = ""  # Десятое изображение
    category: Union[str, int]  # Категория продукта
    ean: Union[str, int]  # EAN код
    description: str  # Описание продукта
    description_de: str  # Описание на немецком
    

    class Config:
        validate_by_name = True
        extra = "allow"  # Позволяет принимать дополнительные поля
        
# Схема для результатов импорта продуктов по фабрике
class FabricMappedProducts(BaseModel):
    not_added_eans: List[str]  # Список не добавленных EAN
    total_not_added: int       # Общее количество не добавленных
    fabric_name: str           # Название фабрики
    delivery_days: int         # Дни доставки
    total_eans_in_fabric: int  # Общее количество EAN в фабрике
    data_for_csv_by_fabric: List[MappedProduct]  # Данные для CSV по фабрике

    class Config:
        validate_by_name = True
    
# Результат импорта продукта
class ProductResult(BaseModel):
    import_id: int  # ID импорта
    product_import_id: int  # ID импорта продукта

# Ответ от Mirakl на импорт
class MiraklImportResponse(BaseModel):
    status: str  # Статус импорта
    results: List[Dict[str, ProductResult]]  # Результаты импорта

# Ответ на импорт нескольких EAN
class ImportManyEanResponse(BaseModel):
    mirakl_response: MiraklImportResponse  # Ответ от Mirakl
    not_added_eans: List[str]  # Не добавленные EAN
    total_not_added: int  # Общее количество не добавленных

# Ответ на импорт продуктов по фабрике
class ImportFabricProductsResponse(BaseModel):
    mirakl_answer: MiraklImportResponse  # Ответ от Mirakl
    not_added_eans: List[str]  # Не добавленные EAN
    total_not_added: int  # Общее количество не добавленных
    delivery_days: str  # Дни доставки
    total_eans_in_fabric: int  # Общее количество EAN в фабрике
    

# Схемы для CRUD операций

# Запрос для импорта по фабрике с рынком
class FabricWithDeliveryAndMarketRequest(BaseModel):
    afterbuy_fabric_id: int  # ID фабрики в Afterbuy
    delivery_days: int  # Дни доставки
    market: Literal["xl", "jv"]  # Рынок (xl или jv)

# Схема для сохранения загруженной фабрики
class saveUploadedFabric(BaseModel):
    afterbuy_fabric_id: int  # ID фабрики в Afterbuy
    status: Literal["pending", "processed", "error"] = "pending"  # Статус загрузки
    market: Literal["xl", "jv"]  # Рынок
    shop: Literal["vente", "xxxlutz"]  # Магазин
    user_id: int  # ID пользователя

# Схема для сохранения загруженного EAN
class saveUploadedEan(BaseModel):
    ean: str  # EAN код
    afterbuy_fabric_id: int  # ID фабрики в Afterbuy
    title: str  # Название продукта
    image_1: str  # Первое изображение
    image_2: Optional[str] = ""  # Второе изображение
    image_3: Optional[str] = ""  # Третье изображение
    user_id: int  # ID пользователя
    uploaded_fabric_id: int  # ID загруженной фабрики
    status: Literal["pending", "processed", "error"] = "pending"  # Статус
    
# Запрос для получения EAN по фабрике
class eansByFabricRequest(BaseModel):
    afterbuy_fabric_id: int  # ID фабрики в Afterbuy

# Запрос для получения фабрик по статусу
class fabricsByStatusRequest(BaseModel):
    status: Literal["pending", "processed", "error"]  # Статус
    
# Запрос для получения EAN по статусу и фабрике
class eansByStatusRequest(BaseModel):
    afterbuy_fabric_id: int  # ID фабрики в Afterbuy
    status: Literal["pending", "processed", "error"]  # Статус
    
# Запрос для получения фабрик по пользователю
class fabricsByUserRequest(BaseModel):
    user_id: int  # ID пользователя

# Запрос для изменения статуса EAN
class changeEanStatusRequest(BaseModel):
    id: int  # ID записи
    new_status: Literal["pending", "processed", "error"]  # Новый статус
    
# Запрос для изменения статуса фабрики
class changeFabricStatusRequest(BaseModel):
    afterbuy_fabric_id: int  # ID фабрики в Afterbuy
    new_status: Literal["pending", "processed", "error"]  # Новый статус
    
# Запрос для получения фабрик по маркетплейсу
class fabricsByMarketPlaceRequest(BaseModel):
    marketplace: Literal["xl", "jv"]  # Маркетплейс (xl или jv)