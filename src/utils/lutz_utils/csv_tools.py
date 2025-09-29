# app/utils/csv_tools.py
import csv
import io


def build_fieldnames(mapping: dict) -> list:
    """Формируем список полей CSV на основании mapping + добавляем обязательные поля."""
    fields = []
    for dst in mapping.values():
        if isinstance(dst, list):
            fields.extend(dst)
        else:
            fields.append(dst)

    # Всегда должен быть category
    if "category" not in fields:
        fields.append("category")

    # Список обязательных/желательных полей (включая Distributor и прочее)
    mandatory = [
        "ean", "product-id", "product-id-type", "gtin", "sku", "shop_sku", "title", "brand", "product_description",
        "name [de]", "description [de]",
        "images.main_image", "images.secondary_image", "main_picture",
        "Color", "Material", "DimensionWidth", "DimensionDepthLength", "DimensionHeight",
        "specifications.color", "specifications.main_material",
        "specifications.width_cm", "specifications.length_depth_cm", "specifications.height_cm",
        "specifications.manufacturer_warranty_years",
        "DistributorName", "DistributorStreet", "DistributorZip", "DistributorCity", "DistributorCountry",
    ]

    for m in mandatory:
        if m not in fields:
            fields.append(m)

    # Добавляем поля офферов (price/state/quantity) если ещё нет
    for extra in ["price", "state", "quantity", "offer-description"]:
        if extra not in fields:
            fields.append(extra)

    # Убираем дубликаты, сохраняя порядок
    return list(dict.fromkeys(fields))


def write_csv(fieldnames: list, rows: list) -> str:
    """Генерируем CSV в памяти и возвращаем содержимое как строку. Разделитель - ';' (Mirakl)."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter=";")
    writer.writeheader()
    for row in rows:
        # гарантируем, что для всех fieldnames есть ключ (если нет — пустая строка)
        writer.writerow({fn: row.get(fn, "") for fn in fieldnames})
    return output.getvalue()