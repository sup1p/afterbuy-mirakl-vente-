# Документация по Схемам

Эта папка определяет **Pydantic-схемы**, используемые в приложении для валидации, сериализации и документации API.  
Схемы сгруппированы по доменам (`ai_schemas.py`, `product_schemas.py`, `user_schemas.py`).

---

## ai_schemas.py

Схемы для AI-генерации описаний продуктов.

- **ProductDescriptionAIVente**
  - `description_de` *(str)* – Чистое описание продукта на **немецком**, длина: 100 – `settings.max_description_chars`.  
  - `description_fr` *(str)* – Чистое описание продукта на **французском**, длина: 100 – `settings.max_description_chars`.  

- **ProductDescriptionAILutz**
  - `description_de` *(str)* – Чистое описание продукта на **немецком**, длина: 100 – `settings.max_description_chars`.  
  - `description_en` *(str)* – Чистое описание продукта на **английском**, длина: 100 – `settings.max_description_chars`.  

---

## product_schemas.py

Схемы для обработки запросов, сопоставлений и результатов импорта продуктов.

### Схемы Запросов
- **ProductRequest**
  - `product_id` *(str)* – Идентификатор продукта (Lutz).  

- **FabricRequest**
  - `fabric_id` *(int)* – Идентификатор ткани (Lutz).  

- **EansWithDeliveryRequest**
  - `ean_list` *(List[str])* – Список EAN кодов продуктов.  
  - `delivery_days` *(int)* – Время доставки в днях.  

- **FabricWithDeliveryRequest**
  - `afterbuy_fabric_id` *(int)* – ID ткани в системе Afterbuy.  
  - `delivery_days` *(int)* – Время доставки в днях.  

- **TestImageResize**
  - `url` *(str)* – URL изображения для изменения размера.  
  - `ean` *(str)* – EAN продукта для ссылки.  

### Схемы Сопоставления Продуктов
- **MappedProduct**
  Представляет сопоставленный продукт, готовый для экспорта/импорта.  
  - `sku` *(int | str)* – SKU продукта.  
  - `product_id` *(str | int, alias: "product-id")* – Внешний идентификатор продукта.  
  - `product_id_type` *(str, alias: "product-id-type")* – Тип идентификатора.  
  - `price` *(float)* – Цена продукта.  
  - `state` *(int)* – Код состояния продукта.  
  - `quantity` *(int)* – Доступное количество.  
  - `brand` *(Optional[str])* – Название бренда (по умолчанию: "").  
  - `internal_description` *(Optional[str], alias: "internal-description")* – Внутреннее описание.  
  - `title_de` *(str)* – Название продукта на немецком.  
  - `image_1` … `image_10` *(str, optional)* – Изображения продукта (основное и дополнительные).  
  - `category` *(str | int)* – Категория продукта.  
  - `ean` *(str | int)* – EAN продукта.  
  - `description` *(str)* – Описание продукта.  
  - `description_de` *(str)* – Описание продукта на немецком.  

- **FabricMappedProducts**
  Сводный ответ для сопоставленных продуктов ткани.  
  - `not_added_eans` *(List[str])* – EAN, которые не были добавлены.  
  - `total_not_added` *(int)* – Количество не добавленных продуктов.  
  - `fabric_name` *(str)* – Название ткани.  
  - `delivery_days` *(int)* – Дни доставки.  
  - `total_eans_in_fabric` *(int)* – Общее количество EAN в этой ткани.  
  - `data_for_csv_by_fabric` *(List[MappedProduct])* – Данные, подготовленные для экспорта в CSV.  

### Схемы Ответов на Импорт
- **ProductResult**
  - `import_id` *(int)* – Идентификатор импорта.  
  - `product_import_id` *(int)* – Идентификатор импортированного продукта.  

- **MiraklImportResponse**
  - `status` *(str)* – Статус импорта.  
  - `results` *(List[Dict[str, ProductResult]])* – Результаты импорта, сгруппированные по продуктам.  

- **ImportManyEanResponse**
  - `mirakl_response` *(MiraklImportResponse)* – Ответ от Mirakl.  
  - `not_added_eans` *(List[str])* – EAN, которые не были добавлены.  
  - `total_not_added` *(int)* – Количество не добавленных продуктов.  

- **ImportFabricProductsResponse**
  - `mirakl_response` *(MiraklImportResponse)* – Ответ от Mirakl.  
  - `not_added_eans` *(List[str])* – EAN, которые не были добавлены.  
  - `total_not_added` *(int)* – Количество не добавленных продуктов.  
  - `total_eans_in_fabric` *(int)* – Общее количество EAN в ткани.  

---

## user_schemas.py

Схемы для управления пользователями и аутентификации.

- **UserCreate**
  - `username` *(str)* – Логин нового пользователя.  
  - `password` *(str)* – Пароль нового пользователя.  

- **UserUpdate**
  - `username` *(Optional[str])* – Новое имя пользователя.  
  - `password` *(Optional[str])* – Новый пароль.  

- **UserOut**
  - `id` *(int)* – ID пользователя.  
  - `username` *(str)* – Имя пользователя.  
  - `is_admin` *(bool)* – Является ли пользователь администратором.  
  - Config: `from_attributes = True` → Позволяет создание из ORM объектов.  

- **Token**
  - `access_token` *(str)* – JWT токен доступа.  
  - `refresh_token` *(str)* – Токен обновления.  
  - `token_type` *(str, default="bearer")* – Тип токена.  

- **RefreshTokenRequest**
  - `refresh_token` *(str)* – Токен обновления.  

---

## Заметки
- Все схемы наследуются от **Pydantic BaseModel**.  
- Используются для **валидации**, **сериализации** и **документации OpenAPI**.  
- Алиасы (например, "product-id") обеспечивают совместимость с внешними API.
