# Router API

## Endpoints mirakl system


### 1. Get Product Import Error
**`GET /import-product-error/{import_parameter}`**

Checks if there are errors for a given product import parameter.

#### Parameters
- `import_parameter` *(string, path)* — The import parameter provided by Mirakl when the product was imported.

#### Example Request
```bash
curl -X GET "http://<host>/import-product-error/12345"
```

#### Responses
- **200 OK**
```json
{
  "message": { ... } // Mirakl response
}
```
- **404 Not Found**
```json
{
  "detail": "Not found"
}
```
- **500 Internal Server Error** — Processing error.

---

### 2. Get Mirakl Platform Settings
**`GET /mirakl-platform-settings`**

Returns all platform settings available from Mirakl API.

#### Example Request
```bash
curl -X GET "http://<host>/mirakl-platform-settings"
```

#### Responses
- **200 OK**
```json
{
  "setting1": "...",
  "setting2": "..."
}
```
- **500 Internal Server Error** — Processing error.

---

### 3. Get Non-Integrated Products
**`GET /mirakl-product-non-integrated/{import_parameter}`**

Fetches products that were not integrated in Mirakl for the given import parameter.

#### Parameters
- `import_parameter` *(string, path)* — The import parameter provided by Mirakl when the product was imported.

#### Example Request
```bash
curl -X GET "http://<host>/mirakl-product-non-integrated/12345"
```

#### Responses
- **200 OK**
```json
{
  "message": { ... } // List of non-integrated products
}
```
- **404 Not Found**
```json
{
  "detail": "Not found"
}
```
- **500 Internal Server Error** — Processing error.

---

### 4. Get Offer Import Error
**`GET /mirakl-offer-import-error/{import_parameter}`**

Checks if there are errors for a given offer import parameter.

#### Parameters
- `import_parameter` *(string, path)* — The import parameter provided by Mirakl when the offer was imported.

#### Example Request
```bash
curl -X GET "http://<host>/mirakl-offer-import-error/12345"
```

#### Responses
- **200 OK**
```json
{
  "message": { ... } // Mirakl response
}
```
- **404 Not Found**
```json
{
  "detail": "Not found"
}
```
- **500 Internal Server Error** — Processing error.

---

## Endpoints product

### 1. Import Product by EAN
**`POST /import-product/{ean}`**

Imports a single product from Afterbuy to Mirakl using EAN and optional fabric ID.

#### Parameters
- `ean` *(string, path)* — EAN code of the product to import.
- `afterbuy_fabric_id` *(integer, query, optional)* — Afterbuy fabric ID for more precise product selection.

#### Example Request
```bash
curl -X POST "http://<host>/import-product/1234567890123?afterbuy_fabric_id=1001"
```

#### Responses
- **200 OK**
```json
{
  // Mirakl API response for the imported product
}
```
- **400 Bad Request**
```json
{
  "detail": "Invalid EAN 1234567890123"
}
```
- **404 Not Found**
```json
{
  "detail": "Product with ean 1234567890123 not found or mapping failed"
}
```
- **500 Internal Server Error**
```json
{
  "detail": "Error message"
}
```

---

### 2. Import Multiple Products by EAN List
**`POST /import-products`**

Imports multiple products from Afterbuy to Mirakl using a list of EANs.

#### Request Body
- `ean_list` *(array of strings, required)* — List of EAN codes to import.

#### Example Request
```bash
curl -X POST "http://<host>/import-products" \
  -H "Content-Type: application/json" \
  -d '{"ean_list": ["1234567890123", "9876543210987"]}'
```

#### Responses
- **200 OK**
```json
{
  "mirakl_response": { ... },
  "not_added_eans": ["9876543210987"],
  "total_not_added": 1
}
```
- **400 Bad Request**
```json
{
  "detail": "EAN list is empty"
}
```
- **404 Not Found**
```json
{
  "detail": "Creating big csv failed"
}
```
- **500 Internal Server Error**
```json
{
  "detail": "Error message"
}
```

---

### 3. Import Products by Afterbuy Fabric ID
**`POST /import-products-by-fabric/{afterbuy_fabric_id}`**

Imports all products from Afterbuy to Mirakl for a given fabric ID.

#### Parameters
- `afterbuy_fabric_id` *(integer, path)* — Afterbuy fabric ID to import products from.

#### Example Request
```bash
curl -X POST "http://<host>/import-products-by-fabric/1001"
```

#### Responses
- **200 OK**
```json
{
  "mirakl_answer": { ... },
  "not_added_eans": ["1234567890123"],
  "total_not_added": 1,
  "total_eans_in_fabric": 10,
  "data_for_csv_by_fabric": [ ... ]
}
```
- **404 Not Found**
```json
{
  "detail": "No products found for fabric 1001"
}
```
- **404 Not Found**
```json
{
  "detail": "Creating big csv failed for fabric: 1001"
}
```
- **500 Internal Server Error**
```json
{
  "detail": "Error message"
}
```

---

## Test Endpoints

### 1. Test Import Product by EAN
**`POST /test-import-product/{ean}/`**

Test endpoint for importing a single product by EAN (returns mapped data for Mirakl, does not import).

#### Parameters
- `ean` *(string, path)* — EAN code of the product to test import.
- `afterbuy_fabric_id` *(integer, query, optional)* — Afterbuy fabric ID for more precise product selection.

#### Example Request
```bash
curl -X POST "http://<host>/test-import-product/1234567890123?afterbuy_fabric_id=1001"
```

#### Responses
- **200 OK**
```json
{
  // Mapped product data for Mirakl
}
```
- **400 Bad Request**
```json
{
  "detail": "Invalid EAN 1234567890123"
}
```
- **500 Internal Server Error**
```json
{
  "detail": "Error message"
}
```

---

### 2. Test Import Products by Afterbuy Fabric ID
**`POST /test-import-products-by-fabric/{afterbuy_fabric_id}`**

Test endpoint for importing products by Afterbuy fabric ID (returns mapped data for all products in the fabric, does not import).

#### Parameters
- `afterbuy_fabric_id` *(integer, path)* — Afterbuy fabric ID to test import products from.

#### Example Request
```bash
curl -X POST "http://<host>/test-import-products-by-fabric/1001"
```

#### Responses
- **200 OK**
```json
{
  "not_added_eans": ["1234567890123"],
  "total_not_added": 1,
  "total_eans_in_fabric": 10,
  "data_for_csv_by_fabric": [ ... ]
}
```
- **404 Not Found**
```json
{
  "detail": "No products found for fabric 1001"
}
```
- **404 Not Found**
```json
{
  "detail": "Creating big csv failed for fabric: 1001"
}
```
- **500 Internal Server Error**
```json
{
  "detail": "Error message"
}
```

---

### 3. Test Resize Image
**`POST /test-resize-image`**

Test endpoint for image resizing and FTP upload functionality.

#### Request Body
- `url` *(string, required)* — Image URL to resize and upload.
- `ean` *(string, required)* — EAN code for the image.

#### Example Request
```bash
curl -X POST "http://<host>/test-resize-image" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/image.jpg", "ean": "1234567890123"}'
```

#### Responses
- **200 OK**
```json
{
  // Result of image resize and upload operation
}
```
- **422 Unprocessable Entity**
```json
{
  "detail": "Error message"
}
```

---
