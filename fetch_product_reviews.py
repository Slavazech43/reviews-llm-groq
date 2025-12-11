# -*- coding: utf-8 -*-
"""
fetch_product_reviews.py

Универсальный скрипт: по ссылке на товар (Wildberries / Ozon и другие)
пытается вытянуть основные поля продукта и отзывы, сохранить в:
 - products.json  (словарь product_id -> product data)
 - reviews.json   (список отзывов с привязкой product_id)

Запуск:
    python3 fetch_product_reviews.py "https://www.wildberries.ru/catalog/396501168/detail.aspx"

Зависимости:
    pip install requests beautifulsoup4

Примечания:
- Некоторые маркетплейсы сильно защищены от скрейпинга (Cloudflare, bot-fingerprinting).
  В этом случае скрипт попробует несколько раз с заголовками браузера.
  Если и это не поможет — появится подсказка использовать Selenium/прокси/ручной экспорт.
- Скрипт сохраняет исходные html-страницы в ./cache для отладки.
"""

import os
import sys
import json
import time
import re
from typing import Dict, Any, List, Tuple
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

# === Настройки ===
CACHE_DIR = "cache_html"
OUTPUT_PRODUCTS = "products.json"
OUTPUT_REVIEWS = "reviews.json"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15"
)
DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.google.com/"
}

os.makedirs(CACHE_DIR, exist_ok=True)


# === Утилиты ===

def safe_get(url: str, max_retries: int = 4, timeout: int = 10) -> Tuple[str, int]:
    """
    Запрос с заголовками, повторами и экспоненциальным backoff.
    Возвращает (text, status_code).
    """
    delay = 1.0
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
            # Сохраним в кэш для отладки
            parsed = urlparse(url)
            fname = os.path.join(CACHE_DIR, f"{parsed.netloc}_{abs(hash(url))}.html")
            with open(fname, "w", encoding="utf-8") as f:
                f.write(resp.text)
            return resp.text, resp.status_code
        except requests.exceptions.RequestException as e:
            print(f"[warn] Request error (attempt {attempt}/{max_retries}): {e}")
            if attempt == max_retries:
                print("[error] Превышено количество попыток запроса.")
                raise
            time.sleep(delay)
            delay *= 2.0
    return "", 0


def clean_think_blocks(text: str) -> str:
    """
    Удаляет блоки <think>...</think> и лишние служебные вставки,
    возвращая "чистый" текст.
    """
    # Удаляем <think>...</think> (DOTALL)
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    # также убираем xml-like оставшиеся теги, если нужно
    cleaned = cleaned.strip()
    return cleaned


def json_save(path: str, data: Any):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[ok] Сохранено: {path}")


# === Парсеры для маркетплейсов (упрощённые) ===

def parse_generic(html: str, url: str) -> Dict[str, Any]:
    """
    Универсальный парсер: пытаемся взять og:title, og:description, meta price и т.д.
    Возвращает словарь с полями name, url, price, description, characteristics (строка).
    """
    soup = BeautifulSoup(html, "html.parser")
    def og(key):
        tag = soup.find("meta", property=f"og:{key}") or soup.find("meta", attrs={"name": f"{key}"})
        return tag["content"].strip() if tag and tag.get("content") else None

    name = og("title") or og("site_name") or (soup.title.string.strip() if soup.title else None)
    description = og("description") or og("site_description")
    # Try common price meta tags
    price = None
    price_meta = soup.find("meta", {"itemprop": "price"}) or soup.find("meta", {"property": "product:price:amount"})
    if price_meta and price_meta.get("content"):
        price = price_meta["content"].strip()
    # fallback: regex for price-like sequences e.g. "1298 ₽" in visible text (first match)
    if not price:
        m = re.search(r"(\d{3,6}\s?₽|\d{3,6}\s?RUR|\d{2,6}\s?руб(?:\.|ль)?)", html)
        if m:
            price = m.group(0)

    # Simple characteristics: join some info blocks if present
    chars = []
    # look for table of characteristics
    for table in soup.find_all("table"):
        # take small tables
        text = table.get_text(separator=" | ", strip=True)
        if text and len(text) < 2000:
            chars.append(text)
    characteristics = "\n".join(chars[:3]) if chars else ""

    product = {
        "name": name or "",
        "url": url,
        "price": price or "",
        "description": (description or "").strip(),
        "characteristics": characteristics.strip(),
        "source": urlparse(url).netloc
    }
    return product


