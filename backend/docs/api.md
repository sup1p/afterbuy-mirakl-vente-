
# API Роутеры

**Все эндпоинты начинаются с префикса `/api`.**

Документация доступна по адресу [`/api/docs`](../api/docs) (Swagger UI) и [`/api/openapi.json`](../api/openapi.json). Интерфейс ReDoc не предоставляется.

# Vente

## Эндпоинты Mirakl

### 1. Получить ошибку импорта продукта
**`GET /import-product-error/{import_parameter}`**

Проверяет, есть ли ошибки для заданного параметра импорта продукта.

#### Параметры
- `import_parameter` *(строка, путь)* — Параметр импорта, предоставленный Mirakl при импорте продукта.

#### Пример запроса
```bash
curl -X GET "http://<host>/import-product-error/12345"
```

#### Ответы
- **200 OK**
```json
{
  "message": { ... } // Ответ от Mirakl
}
```
- **404 Not Found**
```json
{
  "detail": "Not found"
}
```
- **500 Internal Server Error** — Ошибка обработки.

---

### 2. Получить неинтегрированные продукты
**`GET /mirakl-product-non-integrated/{import_parameter}`**

Возвращает продукты, которые не были интегрированы в Mirakl для заданного параметра импорта.

#### Параметры
- `import_parameter` *(строка, путь)* — Параметр импорта, предоставленный Mirakl при импорте продукта.

#### Пример запроса
```bash
curl -X GET "http://<host>/mirakl-product-non-integrated/12345"
```

#### Ответы
- **200 OK**
```json
{
  "message": { ... } // Список неинтегрированных продуктов
}
```
- **404 Not Found**
```json
{
  "detail": "Not found"
}
```
- **500 Internal Server Error** — Ошибка обработки.

---

### 3. Получить ошибку импорта предложения
**`GET /mirakl-offer-import-error/{import_parameter}`**

Проверяет, есть ли ошибки для заданного параметра импорта предложения.

#### Параметры
- `import_parameter` *(строка, путь)* — Параметр импорта, предоставленный Mirakl при импорте предложения.

#### Пример запроса
```bash
curl -X GET "http://<host>/mirakl-offer-import-error/12345"
```

#### Ответы
- **200 OK**
```json
{
  "message": { ... } // Ответ от Mirakl
}
```
- **404 Not Found**
```json
{
  "detail": "Not found"
}
```
- **500 Internal Server Error** — Ошибка обработки.

---

## Эндпоинты продуктов

### 1. Импорт продукта по EAN в Vente
**`POST /import-product/vente/{ean}`**

Импортирует один продукт из Afterbuy в Mirakl, используя EAN и опциональный ID ткани.

#### Параметры
- `ean` *(строка, путь)* — EAN код продукта для импорта.
- `afterbuy_fabric_id` *(целое число, запрос, опционально)* — ID ткани в Afterbuy для более точного выбора продукта.

#### Пример запроса
```bash
curl -X POST "http://<host>/import-product/1234567890123?afterbuy_fabric_id=1001"
```

#### Ответы
- **200 OK**
```json
{
  // Ответ API Mirakl для импортированного продукта
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

### 2. Импорт нескольких продуктов по списку EAN в Vente
**`POST /import-products/vente`**

Импортирует несколько продуктов из Afterbuy в Mirakl, используя список EAN.

#### Тело запроса
- `ean_list` *(массив строк, обязательно)* — Список EAN кодов для импорта.

#### Пример запроса
```bash
curl -X POST "http://<host>/import-products" \
  -H "Content-Type: application/json" \
  -d '{"ean_list": ["1234567890123", "9876543210987"]}'
