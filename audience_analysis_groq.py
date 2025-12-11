import os
import re
import json
import argparse
from typing import Any, Dict, List, Optional
from groq import Groq

MODELS = [
    "qwen/qwen3-32b",
]


SYSTEM_PROMPT = """Ты — аналитик целевой аудитории с практическим опытом маркетинга продукта и анализа отзывов.
Твоя задача — на основе информации о продукте и собранных текстов отзывов сформулировать:
1) основные сегменты целевой аудитории (3-6 сегментов): короткое название сегмента, примерный процент от всех отзывов (оценка), главные потребности и болевые точки,
2) ключевые мотивационные триггеры для каждой группы (чтобы использовать в рекламных сообщениях),
3) рекомендации по позиционированию продукта и точкам улучшения для продукта/комплектации,
4) короткий список гипотез для A/B тестов (2-4 штуки).

Требования к ответу:
- Верни строго **JSON** (без поясняющего текста). JSON должен быть объектом со следующими полями:
  {
    "product_id": "...",
    "product_name": "...",
    "summary": "краткая сводка 1-2 предложения",
    "audience_segments": [
      {"name": "...", "share_pct_est": number, "needs": "...", "pain_points": "...", "recommended_message": "..."},
      ...
    ],
    "recommendations": ["...", "..."],
    "a_b_test_hypotheses": ["...", "..."]
  }
- Если модели нужно что-то уточнить — не задавай вопросов в выводе, формализуй гипотезы/рекомендации.
- Выведи корректный JSON, ничего лишнего. Температура 0 рекомендуется.
"""

USER_PROMPT_TEMPLATE = """
Информация о товаре:
- name: {name}
- url: {url}
- price: {price}

Краткое описание:
{description}

Ключевые характеристики:
{characteristics}

Собрано N отзывов (показаны первые 5 для контекста):
{sample_reviews}

Дополнительная информация: продукт и отзывы относятся к российским маркетплейсам (Wildberries/Ozon) — учти ценовую чувствительность и ожидания бытовых инструментов.

Действуй согласно системной инструкции: выдели сегменты ЦА, их потребности, болевые точки, триггеры, рекомендации по позиционированию и гипотезы для A/B тестов.
"""

JSON_RE_FIND = re.compile(r"(\{(?:.|\n)*\}|\[(?:.|\n)*\])", flags=re.MULTILINE)


def get_client() -> Groq:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("Не найден GROQ_API_KEY в окружении. Установи переменную окружения с ключом Groq.")
    return Groq(api_key=api_key)


