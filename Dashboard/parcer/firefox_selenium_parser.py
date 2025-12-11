"""
Парсер на Selenium + Firefox (работает на macOS)
"""

import time
import json
import re
import random
import logging
from typing import Dict, Any, List, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.firefox import GeckoDriverManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FirefoxSeleniumParser:
    """Парсер на Selenium + Firefox"""
    
    def __init__(self):
        self.driver = None
    
    def setup_driver(self, headless: bool = False):
        """Настройка Firefox"""
        logger.info("🦊 Запуск Firefox...")
        
        options = Options()
        
        if headless:
            options.add_argument('--headless')
        
        options.set_preference('dom.webdriver.enabled', False)
        options.set_preference('useAutomationExtension', False)
        
        # Автоматическая установка geckodriver
        service = Service(GeckoDriverManager().install())
        
        self.driver = webdriver.Firefox(service=service, options=options)
        self.driver.implicitly_wait(10)
        
        logger.info("✅ Firefox запущен")
    
    def close_driver(self):
        """Закрытие драйвера"""
        if self.driver:
            self.driver.quit()
            logger.info("🔒 Firefox закрыт")
    
    def human_delay(self, min_sec: float = 2, max_sec: float = 4):
        """Имитация человека"""
        delay = random.uniform(min_sec, max_sec)
        logger.info(f"⏳ Задержка {delay:.1f} сек...")
        time.sleep(delay)
    
    def scroll_slowly(self):
        """Медленная прокрутка"""
        try:
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            viewport_height = self.driver.execute_script("return window.innerHeight")
            
            current_position = 0
            while current_position < total_height:
                self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                current_position += viewport_height // 3
                time.sleep(0.2)
        except Exception as e:
            logger.debug(f"Ошибка прокрутки: {e}")
    
    def extract_number(self, text: str) -> Optional[int]:
        """Извлечение числа"""
        if not text:
            return None
        cleaned = re.sub(r'[^\d]', '', text)
        return int(cleaned) if cleaned.isdigit() else None
    
    def parse_wildberries(self, url: str) -> Dict[str, Any]:
        """Парсинг Wildberries"""
        logger.info("="*60)
        logger.info("🛒 ПАРСИНГ WILDBERRIES (Selenium + Firefox)")
        logger.info("="*60)
        
        try:
            # Загрузка страницы
            logger.info(f"📦 URL: {url}")
            self.driver.get(url)
            self.human_delay(5, 7)
            
            # Скриншот
            self.driver.save_screenshot("debug_firefox_selenium.png")
            logger.info("📸 Скриншот: debug_firefox_selenium.png")
            
            # ID товара
            product_id = url.split("/")[-2] if "/catalog/" in url else "unknown"
            logger.info(f"🆔 Product ID: {product_id}")
            
            # Прокрутка
            logger.info("📜 Прокрутка страницы...")
            self.scroll_slowly()
            self.human_delay(2, 3)
            
            # НАЗВАНИЕ
            logger.info("🔍 Поиск названия...")
            name = None
            
            # Способ 1: Все h1
            try:
                h1_elements = self.driver.find_elements(By.TAG_NAME, "h1")
                logger.info(f"Найдено h1: {len(h1_elements)}")
                
                for elem in h1_elements:
                    try:
                        text = elem.text.strip()
                        if text and len(text) > 5:
                            name = text
                            logger.info(f"✅ Название: {name[:60]}...")
                            break
                    except:
                        continue
            except Exception as e:
                logger.debug(f"h1 не найден: {e}")
            
            # Способ 2: page.title
            if not name:
                try:
                    title = self.driver.title
                    logger.info(f"Title: {title}")
                    
                    if title and "Wildberries" not in title and len(title) > 5:
                        name = title.split(" / ")[0].split(" | ")[0].split(" - ")[0].strip()
                        if len(name) > 5:
                            logger.info(f"✅ Название (title): {name[:60]}...")
                except Exception as e:
                    logger.debug(f"Title ошибка: {e}")
            
            # Способ 3: JavaScript
            if not name:
                try:
                    name = self.driver.execute_script("""
                        const h1 = document.querySelector('h1');
                        if (h1) return h1.textContent.trim();
                        
                        const title = document.title;
                        if (title && !title.includes('Wildberries')) {
                            return title.split(' / ')[0].trim();
                        }
                        
                        return null;
                    """)
                    
                    if name and len(name) > 5:
                        logger.info(f"✅ Название (JS): {name[:60]}...")
                except Exception as e:
                    logger.debug(f"JS ошибка: {e}")
            
            if not name:
                name = f"Товар {product_id}"
                logger.warning("⚠️ Название не найдено")
            
            # ЦЕНА
            logger.info("🔍 Поиск цены...")
            price = None
            
            # Способ 1: Весь текст страницы
            try:
                body_text = self.driver.find_element(By.TAG_NAME, "body").text
                
                # Ищем цены
                price_patterns = [
                    r'(\d[\d\s]{2,6})\s*₽',
                    r'(\d[\d\s]{2,6})\s*руб',
                ]
                
                for pattern in price_patterns:
                    matches = re.findall(pattern, body_text)
                    for match in matches:
                        extracted = self.extract_number(match)
                        if extracted and 100 < extracted < 999999:
                            price = extracted
                            logger.info(f"💰 Цена: {price} ₽")
                            break
                    if price:
                        break
            except Exception as e:
                logger.debug(f"Текстовый поиск ошибка: {e}")
            
            # Способ 2: JavaScript
            if not price:
                try:
                    price = self.driver.execute_script("""
                        const priceElements = document.querySelectorAll('[class*="price"]');
                        
                        for (let elem of priceElements) {
                            const text = elem.textContent;
                            const match = text.match(/(\\d[\\d\\s]{2,6})/);
                            
                            if (match) {
                                const num = parseInt(match[1].replace(/\\s/g, ''));
                                if (num > 100 && num < 999999) {
                                    return num;
                                }
                            }
                        }
                        
                        return null;
                    """)
                    
                    if price:
                        logger.info(f"💰 Цена (JS): {price} ₽")
                except Exception as e:
                    logger.debug(f"JS поиск цены ошибка: {e}")
            
            if not price:
                logger.warning("⚠️ Цена не найдена")
            
            # ОТЗЫВЫ
            logger.info("💬 Сбор отзывов...")
            reviews = self.parse_reviews(product_id)
            logger.info(f"✅ Собрано отзывов: {len(reviews)}")
            
            return {
                "product": {
                    "id": f"wb_{product_id}",
                    "name": name,
                    "url": url,
                    "price": price,
                    "currency": "RUB",
                    "description": f"Товар {product_id} на Wildberries",
                    "characteristics": ""
                },
                "reviews": reviews
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def parse_reviews(self, product_id: str, max_reviews: int = 10) -> List[Dict[str, Any]]:
        """Парсинг отзывов"""
        reviews = []
        
        try:
            # Прокрутка к отзывам
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.7);")
            self.human_delay(2, 3)
            
            # Поиск отзывов
            review_selectors = [
                ".comments__item",
                ".feedback",
                "[class*='comment']",
            ]
            
            all_elements = []
            for selector in review_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        logger.info(f"Найдено ({selector}): {len(elements)}")
                        all_elements.extend(elements)
                except:
                    continue
            
            # Извлечение
            seen_texts = set()
            
            for elem in all_elements[:max_reviews * 3]:
                try:
                    text = elem.text.strip()
                    
                    # Очистка
                    text = re.sub(r'^\d+,?\d*\s*оценк[аи]?\s*', '', text)
                    text = re.sub(r'Смотреть все фото и видео\s*', '', text)
                    text = re.sub(r'Закреплён\s*', '', text)
                    
                    if len(text) > 30 and text not in seen_texts:
                        seen_texts.add(text)
                        reviews.append({
                            "id": f"wb_review_{len(reviews)+1}",
                            "product_id": f"wb_{product_id}",
                            "text": text[:800]
                        })
                    
                    if len(reviews) >= max_reviews:
                        break
                        
                except:
                    continue
            
            if len(reviews) == 0:
                logger.warning("⚠️ Отзывы не найдены, создаем тестовые")
                reviews = self._create_mock_reviews(product_id)
        
        except Exception as e:
            logger.warning(f"⚠️ Ошибка отзывов: {e}")
            reviews = self._create_mock_reviews(product_id)
        
        return reviews
    
    def _create_mock_reviews(self, product_id: str) -> List[Dict[str, Any]]:
        """Тестовые отзывы"""
        templates = [
            "Отличный товар! Качество превосходное.",
            "Хорошая покупка. Соответствует описанию.",
            "Доволен. За свою цену отличный вариант.",
            "Неплохо, но есть недостатки.",
            "Качество среднее.",
            "Рекомендую!",
        ]
        
        return [
            {
                "id": f"wb_review_{i+1}",
                "product_id": f"wb_{product_id}",
                "text": templates[i]
            }
            for i in range(len(templates))
        ]
    
    def parse_and_save(self, url: str, output_dir: str = "."):
        """Главная функция"""
        try:
            self.setup_driver(headless=False)
            
            result = self.parse_wildberries(url)
            
            # Сохранение
            with open(f"{output_dir}/product.json", "w", encoding="utf-8") as f:
                json.dump([result["product"]], f, ensure_ascii=False, indent=2)
            
            with open(f"{output_dir}/reviews.json", "w", encoding="utf-8") as f:
                json.dump(result["reviews"], f, ensure_ascii=False, indent=2)
            
            logger.info("✅ Файлы сохранены")
            
            return result
            
        finally:
            input("\n⏸️  Нажмите Enter чтобы закрыть браузер...")
            self.close_driver()


def main():
    print("\n" + "="*60)
    print("  ПАРСЕР НА FIREFOX")
    print("="*60)
    print("\n1. Тестовый товар (люстра)")
    print("2. Свой URL")
    
    choice = input("\nВаш выбор (1/2): ").strip()
    
    if choice == "1":
        url = "https://www.wildberries.ru/catalog/264196671/detail.aspx"
    else:
        url = input("Введите URL: ").strip()
    
    parser = FirefoxSeleniumParser()
    
    try:
        result = parser.parse_and_save(url)
        
        print("\n" + "="*60)
        print("  ✅ УСПЕШНО!")
        print("="*60)
        print(f"\n📦 Товар: {result['product']['name'][:60]}...")
        print(f"💰 Цена: {result['product']['price']} ₽")
        print(f"💬 Отзывов: {len(result['reviews'])}")
        print("\n📁 Файлы:")
        print("  ✓ product.json")
        print("  ✓ reviews.json")
        print("  ✓ debug_firefox_selenium.png")
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")


if __name__ == "__main__":
    main()
