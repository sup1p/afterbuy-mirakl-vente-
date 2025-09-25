# app/utils/html_parser.py
from bs4 import BeautifulSoup, Tag, NavigableString
import re


def _clean_text_lines(text: str) -> str:
    """Чистим пустые строки и одиночные ':' из текста."""
    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    merged = []
    for ln in lines:
        if ln == ":" and merged:
            merged[-1] = merged[-1] + ":"
        else:
            merged.append(ln)
    return "\n".join(merged)


def extract_text_from_html(html_str: str) -> str:
    """Извлекаем текст из HTML (без script/style) — универсальный фолбэк."""
    if not html_str:
        return ""
    soup = BeautifulSoup(html_str, "html.parser")
    for t in soup(["script", "style"]):
        t.decompose()
    return _clean_text_lines(soup.get_text(separator="\n"))


def extract_productdetails(html_str: str) -> str:
    """
    Пытаемся достать блок 'Produktdetails' из HTML.
    Если не найдено — чистим весь текст.
    """
    if not html_str:
        return ""
    soup = BeautifulSoup(html_str, "html.parser")
    for t in soup(["script", "style"]):
        t.decompose()

    # ищем заголовок "Produktdetails"
    heading = soup.find(
        string=lambda t: isinstance(t, str) and re.search(r"produkt\s*details", t, re.I)
    )
    if not heading:
        return extract_text_from_html(html_str)

    # start_node = heading сам по себе, если это Tag, иначе parent
    start_node = heading if isinstance(heading, Tag) else heading.parent
    if start_node is None:
        return extract_text_from_html(html_str)

    container = None
    # оригинальная логика: find_all_next, ищем первый элемент после заголовка с текстом >20 символов
    for el in start_node.find_all_next(["div", "section", "table", "td"], limit=600):
        if not isinstance(el, Tag):
            continue
        txt = el.get_text(strip=True)
        if txt and len(txt) > 20:
            container = el
            break

    if not container:
        return extract_text_from_html(html_str)

    raw_text = container.get_text(separator="\n")
    return _clean_text_lines(raw_text)