def parse_wildberries(html: str, url: str) -> Dict[str, Any]:
    """
    Попытка более точной выборки для Wildberries.
    Но сайту может быть нужна JS — тогда fallback на generic.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Try to read JSON data embedded (wildberries often embeds JSON in <script> window.__INITIAL_STATE__ or similar)
    # We'll try some heuristics; if not found — fallback to generic.
    # NOTE: this is best-effort; Wildberries markup изменяется часто.
    product = parse_generic(html, url)

    # Try to extract product name from specific selectors
    h1 = soup.find("h1")
    if h1 and h1.text.strip():
        product["name"] = h1.text.strip()

    # Wildberries sometimes has 'price' in data-product-price or meta name="twitter:data1"
    price_tag = soup.find(attrs={"data-purpose": "price"})
    if price_tag:
        product["price"] = price_tag.get_text(strip=True)

    return product


def parse_ozon(html: str, url: str) -> Dict[str, Any]:
    """
    Попытка парсинга для Ozon.
    """
    soup = BeautifulSoup(html, "html.parser")
    product = parse_generic(html, url)

    # Ozon often sets <h1> title in page
    h1 = soup.find("h1")
    if h1 and h1.text.strip():
        product["name"] = h1.text.strip()

    # price
    price_el = soup.select_one("[data-test-id=price]")
    if price_el:
        product["price"] = price_el.get_text(strip=True)

    return product


def extract_reviews_from_html(html: str) -> List[Dict[str, Any]]:
    """
    Пытаемся найти отзывы в HTML: ищем блоки с классами 'review', 'feedback' и т.п.
    Возвращаем список словарей: { "text": "...", "author": "...", "rating": 5/None }
    """
    soup = BeautifulSoup(html, "html.parser")
    results = []
    # common guess classes
    candidates = soup.find_all(class_=re.compile(r"(review|feedback|comment|opinion|user-review|product-review)", re.I))
    if not candidates:
        # fallback: look for elements with "data-test" containing "review"
        candidates = soup.select("[data-test*='review'], [data-test*='comment']")
    # Deduplicate and collect text
    seen = set()
    for el in candidates:
        text = el.get_text(separator=" ", strip=True)
        if not text or len(text) < 10:
            continue
        if text in seen:
            continue
        seen.add(text)
        # Try to get rating (look inside for stars or numeric)
        rating = None
        rmatch = re.search(r"(\d(?:[.,]\d)?)[/ ]?5", text)
        if rmatch:
            try:
                rating = int(float(rmatch.group(1)))
            except:
                rating = None
        results.append({"text": text, "author": None, "rating": rating})
    return results


# === Основная логика ===

def detect_site_and_parse(url: str) -> Dict[str, Any]:
    html, status = safe_get(url)
    domain = urlparse(url).netloc.lower()
    print(f"[info] HTTP status: {status}  domain: {domain}")

    if status >= 400:
        # special-case: 498 or other bot-block — try one more time with slightly different UA
        print(f"[warn] Получен статус {status}. Попробуем ещё раз с другим User-Agent.")
        alt_headers = DEFAULT_HEADERS.copy()
        alt_headers["User-Agent"] = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        try:
            resp = requests.get(url, headers=alt_headers, timeout=12)
            with open(os.path.join(CACHE_DIR, f"{domain}_fallback.html"), "w", encoding="utf-8") as f:
                f.write(resp.text)
            html = resp.text
            status = resp.status_code
            print(f"[info] Повторный запрос статус: {status}")
        except Exception as e:
            print(f"[error] Повторный запрос не удался: {e}")
            # не бросаем исключение — вернём generic с пустыми отзывами
            return {"product": parse_generic("", url), "reviews": []}

    # Выбор парсера по домену
    if "wildberries.ru" in domain:
        product = parse_wildberries(html, url)
    elif "ozon.ru" in domain:
        product = parse_ozon(html, url)
    else:
        product = parse_generic(html, url)

    # Попытка извлечь отзывы
    reviews = extract_reviews_from_html(html)
    return {"product": product, "reviews": reviews}


def ensure_products_file():
    if os.path.exists(OUTPUT_PRODUCTS):
        with open(OUTPUT_PRODUCTS, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}


def ensure_reviews_file():
    if os.path.exists(OUTPUT_REVIEWS):
        with open(OUTPUT_REVIEWS, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return []
    return []


def interactive_add_reviews(product_id: str) -> List[Dict[str, Any]]:
    """
    Если автоматом не нашлось отзывов, даём пользователю возможность:
    - ввести несколько отзывов вручную
    - или нажать Enter чтобы пропустить
    """
    print("[input] Введите отзывы вручную (каждый отзыв новой строкой). Пустая строка — окончание.")
    print("Введите 'file:<path>' чтобы загрузить отзывы из файла (по строкам).")
    collected = []
    while True:
        line = input()
        if not line.strip():
            break
        if line.startswith("file:"):
            p = line.split("file:",1)[1].strip()
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    for l in f:
                        t = l.strip()
                        if t:
                            collected.append({"product_id": product_id, "text": t})
                break
            else:
                print("[error] Файл не найден:", p)
                continue
        collected.append({"product_id": product_id, "text": line.strip()})
    return collected


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 fetch_product_reviews.py <product_url>")
        sys.exit(1)
    url = sys.argv[1].strip()
    print(f"[info] Start parsing: {url}")

    out_products = ensure_products_file()
    out_reviews = ensure_reviews_file()

    parsed = detect_site_and_parse(url)
    product = parsed["product"]
    reviews = parsed["reviews"]

    # Make product_id
    parsed_url = urlparse(url)
    product_id = f"{parsed_url.netloc}_{abs(hash(url))}"

    # if product name missing, ask user to input (fallback)
    if not product.get("name"):
        name = input("[input] Введите название товара (или Enter чтобы пропустить): ").strip()
        if name:
            product["name"] = name

    # Save product record
    product_record = {
        "id": product_id,
        "name": product.get("name",""),
        "url": url,
        "price": product.get("price",""),
        "description": product.get("description",""),
        "characteristics": product.get("characteristics",""),
        "source": product.get("source",""),
    }
    out_products[product_id] = product_record

    # If no reviews found — allow manual entry
    if not reviews:
        print("[info] Найдено отзывов: 0")
        extra = interactive_add_reviews(product_id)
        if extra:
            for r in extra:
                out_reviews.append({"product_id": product_id, "text": r["text"]})
    else:
        # Normalize review items
        for r in reviews:
            text = r.get("text") or r.get("comment") or ""
            out_reviews.append({"product_id": product_id, "text": text, "rating": r.get("rating")})

    # Persist files
    json_save(OUTPUT_PRODUCTS, out_products)
    json_save(OUTPUT_REVIEWS, out_reviews)

    print(f"[info] Найдено отзывов: {len([r for r in out_reviews if r.get('product_id')==product_id])}")


if __name__ == "__main__":
    main()