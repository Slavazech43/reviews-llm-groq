# -*- coding: utf-8 -*-
"""
reviews_groq_criteria.py

Скрипт для анализа отзывов с помощью Groq API и кастомного промпта.

- Берёт товары из products.json
- Берёт отзывы из reviews.json
- Для каждого (отзыв, модель) делает:
    - system prompt: аналитик отзывов
    - user prompt: информация о товаре + текст отзыва + критерии
    - Модель сама определяет тональность отзыва
- Результат сохраняет в results_criteria.json

Перед запуском:
    pip install groq
    export GROQ_API_KEY="твой_ключ"

Файлы рядом со скриптом:
    products.json
    reviews.json
"""

import os
import json
import re
from typing import Dict, Any, List

from groq import Groq

# =========================
# 1. SYSTEM PROMPT
# =========================

SYSTEM_PROMPT = """
Ты — аналитик отзывов с экспертизой в выявлении скрытых паттернов, мотивации пользователя и потенциальных манипуляций.
Твоя задача — не просто суммировать отзыв, а провести его многоаспектную оценку по ключевым критериям.
""".strip()

# =========================
# 2. USER PROMPT BUILDER
# =========================

def build_user_prompt(product: Dict[str, Any], review_text: str) -> str:
    """
    Строит user prompt для ОДНОГО отзыва + ОДНОГО товара.
    Модель сама определяет тональность и заполняет JSON.
    """
    return f"""
Пожалуйста, проанализируй предоставленный отзыв на продукт по следующим критериям. 
По каждому пункту дай краткое обоснование (1-2 предложения) и оценку от 1 до 5, 
где 1 — минимальное соответствие, 5 — максимальное.

Информация о товаре:
- Товар: {product.get("name", "")}
- Ссылка: {product.get("url", "")}
- Цена: {product.get("price", "")} {product.get("currency", "")}

Описание:
{product.get("description", "")}

Характеристики:
{product.get("characteristics", "")}

Текст отзыва:
{review_text}

Критерии анализа:

1) Информативность: Насколько отзыв содержит конкретные факты, данные, детали об использовании продукта 
   (материал, срок службы, точные проблемы/плюсы)?

2) Релевантность: Насколько содержание отзыва соответствует заявленным функциям и назначению продукта?

3) Опыт использования (User Experience): Передает ли отзыв личный, субъективный опыт автора, его эмоции и 
   ощущения от взаимодействия с продуктом?

4) Ответы на вопросы: Можно ли из отзыва извлечь ответы на типичные вопросы потенциальных покупателей 
   (о качестве, простоте использования, недостатках)?

5) Контекст: Указан ли в отзыве важный контекст использования (климат, уровень навыков, сценарий применения), 
   который влияет на оценку?

6) Сравнение: Сравнивает ли автор продукт с аналогами, предыдущими версиями или ожиданиями?

7) Нарушение правил: Есть ли признаки того, что отзыв может быть фейковым, заказным, оскорбительным, 
   нецензурным или не соответствующим правилам платформы?

8) Конфликт интересов: Обнаруживаются ли признаки, что автор может быть конкурентом, аффилированным лицом 
   (сотрудником, получившим продукт на условиях рекламы), или его мнение обусловлено неоправданными ожиданиями?

Твоя задача:
1. Определи общую тональность отзыва: "положительный", "нейтральный" или "отрицательный".
2. Для КАЖДОГО критерия сформируй:
   - название критерия,
   - числовую оценку от 1 до 5,
   - краткое обоснование (1-2 предложения).

Ответ верни СТРОГО в виде корректного JSON без пояснений вокруг, в формате:

{{
  "тональность": "положительный | нейтральный | отрицательный",
  "критерии": [
    {{
      "критерий": "Информативность",
      "оценка": 1-5,
      "обоснование": "..."
    }},
    {{
      "критерий": "Релевантность",
      "оценка": 1-5,
      "обоснование": "..."
    }},
    ...
  ]
}}

НЕ используй теги <think> и подобные, просто верни JSON.
    """.strip()

def load_products(path: str) -> Dict[str, Dict[str, Any]]:
    """
    Загружает products.json (список объектов) и превращает в словарь по id.
    """
    with open(path, "r", encoding="utf-8") as f:
        items = json.load(f)

    products_by_id: Dict[str, Dict[str, Any]] = {}
    for p in items:
        pid = p["id"]
        products_by_id[pid] = p
    return products_by_id


def load_reviews(path: str) -> List[Dict[str, Any]]:
    """
    Загружает reviews.json (список отзывов).
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_client() -> Groq:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Не найден GROQ_API_KEY. Установи переменную окружения GROQ_API_KEY со своим ключом Groq."
        )
    return Groq(api_key=api_key)

MODELS: List[str] = [
    "qwen/qwen3-32b",
]

# =========================
# 5. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =========================

THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)

def strip_think_tags(text: str) -> str:
    """
    Удаляет блоки вида <think>...</think> из ответа модели, если они есть.
    """
    return THINK_RE.sub("", text).strip()

def call_model(client: Groq, model: str, product: Dict[str, Any], review_text: str) -> Dict[str, Any]:
    """
    Вызов модели Groq: system + user, постобработка без <think>, парсинг JSON.
    Возвращаем dict с результатом или с полем raw_response, если JSON не распарсился.
    """
    user_prompt = build_user_prompt(product, review_text)

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.0,
    )

    content = completion.choices[0].message.content or ""
    content = strip_think_tags(content)

    try:
        parsed = json.loads(content)
        return parsed
    except json.JSONDecodeError:
        # если модель всё равно не попала в JSON — сохраняем сырой текст
        return {
            "raw_response": content,
            "parse_error": "JSONDecodeError"
        }


def main():
    products = load_products("products.json")
    reviews = load_reviews("reviews.json")
    client = get_client()

    results: List[Dict[str, Any]] = []

    for r in reviews:
        review_id = r["id"]
        product_id = r["product_id"]
        text = r["text"]

        product = products.get(product_id)
        if not product:
            print(f"[WARN] Для отзыва {review_id} не найден product_id={product_id}, пропускаю.")
            continue

        print("=" * 80)
        print(f"Отзыв: {review_id}")
        print(f"Товар: {product['name']}")
        print(f"Текст отзыва: {text}\n")

        for model in MODELS:
            print("-" * 80)
            print(f"Модель: {model}")

            resp = call_model(client, model, product, text)

            sentiment = resp.get("тональность") if isinstance(resp, dict) else None
            crits = resp.get("критерии") if isinstance(resp, dict) else None
            print(f"Тональность (по модели): {sentiment}")
            if isinstance(crits, list):
                print(f"Критериев: {len(crits)}")
            else:
                print("Ответ не в формате ожидаемого JSON, см. results_criteria.json")

            results.append({
                "review_id": review_id,
                "product_id": product_id,
                "model": model,
                "result": resp
            })

    out_path = "results_criteria.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nГотово! Результаты сохранены в {out_path}")


if __name__ == "__main__":
    main()