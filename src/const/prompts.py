from src.core.settings import settings

def build_description_prompt_vente(html_desc: str, product_properties: dict, product_article: str, product_price: float | int, delivery_days: int | None = 90):
    description_prompt = (
        "You are an e-commerce content assistant. "
        "Your task is to take the provided raw product text, properties, article title, and additional offer details, "
        "and generate two different product descriptions suitable for an online marketplace.\n\n"
        "Output must strictly follow this schema:\n"
        f"- description_de: German description (marketing-friendly, clear, maximum {settings.max_description_chars} characters, minimum 100 characters). "
        "Focus only on the product itself: design, dimensions, material, color, usage, style, etc.\n"
        f"- description_fr: French description (maximum {settings.max_description_chars} characters, minimum 100 characters). "
        "This text should focus on the commercial offer: mention price, delivery time, warranty, and other conditions relevant to French buyers. "
        "Highlight the value of the offer (e.g., fast delivery, affordable price, included guarantee). Do not just translate the German version — adapt it to emphasize the offer.\n\n"
        "Rules:\n"
        "- You must NOT call any tools. "
        "- Remove HTML tags, promotional inserts, control characters, and irrelevant technical clutter (e.g. EAN codes, packaging details, surcharge notes).\n"
        "- Remove all special characters or editor symbols such as \\n, \\t, escaped quotes (\\\"), braces (\\{...\\}), or similar artifacts. "
        "The final descriptions must contain only clean, natural text.\n"
        "- Use product properties and article title in the German description to make the product clear.\n"
        "- Use price, delivery time, and warranty in the French description if available, to make the offer appealing.\n"
        "- Write in fluent, natural, customer-friendly language.\n"
        "- Avoid repetitions, bullet lists, and unnecessary technical jargon unless essential (e.g. measurements).\n"
        "- Maximum length per description: 2250 characters.\n\n"
        "Input data:\n"
        f"Raw text:\n{html_desc}\n\n"
        f"Product properties:\n{product_properties}\n\n"
        f"Article:\n{product_article}\n\n"
        f"Offer details:\nPrice: {product_price} euro\nDelivery days: {delivery_days}\n"
    )
    return description_prompt


def build_description_prompt_lutz(html_desc: str, product_properties: dict, product_article: str, product_price: float | int, delivery_days: int | None = 90):
    description_prompt = (
        "You are an e-commerce content assistant. "
        "Your task is to take the provided raw product text, properties, article title, and additional offer details, "
        "and generate two different product descriptions suitable for an online marketplace.\n\n"
        "Output must strictly follow this schema:\n"
        f"- description_de: German description (marketing-friendly, clear, maximum {settings.max_description_chars} characters, minimum 100 characters). "
        "Focus only on the product itself: design, dimensions, material, color, usage, style, etc.\n"
        f"- description_en: English description (maximum {settings.max_description_chars} characters, minimum 100 characters). "
        "This text should focus on the commercial offer: mention price, delivery time, warranty, and other conditions relevant to English buyers. "
        "Highlight the value of the offer (e.g., fast delivery, affordable price, included guarantee). Do not just translate the German version — adapt it to emphasize the offer.\n\n"
        "Rules:\n"
        "- You must NOT call any tools. "
        "- Remove HTML tags, promotional inserts, control characters, and irrelevant technical clutter (e.g. EAN codes, packaging details, surcharge notes).\n"
        "- Remove all special characters or editor symbols such as \\n, \\t, escaped quotes (\\\"), braces (\\{...\\}), or similar artifacts. "
        "The final descriptions must contain only clean, natural text.\n"
        "- Use product properties and article title in the German description to make the product clear.\n"
        "- Use price, delivery time, and warranty in the French description if available, to make the offer appealing.\n"
        "- Write in fluent, natural, customer-friendly language.\n"
        "- Avoid repetitions, bullet lists, and unnecessary technical jargon unless essential (e.g. measurements).\n"
        "- Maximum length per description: 2250 characters.\n\n"
        "Input data:\n"
        f"Raw text:\n{html_desc}\n\n"
        f"Product properties:\n{product_properties}\n\n"
        f"Article:\n{product_article}\n\n"
        f"Offer details:\nPrice: {product_price} euro\nDelivery days: {delivery_days}\n"
    )
    return description_prompt