def safe_load_json(path: str) -> Any:
    """Загружает JSON-файл и возвращает Python-структуру."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_product_input(prod_json: Any) -> List[Dict[str, Any]]:
    """
    Приводит products.json к списку product-объектов.
    Поддерживает: single object, list of objects, dict of id->object.
    """
    if isinstance(prod_json, list):
        return prod_json
    if isinstance(prod_json, dict):
        # определим — это либо объект продукта, либо mapping
        # если ключи похожи на product ids? — но безопаснее: если есть 'name' — считаем это одним продуктом
        if "name" in prod_json:
            return [prod_json]
        # иначе есть вероятность, что это mapping id->obj
        result = []
        for k, v in prod_json.items():
            if isinstance(v, dict):
                v.setdefault("product_id", k)
                result.append(v)
        return result
    raise ValueError("Не удалось распознать формат products.json")


def extract_reviews_from_results(results_json: Any) -> List[Dict[str, Any]]:
    """
    Из results.json пытаемся извлечь списки отзывов.
    Ожидаем, что элементы содержат поле 'review' (текст) и опционально 'product_id'.
    Если файл — просто список текстов, вернём их.
    """
    reviews_out = []
    if isinstance(results_json, list):
        # элементы могут быть dict с разными ключами
        for item in results_json:
            if isinstance(item, dict):
                # поле с текстом может быть 'review' или 'review_text' или 'text'
                text = item.get("review") or item.get("review_text") or item.get("text")
                pid = item.get("product_id") or item.get("productId") or item.get("product")
                if text:
                    reviews_out.append({"review": text, "product_id": pid})
                else:
                    # попытка: если есть 'raw_response' — в нём может быть JSON — но пропускаем
                    continue
            elif isinstance(item, str):
                reviews_out.append({"review": item, "product_id": None})
    elif isinstance(results_json, dict):
        # если это dict, попробуем найти значение, где лежит список отзывов
        # ищем ключи вроде 'reviews', 'results'
        for k in ("reviews", "results", "data"):
            if k in results_json and isinstance(results_json[k], list):
                return extract_reviews_from_results(results_json[k])
        # если dict сам содержит 'review'
        text = results_json.get("review") or results_json.get("review_text")
        if text:
            reviews_out.append({"review": text, "product_id": results_json.get("product_id")})
    return reviews_out


def first_sample_reviews_for_product(reviews: List[Dict[str, Any]], product_id: Optional[str], n: int = 5) -> List[str]:
    filtered = [r["review"] for r in reviews if (product_id is None or r.get("product_id") == product_id)]
    return filtered[:n]


def extract_json_from_model_response(text: str) -> Any:
    """
    Пытаемся найти первый JSON (object/array) в тексте ответа модели и распарсить.
    Это удаляет любые <think> ... </think> или прочие префиксы.
    """
    # быстрый try - если строка сама валидный JSON
    try:
        return json.loads(text)
    except Exception:
        pass

    # ищем первый JSON-паттерн
    m = JSON_RE_FIND.search(text)
    if m:
        candidate = m.group(1)
        # пробуем "исправить" кавычки если нужно? пока просто load
        try:
            return json.loads(candidate)
        except Exception:
            # пробуем заменить одинарные кавычки на двойные (опасно, но иногда помогает)
            candidate2 = candidate.replace("'", '"')
            try:
                return json.loads(candidate2)
            except Exception:
                return {"__raw_extracted": candidate, "__original_text_start": text[:400]}
    # ничего не нашли
    return {"__raw_response": text}

THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)

def strip_think_tags(text: str) -> str:
    """
    Удаляет блоки вида <think>...</think> из ответа модели, если они есть.
    """
    return THINK_RE.sub("", text).strip()

def call_model_and_parse(client: Groq, model: str, system_prompt: str, user_prompt: str) -> Any:
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.0,
        max_tokens=1500,
    )
    content = completion.choices[0].message.content
    parsed = extract_json_from_model_response(content)
    return { "parsed": parsed}


def build_user_prompt_for_product(product: Dict[str, Any], sample_reviews: List[str]) -> str:
    # создаём аккуратную строку характеристик
    chars = product.get("characteristics") or product.get("characteristics_text") or ""
    if isinstance(chars, dict):
        chars = "\n".join([f"- {k}: {v}" for k, v in chars.items()])
    sample_txt = "\n".join([f"- {r}" for r in sample_reviews]) if sample_reviews else "(нет примеров)"
    return USER_PROMPT_TEMPLATE.format(
        name=product.get("name", "Unknown"),
        url=product.get("url", ""),
        price=product.get("price", ""),
        description=product.get("description", "")[:2000],  # обрезаем для безопасности
        characteristics=chars,
        sample_reviews=sample_txt,
    )


def main():
    parser = argparse.ArgumentParser(description="Audience analysis (Groq) - product + reviews -> audience JSON")
    parser.add_argument("--product", "-p", required=True, help="path to products.json")
    parser.add_argument("--reviews", "-r", required=True, help="path to results.json (reviews)")
    parser.add_argument("--out", "-o", default="audience_analysis_results.json", help="output filename")
    args = parser.parse_args()

    # load files
    try:
        raw_products = safe_load_json(args.product)
    except Exception as e:
        print(f"[error] Не удалось загрузить products file: {e}")
        return

    try:
        raw_reviews = safe_load_json(args.reviews)
    except Exception as e:
        print(f"[error] Не удалось загрузить reviews file: {e}")
        return

    products = normalize_product_input(raw_products)
    reviews = extract_reviews_from_results(raw_reviews)

    if not reviews:
        print("[warning] Не найдено текстов отзывов в results.json. Убедитесь, что поле 'review' присутствует.")
        # но не прерываем — можно попытаться проанализировать только продукт
    else:
        print(f"[info] Загружено {len(reviews)} отзывов.")

    client = get_client()

    results_out = []
    # Если products пуст — проанализируем всё сразу как общий кейс
    if not products:
        print("[warning] В products.json не найдено продуктов. Выполняется общий анализ по всем отзывам.")
        # строим фиктивный объект
        prod_obj = {"product_id": None, "name": "Aggregated product", "url": "", "price": "", "description": ""}
        sample = first_sample_reviews_for_product(reviews, None, n=5)
        user_prompt = build_user_prompt_for_product(prod_obj, sample)
        per_model = {}
        for model in MODELS:
            print(f"[info] Вызов модели: {model}")
            try:
                res = call_model_and_parse(client, model, SYSTEM_PROMPT, user_prompt)
                per_model[model] = res
            except Exception as e:
                per_model[model] = {"error": str(e)}
        results_out.append({"product": prod_obj, "models": per_model})
    else:
        for prod in products:
            pid = prod.get("product_id") or prod.get("id") or prod.get("sku") or prod.get("article")
            name = prod.get("name")
            print(f"[info] Загружен товар: {name} (id={pid})")
            sample = first_sample_reviews_for_product(reviews, pid, n=5)
            # если по product_id нет отзывов, возьмём все отзывы, но пометим это
            if not sample:
                sample = first_sample_reviews_for_product(reviews, None, n=5)
                print(f"[warning] Не найдено отзывов для product_id={pid}. Используем общие примеры ({len(sample)}).")
            user_prompt = build_user_prompt_for_product(prod, sample)
            per_model = {}
            for model in MODELS:
                print(f"[info] Вызов модели: {model} для продукта {name}")
                try:
                    res = call_model_and_parse(client, model, SYSTEM_PROMPT, user_prompt)
                except Exception as e:
                    print(f"[error] Ошибка вызова модели {model}: {e}")
                    res = {"error": str(e)}
                per_model[model] = res
            results_out.append({"product": {"product_id": pid, "name": name}, "models": per_model})

    # Сохраняем результат
    out_path = args.out
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results_out, f, ensure_ascii=False, indent=2)

    

    print(f"[ok] Сохранено в {out_path}")


if __name__ == "__main__":
    main()