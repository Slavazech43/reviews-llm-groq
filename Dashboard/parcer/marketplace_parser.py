"""
Парсер для Wildberries и Ozon
Автоматически создает product.json и reviews.json для Audience Lens
"""

import asyncio
import json
import re
import random
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright, Page, Browser
from urllib.parse import quote

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MarketplaceParser:
    """Универсальный парсер для маркетплейсов"""
    
    def __init__(self, marketplace: str = "wb"):
        """
        Args:
            marketplace: 'wb' для Wildberries или 'ozon' для Ozon
        """
        self.marketplace = marketplace.lower()
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
    async def human_delay(self, min_sec=1, max_sec=3):
        """Случайная задержка для имитации человека"""
        await asyncio.sleep(random.uniform(min_sec, max_sec))
    
    async def setup_browser(self):
        """Запуск браузера с антидетект настройками"""
        logger.info("Запуск браузера...")
        
        self.playwright = await async_playwright().start()
        
        self.browser = await self.playwright.chromium.launch(
            headless=True,  # Измените на False для отладки
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ]
        )
        
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            java_script_enabled=True,
            ignore_https_errors=True
        )
        
        # Маскировка автоматизации
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { 
                get: () => undefined 
            });
            
            Object.defineProperty(navigator, 'plugins', { 
                get: () => [1, 2, 3, 4, 5] 
            });
        """)
        
        self.page = await self.context.new_page()
        self.page.set_default_timeout(30000)  # Увеличил до 30 секунд
        self.page.set_default_navigation_timeout(60000)  # Увеличил до 60 секунд
        
        logger.info("Браузер успешно запущен")
    
    async def close_browser(self):
        """Закрытие браузера"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Браузер закрыт")
    
    async def parse_wildberries(self, product_url: str) -> Dict[str, Any]:
        """Парсинг товара с Wildberries"""
        logger.info(f"Парсинг WB: {product_url}")
        
        try:
            await self.page.goto(product_url, wait_until="domcontentloaded", timeout=60000)
            await self.human_delay(3, 5)  # Увеличил задержку
        except Exception as e:
            logger.error(f"Ошибка загрузки страницы: {e}")
            # Попытка еще раз
            await self.human_delay(2, 3)
            await self.page.goto(product_url, wait_until="networkidle", timeout=60000)
        
        # Извлечение данных
        product_id = product_url.split("/")[-2] if "/catalog/" in product_url else "unknown"
        
        # Название
        name = await self._get_text("h1")
        
        # Цена
        price_text = await self._get_text(".price-block__final-price")
        price = self._extract_number(price_text) if price_text else None
        
        # Описание
        description = await self._get_text(".product-page__description-text")
        
        # Характеристики
        characteristics = await self._parse_wb_characteristics()
        
        # Отзывы
        reviews = await self._parse_wb_reviews()
        
        return {
            "product": {
                "id": f"wb_{product_id}",
                "name": name or "Неизвестно",
                "url": product_url,
                "price": price,
                "currency": "RUB",
                "description": description or "",
                "characteristics": characteristics
            },
            "reviews": reviews
        }
    
    async def parse_ozon(self, product_url: str) -> Dict[str, Any]:
        """Парсинг товара с Ozon"""
        logger.info(f"Парсинг Ozon: {product_url}")
        
        try:
            await self.page.goto(product_url, wait_until="domcontentloaded", timeout=60000)
            await self.human_delay(3, 5)
        except Exception as e:
            logger.error(f"Ошибка загрузки страницы: {e}")
            await self.human_delay(2, 3)
            await self.page.goto(product_url, wait_until="networkidle", timeout=60000)
        
        # Ожидание загрузки
        try:
            await self.page.wait_for_selector("h1", timeout=15000)
        except:
            logger.warning("Заголовок не загрузился")
        
        product_id = product_url.split("/")[-1].split("-")[-1] if "/product/" in product_url else "unknown"
        
        # Название
        name = await self._get_text("h1")
        
        # Цена
        price = await self._parse_ozon_price()
        
        # Описание
        description = await self._parse_ozon_description()
        
        # Характеристики
        characteristics = await self._parse_ozon_characteristics()
        
        # Отзывы
        reviews = await self._parse_ozon_reviews()
        
        return {
            "product": {
                "id": f"ozon_{product_id}",
                "name": name or "Неизвестно",
                "url": product_url,
                "price": price,
                "currency": "RUB",
                "description": description or "",
                "characteristics": characteristics
            },
            "reviews": reviews
        }
    
    async def _get_text(self, selector: str) -> Optional[str]:
        """Получение текста из элемента"""
        try:
            element = await self.page.query_selector(selector)
            if element:
                text = await element.text_content()
                return text.strip() if text else None
        except:
            pass
        return None
    
    def _extract_number(self, text: str) -> Optional[int]:
        """Извлечение числа из текста"""
        if not text:
            return None
        
        # Удаляем все кроме цифр
        cleaned = re.sub(r'[^\d]', '', text)
        
        if cleaned.isdigit():
            return int(cleaned)
        return None
    
    async def _parse_wb_characteristics(self) -> str:
        """Парсинг характеристик WB"""
        try:
            # Пытаемся найти блок с характеристиками
            characteristics_selectors = [
                ".product-params__table",
                "[data-link='text{:product-details/product-params}']",
                ".params"
            ]
            
            for selector in characteristics_selectors:
                element = await self.page.query_selector(selector)
                if element:
                    text = await element.text_content()
                    return text.strip() if text else ""
        except:
            pass
        
        return ""
    
    async def _parse_ozon_price(self) -> Optional[int]:
        """Парсинг цены Ozon (из статьи)"""
        content = await self.page.content()
        
        # Поиск в JSON
        json_patterns = [
            r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
            r'<script[^>]*data-widget[^>]*>([^<]*)',
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            
            for match in matches:
                try:
                    if isinstance(match, str) and match.startswith('{'):
                        data = json.loads(match)
                        
                        def find_price(obj):
                            if isinstance(obj, dict):
                                for key, value in obj.items():
                                    if key in ['price', 'currentPrice', 'finalPrice', 'amount']:
                                        if isinstance(value, (int, float)):
                                            return int(value)
                                        elif isinstance(value, str) and value.isdigit():
                                            return int(value)
                                    
                                    if isinstance(value, (dict, list)):
                                        result = find_price(value)
                                        if result:
                                            return result
                            
                            elif isinstance(obj, list):
                                for item in obj:
                                    result = find_price(item)
                                    if result:
                                        return result
                            
                            return None
                        
                        found_price = find_price(data)
                        if found_price:
                            return found_price
                except:
                    continue
        
        # Поиск через селекторы
        price_selectors = [
            "[data-widget='webPrice']",
            "[data-widget='price']",
            ".price",
        ]
        
        for selector in price_selectors:
            try:
                price_elem = await self.page.query_selector(selector)
                if price_elem:
                    price_text = await price_elem.text_content()
                    if price_text:
                        return self._extract_number(price_text)
            except:
                continue
        
        return None
    
    async def _parse_ozon_description(self) -> str:
        """Парсинг описания Ozon"""
        description_selectors = [
            "[data-widget='webDescription']",
            ".product-description",
            "[class*='description']"
        ]
        
        for selector in description_selectors:
            text = await self._get_text(selector)
            if text:
                return text
        
        return ""
    
    async def _parse_ozon_characteristics(self) -> str:
        """Парсинг характеристик Ozon"""
        characteristics_selectors = [
            "[data-widget='webCharacteristics']",
            ".product-characteristics",
            "[class*='characteristics']"
        ]
        
        for selector in characteristics_selectors:
            text = await self._get_text(selector)
            if text:
                return text
        
        return ""
    
    async def _parse_wb_reviews(self, max_reviews: int = 10) -> List[Dict[str, Any]]:
        """Парсинг отзывов WB"""
        reviews = []
        
        try:
            # Попытка найти секцию с отзывами
            review_selectors = [
                ".comments__item",
                "[data-link='text{:comments}']",
                ".feedback"
            ]
            
            for selector in review_selectors:
                elements = await self.page.query_selector_all(selector)
                
                if elements:
                    for i, elem in enumerate(elements[:max_reviews]):
                        try:
                            text = await elem.text_content()
                            if text:
                                reviews.append({
                                    "id": f"wb_review_{i+1}",
                                    "product_id": "wb_product",
                                    "text": text.strip()
                                })
                        except:
                            continue
                    
                    if reviews:
                        break
        except Exception as e:
            logger.warning(f"Ошибка парсинга отзывов WB: {e}")
        
        return reviews
    
    async def _parse_ozon_reviews(self, max_reviews: int = 10) -> List[Dict[str, Any]]:
        """Парсинг отзывов Ozon"""
        reviews = []
        
        try:
            review_selectors = [
                "[data-widget='webReviews']",
                ".review-item",
                "[class*='review']"
            ]
            
            for selector in review_selectors:
                elements = await self.page.query_selector_all(selector)
                
                if elements:
                    for i, elem in enumerate(elements[:max_reviews]):
                        try:
                            text = await elem.text_content()
                            if text:
                                reviews.append({
                                    "id": f"ozon_review_{i+1}",
                                    "product_id": "ozon_product",
                                    "text": text.strip()
                                })
                        except:
                            continue
                    
                    if reviews:
                        break
        except Exception as e:
            logger.warning(f"Ошибка парсинга отзывов Ozon: {e}")
        
        return reviews
    
    async def parse_and_save(self, product_url: str, output_dir: str = "."):
        """Главная функция: парсинг и сохранение в JSON"""
        try:
            await self.setup_browser()
            
            # Определяем маркетплейс по URL
            if "wildberries" in product_url or "wb.ru" in product_url:
                result = await self.parse_wildberries(product_url)
            elif "ozon" in product_url:
                result = await self.parse_ozon(product_url)
            else:
                raise ValueError("Неподдерживаемый маркетплейс. Используйте WB или Ozon URL")
            
            # Сохранение product.json
            product_data = [result["product"]]
            with open(f"{output_dir}/product.json", "w", encoding="utf-8") as f:
                json.dump(product_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Сохранено: {output_dir}/product.json")
            
            # Сохранение reviews.json
            reviews_data = result["reviews"]
            with open(f"{output_dir}/reviews.json", "w", encoding="utf-8") as f:
                json.dump(reviews_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Сохранено: {output_dir}/reviews.json")
            logger.info(f"📊 Собрано отзывов: {len(reviews_data)}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга: {e}")
            raise
        
        finally:
            await self.close_browser()


async def main():
    """Пример использования"""
    
    # URL товара (замените на свой)
    product_url = "https://www.wildberries.ru/catalog/396501168/detail.aspx"
    # или
    # product_url = "https://www.ozon.ru/product/..."
    
    parser = MarketplaceParser()
    
    try:
        result = await parser.parse_and_save(product_url)
        
        print("\n" + "="*50)
        print("✅ ПАРСИНГ ЗАВЕРШЕН")
        print("="*50)
        print(f"Товар: {result['product']['name']}")
        print(f"Цена: {result['product']['price']} ₽")
        print(f"Отзывов собрано: {len(result['reviews'])}")
        print("\nФайлы созданы:")
        print("  - product.json")
        print("  - reviews.json")
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")


if __name__ == "__main__":
    asyncio.run(main())
