import os
import json
import re
from typing import Dict, Any, List

from groq import Groq

SYSTEM_PROMPT = """
Ты — профессиональный копирайтер-маркетолог, специализирующийся на персонализации контента для маркетплейсов.
Твоя задача — создавать убедительные тексты для товаров, которые максимально точно обращаются к языку, 
ценностям и "болям" конкретного сегмента целевой аудитории.
Ты превращаешь сухие характеристики в убедительные истории для каждой группы покупателей.
""".strip()


def build_user_prompt(product: Dict[str, Any], segment: Dict[str, Any], reviews_insights: List[str]) -> str:
    """
    Строит user prompt для генерации описания товара под конкретный сегмент.
    """
    
    # Собираем инсайты из отзывов
    positive_reviews = [r for r in reviews_insights if 'Достоинства' in r][:3]
    negative_reviews = [r for r in reviews_insights if 'Недостатки' in r][:3]
    
    reviews_text = ""
    if positive_reviews or negative_reviews:
        reviews_text = f"""
Инсайты из отзывов реальных покупателей:

Сильные стороны (из положительных отзывов):
{chr(10).join(f"- {r[:200]}..." for r in positive_reviews)}

Слабые места/возражения (из негативных отзывов):
{chr(10).join(f"- {r[:200]}..." for r in negative_reviews)}
"""
    
    return f"""
Роль:
Ты — копирайтер-маркетолог, специализирующийся на персонализации контента. Твоя задача — создать 
улучшенное описание товара, максимально точно обращающееся к языку, ценностям и "болям" конкретного 
сегмента целевой аудитории.

Информация о товаре:

Название: {product['name']}
Цена: {product['price']} {product['currency']}
Текущее описание: {product['description']}
Характеристики: {product['characteristics']}

Целевой сегмент аудитории:

Название сегмента: {segment['name']}
Доля аудитории: {segment['share_pct_est']}%
Основные потребности: {segment['needs']}
Болевые точки: {segment['pain_points']}
Рекомендуемое сообщение: {segment['recommended_message']}
{reviews_text}

Задача:
Создай готовое к публикации описание товара для этого сегмента аудитории.

Структура ответа (строго придерживайся):

1. СЕГМЕНТ-ЦЕЛЬ
{segment['name']}

2. СТРАТЕГИЯ ТЕКСТА
[1-2 предложения: как и почему этот текст работает на данный сегмент]

3. ЗАГОЛОВОК (H1)
[Цепляющий заголовок, 5-10 слов]

4. ЛИД-АБЗАЦ (ПОДЗАГОЛОВОК)
[Эмоциональное введение, 2-3 предложения]

5. ОСНОВНОЕ ОПИСАНИЕ

## Что вы получаете
[Превращение характеристик в выгоды для этого сегмента]

## Решение ваших задач
[Ответы на скрытые вопросы и снятие возражений из отзывов]

## Что говорят покупатели
[Социальное доказательство на основе реальных отзывов]

## Идеальные сценарии использования
[Контекст использования для этого сегмента]

6. ПОЧЕМУ ВЫБИРАЮТ ИМЕННО ЭТУ МОДЕЛЬ
- [Пункт 1]
- [Пункт 2]
- [Пункт 3]
- [Пункт 4]

7. ПРИЗЫВ К ДЕЙСТВИЮ
[Фраза для кнопки, соответствующая мотивации сегмента]

Требования:
- Объём: 1500-2500 символов
- Тон: соответствует сегменту
- Используй конкретные цифры и характеристики
- Обращайся напрямую к болям сегмента
- Включи цитаты или пересказ отзывов
- Формат: готовый текст для карточки товара

Начинай ответ сразу с раздела "1. СЕГМЕНТ-ЦЕЛЬ".
    """.strip()


def load_products(path: str) -> Dict[str, Dict[str, Any]]:
    """
    Загружает product.json (список объектов) и превращает в словарь по id.
    """
    with open(path, "r", encoding="utf-8") as f:
        items = json.load(f)

    products_by_id: Dict[str, Dict[str, Any]] = {}
    for p in items:
        pid = p["id"]
        products_by_id[pid] = p
    return products_by_id


def load_audience_segments(path: str) -> Dict[str, Any]:
    """
    Загружает audience_analysis_results.json и извлекает сегменты.
    Структура: массив[0].models['qwen/qwen3-32b'].parsed
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    parsed = data[0]['models']['qwen/qwen3-32b']['parsed']
    
    return {
        'product_name': parsed['product_name'],
        'summary': parsed['summary'],
        'segments': parsed['audience_segments'],
        'recommendations': parsed.get('recommendations', []),
        'ab_tests': parsed.get('a_b_test_hypotheses', [])
    }


def load_reviews(path: str) -> List[str]:
    """
    Загружает reviews.json и извлекает текст отзывов.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            reviews = json.load(f)
        
        # Извлекаем только текст отзывов
        return [r.get('review', r.get('text', '')) for r in reviews if r.get('review') or r.get('text')]
    except FileNotFoundError:
        print(f"[warning] Файл {path} не найден, генерация без инсайтов из отзывов.")
        return []


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

THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)

def strip_think_tags(text: str) -> str:
    """
    Удаляет блоки вида <think>...</think> из ответа модели, если они есть.
    """
    return THINK_RE.sub("", text).strip()

def call_model(
    client: Groq, 
    model: str, 
    product: Dict[str, Any], 
    segment: Dict[str, Any],
    reviews_insights: List[str]
) -> tuple:
    """
    Вызов модели Groq для генерации описания товара.
    Возвращает (текст описания, количество токенов).
    """
    user_prompt = build_user_prompt(product, segment, reviews_insights)

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=3000,
    )

    content = completion.choices[0].message.content or ""
    
    # Подсчет использованных токенов
    tokens_used = completion.usage.total_tokens if hasattr(completion, 'usage') else 0
    
    return content, tokens_used


def save_as_markdown(results: List[Dict[str, Any]], product_name: str, output_path: str):
    """
    Сохраняет результаты в красивом Markdown формате.
    """
    markdown_path = output_path.replace('.json', '.md')
    
    with open(markdown_path, 'w', encoding='utf-8') as f:
        f.write(f"# Персонализированные описания товара\n\n")
        f.write(f"**Товар:** {product_name}\n\n")
        f.write("---\n\n")
        
        for result in results:
            f.write(f"## Сегмент: {result['segment_name']} ({result['segment_share']}% аудитории)\n\n")
            f.write(f"**Модель:** {result['model']}\n")
            f.write(f"**Токенов использовано:** {result['tokens_used']}\n\n")
            f.write(result['description'])
            f.write("\n\n---\n\n")
    
    print(f"[info] Markdown версия сохранена: {markdown_path}")


def main():
    print("\n" + "="*80)
    print("  📝 ГЕНЕРАТОР ПЕРСОНАЛИЗИРОВАННЫХ ОПИСАНИЙ ТОВАРА")
    print("="*80)
    
    # Загрузка данных
    print("\n[info] Загрузка данных...")
    
    try:
        products = load_products("product.json")
        audience_data = load_audience_segments("audience_analysis_results.json")
        reviews_insights = load_reviews("reviews.json")
        
        print(f"[info] Загружено товаров: {len(products)}")
        print(f"[info] Загружено сегментов: {len(audience_data['segments'])}")
        print(f"[info] Загружено отзывов: {len(reviews_insights)}")
        
    except FileNotFoundError as e:
        print(f"\n[error] Не найден файл: {e}")
        print("\n💡 Убедитесь что существуют файлы:")
        print("  - product.json")
        print("  - audience_analysis_results.json")
        print("  - reviews.json (опционально)")
        return
    
    # Получаем первый товар (можно расширить для нескольких)
    product_id = list(products.keys())[0]
    product = products[product_id]
    
    print(f"\n[info] Товар для генерации: {product['name']}")
    print(f"[info] Цена: {product['price']} {product['currency']}")
    
    # Инициализация клиента
    client = get_client()
    
    results: List[Dict[str, Any]] = []
    total_tokens = 0
    
    # Генерация для каждого сегмента
    for idx, segment in enumerate(audience_data['segments'], 1):
        print("\n" + "="*80)
        print(f"[{idx}/{len(audience_data['segments'])}] Сегмент: {segment['name']}")
        print("-"*80)
        
        for model in MODELS:
            print(f"[info] Модель: {model}")
            
            try:
                description, tokens_used = call_model(
                    client, 
                    model, 
                    product, 
                    segment,
                    reviews_insights
                )
                
                total_tokens += tokens_used
                
                print(f"[ok] Описание создано! Токенов: {tokens_used}")
                print(f"[info] Длина текста: {len(description)} символов")
                
                results.append({
                    "segment_name": segment['name'],
                    "segment_share": segment['share_pct_est'],
                    "description": description,
                    "model": model,
                    "tokens_used": tokens_used
                })
                
            except Exception as e:
                print(f"[error] Ошибка при генерации: {e}")
                import traceback
                traceback.print_exc()
    
    # Сохранение результатов
    out_path = "product_descriptions.json"
    
    output_data = {
        "product": {
            "id": product['id'],
            "name": product['name'],
            "price": product['price'],
            "currency": product['currency']
        },
        "descriptions": results,
        "metadata": {
            "total_segments": len(results),
            "total_tokens": total_tokens,
            "models_used": MODELS
        }
    }
    
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*80)
    print("  ✅ ГЕНЕРАЦИЯ ЗАВЕРШЕНА!")
    print("="*80)
    print(f"\n📊 Статистика:")
    print(f"  - Создано описаний: {len(results)}")
    print(f"  - Всего токенов: {total_tokens}")
    print(f"\n💾 Файлы:")
    print(f"  - JSON: {out_path}")
    
    # Сохранение в Markdown
    save_as_markdown(results, product['name'], out_path)
    
    print("\n💡 Используйте описания для карточек товара на маркетплейсах!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()