```

#### Ответы
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

### 3. Импорт продуктов по ID ткани Afterbuy в Vente
**`POST /import-products-by-fabric/vente`**

Импортирует все продукты из Afterbuy в Mirakl для заданного ID ткани.

#### Параметры
- `afterbuy_fabric_id` *(целое число, тело)* - ID ткани в Afterbuy для импорта продуктов.
- `delivery_days` *(целое число, тело)* - Срок доставки продуктов клиентам.

#### Пример запроса
```bash
curl -X POST "http://<host>/import-products-by-fabric/vente"
```

#### Ответы
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

### 4. Импорт продуктов по ID ткани из файла в Vente
**`POST /import-products-by-fabric-from-file/vente`**

Импортирует продукты из Afterbuy в Mirakl по ID ткани, используя данные из файла.

#### Тело запроса
- `afterbuy_fabric_id` *(целое число, обязательно)* — ID ткани в Afterbuy для импорта продуктов.
- `delivery_days` *(целое число, обязательно)* — Срок доставки продуктов клиентам.
- `market` *(строка, обязательно)* — Рынок, для которого выполняется импорт.

#### Пример запроса
```bash
curl -X POST "http://<host>/import-products-by-fabric-from-file/vente" \
  -H "Content-Type: application/json" \
  -d '{"afterbuy_fabric_id": 1001, "delivery_days": 5, "market": "EU"}'
```

#### Ответы
- **200 OK**
```json
{
  "mirakl_answer": { ... },
  "not_added_eans": ["1234567890123"],
  "total_not_added": 1,
  "delivery days": 5,
  "total_eans_in_fabric": 10,
  "afterbuty_fabric_name": "Fabric Name",
  "database_status": "created"
}
```
- **403 Forbidden**
```json
{
  "detail": "Error message"
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
  "detail": "Error importing products to Mirakl"
}
```

---

## Тестовые эндпоинты

### 1. Тестовый импорт продукта по EAN
**`POST /test-import-product/vente/{ean}/`**

Тестовый эндпоинт для импорта одного продукта по EAN (возвращает сопоставленные данные для Mirakl, не импортирует).

#### Параметры
- `ean` *(строка, путь)* — EAN код продукта для тестового импорта.
- `afterbuy_fabric_id` *(целое число, запрос, опционально)* — ID ткани в Afterbuy для более точного выбора продукта.

#### Пример запроса
```bash
curl -X POST "http://<host>/test-import-product/1234567890123?afterbuy_fabric_id=1001"
```

#### Ответы
- **200 OK**
```json
{
  // Сопоставленные данные продукта для Mirakl
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

### 2. Тестовый импорт продуктов по ID ткани Afterbuy
**`POST /test-import-products-by-fabric/vente`**

Тестовый эндпоинт для импорта продуктов по ID ткани Afterbuy (возвращает сопоставленные данные для всех продуктов в ткани, не импортирует).

#### Параметры
- `afterbuy_fabric_id` *(целое число, путь)* — ID ткани в Afterbuy для тестового импорта продуктов.
- `delivery_days` *(целое число, тело)* - Срок доставки продуктов клиентам.

#### Пример запроса
```bash
curl -X POST "http://<host>/test-import-products-by-fabric"
```

#### Ответы
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

### 3. Тестирование изменения размера изображения
**`POST /test-resize-image`**

Тестовый эндпоинт для изменения размера изображения и функциональности загрузки по FTP.

#### Тело запроса
- `url` *(строка, обязательно)* — URL изображения для изменения размера и загрузки.
- `ean` *(строка, обязательно)* — EAN код для изображения.

#### Пример запроса
```bash
curl -X POST "http://<host>/test-resize-image" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/image.jpg", "ean": "1234567890123"}'
```

#### Ответы
- **200 OK**
```json
{
  // Результат операции изменения размера изображения и загрузки
}
```
- **422 Unprocessable Entity**
```json
{
  "detail": "Error message"
}
```

---
### 4. Тестирование удаления фона изображения
**`POST /test-remove-bg-image`**

Тестовый эндпоинт для удаления фона изображения и функциональности загрузки по FTP.

#### Тело запроса
- `image` - multipart-form/data, просто загрузка изображения

#### Ответы
- **200 OK**
```json
{
  // Результат операции удаления фона изображения и загрузки
}
```
- **422 Unprocessable Entity**
```json
{
  "detail": "Error message"
}
```