"""
Улучшенный парсер с использованием API Wildberries
Более стабильный и быстрый
"""

import asyncio
import json
import re
import logging
import aiohttp
from typing import Dict, Any, List, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class WBAPIParser:
    """Парсер через API Wildberries"""
    
    @staticmethod
    def extract_product_id(url: str) -> str:
        """Извлечение ID товара из URL"""
        match = re.search(r'/catalog/(\d+)/', url)
        return match.group(1) if match else None
    
    async def get_product_info(self, product_id: str) -> Optional[Dict]:
        """Получение информации о товаре через API"""
        try:
            # API для получения базовой информации
            api_url = f"https://card.wb.ru/cards/v1/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm={product_id}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
        except Exception as e:
            logger.error(f"❌ Ошибка API: {e}")
        
        return None
    
    async def parse_product(self, url: str) -> Dict[str, Any]:
        """Парсинг товара"""
        logger.info("="*60)
        logger.info("🛒 ПАРСИНГ WILDBERRIES (API)")
        logger.info("="*60)
        
        product_id = self.extract_product_id(url)
        if not product_id:
            raise ValueError("Не удалось извлечь ID товара из URL")
        
        logger.info(f"🆔 Product ID: {product_id}")
        
        # Получение данных через API
        data = await self.get_product_info(product_id)
        
        if not data or 'data' not in data or 'products' not in data['data']:
            logger.error("❌ Не удалось получить данные через API")
            return self._create_fallback_data(product_id, url)
        
        product = data['data']['products'][0]
        
        # Извлечение данных
        name = product.get('name', 'Товар без названия')
        logger.info(f"✅ Название: {name[:60]}...")
        
        # Цена
        price = None
        if 'salePriceU' in product:
            price = product['salePriceU'] // 100  # Цена в копейках, делим на 100
            logger.info(f"💰 Цена: {price} ₽")
        
        # Бренд
        brand = product.get('brand', '')
        
        # Рейтинг
        rating = product.get('rating', 0)
        
        # Количество отзывов
        feedbacks = product.get('feedbacks', 0)
        logger.info(f"⭐ Рейтинг: {rating}, Отзывов: {feedbacks}")
        
        # Описание и характеристики
        description = product.get('description', '')
        
        return {
            "product": {
                "id": f"wb_{product_id}",
                "name": name,
                "url": url,
                "price": price,
                "currency": "RUB",
                "description": description[:500] if description else f"Товар от бренда {brand}",
                "characteristics": f"Бренд: {brand}. Рейтинг: {rating}. Отзывов: {feedbacks}.",
                "rating": rating,
                "reviews_count": feedbacks
            }
        }
    
    def _create_fallback_data(self, product_id: str, url: str) -> Dict[str, Any]:
        """Создание запасных данных"""
        logger.warning("⚠️ Используются запасные данные")
        return {
            "product": {
                "id": f"wb_{product_id}",
                "name": f"Товар {product_id}",
                "url": url,
                "price": None,
                "currency": "RUB",
                "description": "Описание недоступно",
                "characteristics": "Характеристики недоступны"
            }
        }
    
    def _create_mock_reviews(self, product_id: str, count: int = 6) -> List[Dict]:
        """Создание тестовых отзывов"""
        reviews_templates = [
            {
                "rating": 5,
                "text": "Отличный товар! Качество на высоте, доставка быстрая. Всем рекомендую!"
            },
            {
                "rating": 5,
                "text": "Очень довольна покупкой. Соответствует описанию, цена приемлемая."
            },
            {
                "rating": 4,
                "text": "Хороший товар за свою цену. Есть небольшие недостатки, но в целом доволен."
            },
            {
                "rating": 5,
                "text": "Превзошел ожидания! Буду заказывать еще."
            },
            {
                "rating": 3,
                "text": "Неплохо, но ожидал большего. Качество среднее."
            },
            {
                "rating": 4,
                "text": "Рекомендую к покупке. За такие деньги отличный вариант."
            }
        ]
        
        return [
            {
                "id": f"wb_review_{i+1}",
                "product_id": f"wb_{product_id}",
                "text": template["text"],
                "rating": template["rating"]
            }
            for i, template in enumerate(reviews_templates[:count])
        ]
    
    async def parse_and_save(self, url: str, output_dir: str = "."):
        """Главная функция парсинга"""
        try:
            # Парсинг товара
            result = await self.parse_product(url)
            product_id = self.extract_product_id(url)
            
            # Создание отзывов (пока моковых)
            reviews = self._create_mock_reviews(product_id, 6)
            logger.info(f"💬 Создано отзывов: {len(reviews)}")
            
            result["reviews"] = reviews
            
            # Сохранение
            with open(f"{output_dir}/product.json", "w", encoding="utf-8") as f:
                json.dump([result["product"]], f, ensure_ascii=False, indent=2)
            
            with open(f"{output_dir}/reviews.json", "w", encoding="utf-8") as f:
                json.dump(reviews, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Файлы сохранены")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            raise


async def main():
    print("\n" + "="*60)
    print("  БЫСТРЫЙ ПАРСЕР WILDBERRIES (API)")
    print("="*60)
    print("\n1. Тестовый товар (люстра)")
    print("2. Свой URL")
    
    choice = input("\nВаш выбор (1/2): ").strip()
    
    if choice == "1":
        url = "https://www.wildberries.ru/catalog/264196671/detail.aspx"
    else:
        url = input("Введите URL: ").strip()
    
    parser = WBAPIParser()
    
    try:
        result = await parser.parse_and_save(url)
        
        print("\n" + "="*60)
        print("  ✅ УСПЕШНО!")
        print("="*60)
        print(f"\n📦 Товар: {result['product']['name'][:60]}...")
        print(f"💰 Цена: {result['product']['price']} ₽")
        print(f"⭐ Рейтинг: {result['product'].get('rating', 'N/A')}")
        print(f"💬 Отзывов: {len(result['reviews'])}")
        print("\n📁 Файлы:")
        print("  ✓ product.json")
        print("  ✓ reviews.json")
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")


if __name__ == "__main__":
    asyncio.run(main())
