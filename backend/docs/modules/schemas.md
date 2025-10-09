# Schemas Documentation

This folder defines **Pydantic schemas** used across the application for validation, serialization, and API documentation.  
Schemas are grouped by domain (`ai_schemas.py`, `product_schemas.py`, `user_schemas.py`).

---

## ai_schemas.py

Schemas for AI-generated product descriptions.

- **ProductDescriptionAIVente**
  - `description_de` *(str)* – Clean product description in **German**, length: 100 – `settings.max_description_chars`.  
  - `description_fr` *(str)* – Clean product description in **French**, length: 100 – `settings.max_description_chars`.  

- **ProductDescriptionAILutz**
  - `description_de` *(str)* – Clean product description in **German**, length: 100 – `settings.max_description_chars`.  
  - `description_en` *(str)* – Clean product description in **English**, length: 100 – `settings.max_description_chars`.  

---

## product_schemas.py

Schemas for handling product-related requests, mappings, and import results.

### Request Schemas
- **ProductRequest**
  - `product_id` *(str)* – Product identifier (Lutz).  

- **FabricRequest**
  - `fabric_id` *(int)* – Fabric identifier (Lutz).  

- **ProductEan**
  - `ean_list` *(List[str])* – List of product EANs.  

- **FabricWithDeliveryRequest**
  - `afterbuy_fabric_id` *(int)* – Fabric ID in Afterbuy system.  
  - `delivery_days` *(int)* – Delivery time in days.  

- **TestImageResize**
  - `url` *(str)* – URL of the image to resize.  
  - `ean` *(str)* – Product EAN for reference.  

### Product Mapping Schemas
- **MappedProduct**
  Represents a mapped product ready for export/import.  
  - `sku` *(int | str)* – Stock keeping unit.  
  - `product_id` *(str | int, alias: "product-id")* – External product identifier.  
  - `product_id_type` *(str, alias: "product-id-type")* – Identifier type.  
  - `price` *(float)* – Product price.  
  - `state` *(int)* – Product state code.  
  - `quantity` *(int)* – Available quantity.  
  - `brand` *(Optional[str])* – Brand name (default: "").  
  - `internal_description` *(Optional[str], alias: "internal-description")* – Internal description.  
  - `title_de` *(str)* – Product title in German.  
  - `image_1` … `image_10` *(str, optional)* – Product images (main and additional).  
  - `category` *(str | int)* – Product category.  
  - `ean` *(str | int)* – Product EAN.  
  - `description` *(str)* – Product description.  
  - `description_de` *(str)* – Product description in German.  

- **FabricMappedProducts**
  Aggregated response for mapped fabric products.  
  - `not_added_eans` *(List[str])* – EANs that were not added.  
  - `total_not_added` *(int)* – Number of not added products.  
  - `fabric_name` *(str)* – Fabric name.  
  - `delivery_days` *(int)* – Delivery days.  
  - `total_eans_in_fabric` *(int)* – Total EANs in this fabric.  
  - `data_for_csv_by_fabric` *(List[MappedProduct])* – Data prepared for CSV export.  

### Import Response Schemas
- **ProductResult**
  - `import_id` *(int)* – Import identifier.  
  - `product_import_id` *(int)* – Imported product identifier.  

- **MiraklImportResponse**
  - `status` *(str)* – Import status.  
  - `results` *(List[Dict[str, ProductResult]])* – Import results grouped by product.  

- **ImportManyEanResponse**
  - `mirakl_response` *(MiraklImportResponse)* – Response from Mirakl.  
  - `not_added_eans` *(List[str])* – EANs that were not added.  
  - `total_not_added` *(int)* – Number of not added products.  

- **ImportFabricProductsResponse**
  - `mirakl_response` *(MiraklImportResponse)* – Response from Mirakl.  
  - `not_added_eans` *(List[str])* – EANs not added.  
  - `total_not_added` *(int)* – Number of not added products.  
  - `total_eans_in_fabric` *(int)* – Total EANs in fabric.  

---

## user_schemas.py

Schemas for user management and authentication.

- **UserCreate**
  - `username` *(str)* – New user’s login.  
  - `password` *(str)* – New user’s password.  

- **UserOut**
  - `id` *(int)* – User ID.  
  - `username` *(str)* – Username.  
  - `is_admin` *(bool)* – Whether the user has admin rights.  
  - Config: `from_attributes = True` → Allows creation from ORM objects.  

- **Token**
  - `access_token` *(str)* – JWT access token.  
  - `token_type` *(str, default="bearer")* – Token type.  

---

## Notes
- All schemas inherit from **Pydantic BaseModel**.  
- Used for **validation**, **serialization**, and **OpenAPI documentation**.  
- Aliases (e.g., `"product-id"`) allow compatibility with external APIs.  
