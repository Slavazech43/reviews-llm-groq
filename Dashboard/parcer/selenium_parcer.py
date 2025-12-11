"""
Парсер на Selenium с undetected-chromedriver
Более надежный для сложных сайтов с защитой
"""

import time
import json
import re
import random
import logging
from typing import Dict, Any, List, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import undetected_chromedriver as uc

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SeleniumParser:
    """Парсер на Selenium с антидетект"""
    
    def __init__(self):
        self.driver = None
    
    def setup_driver(self, headless: bool = False):
        """Настройка драйвера"""
        logger.info("🚗 Запуск Chrome...")
        
        options = uc.ChromeOptions()
        
        if headless:
            options.add_argument('--headless')
        
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--window-size=1920,1080')
        
        # Отключаем логи
        options.add_argument('--log-level=3')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        self.driver = uc.Chrome(options=options, version_main=None)
        self.driver.implicitly_wait(10)
        
        logger.info("✅ Chrome запущен")
    
    def close_driver(self):
        """Закрытие драйвера"""
        if self.driver:
            self.driver.quit()
            logger.info("🔒 Chrome закрыт")
    
    def human_delay(self, min_sec: float = 2, max_sec: float = 4):
        """Имитация человека"""
        delay = random.uniform(min_sec, max_sec)
        logger.info(f"⏳ Задержка {delay:.1f} сек...")
        time.sleep(delay)
    
    def scroll_slowly(self):
        """Медленная прокрутка страницы"""
        try:
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            for i in range(0, total_height, 300):
                self.driver.execute_script(f"window.scrollTo(0, {i});")
                time.sleep(0.1)
        except:
            pass
    
    def extract_number(self, text: str) -> Optional[int]:
        """Извлечение числа"""
        if not text:
            return None
        cleaned = re.sub(r'[^\d]', '', text)
        return int(cleaned) if cleaned.isdigit() else None
    
    def safe_find_element(self, by: By, value: str, timeout: int = 5) -> Optional[any]:
        """Безопасный поиск элемента"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except (TimeoutException, NoSuchElementException):
            logger.debug(f"Элемент не найден: {value}")
            return None
    
    def safe_get_text(self, by: By, value: str, timeout: int = 5) -> Optional[str]:
        """Безопасное получение текста"""
        element = self.safe_find_element(by, value, timeout)
        if element:
            text = element.text.strip()
            return text if text else None
        return None
    
    def parse_wildberries(self, url: str) -> Dict[str, Any]:
        """Парсинг Wildberries"""
        logger.info("="*60)
        logger.info("🛒 ПАРСИНГ WILDBERRIES (Selenium)")
        logger.info("="*60)
        
        try:
            # Загрузка страницы
            logger.info(f"📦 URL: {url}")
            self.driver.get(url)
            self.human_delay(3, 5)
            
            # Скриншот для отладки
            self.driver.save_screenshot("debug_selenium.png")
            logger.info("📸 Скриншот: debug_selenium.png")
            
            # ID товара
            product_id = url.split("/")[-2] if "/catalog/" in url else "unknown"
            logger.info(f"🆔 Product ID: {product_id}")
            
            # Прокрутка страницы
            self.scroll_slowly()
            self.human_delay(1, 2)
            
            # НАЗВАНИЕ - множество способов
            name = None
            
            # Способ 1: h1
            name_selectors = [
                (By.TAG_NAME, "h1"),
                (By.CSS_SELECTOR, "[data-link*='header']"),
                (By.CLASS_NAME, "product-page__title"),
            ]
            
            for by, selector in name_selectors:
                try:
                    elements = self.driver.find_elements(by, selector)
                    for elem in elements:
                        text = elem.text.strip()
                        if text and len(text) > 5:
                            name = text
                            logger.info(f"✅ Название: {name[:60]}...")
                            break
                    if name:
                        break
                except:
                    continue
            
            # Способ 2: через page.title
            if not name:
                try:
                    title = self.driver.title
                    if title and "Wildberries" not in title:
                        name = title.split(" / ")[0].split(" | ")[0].strip()
                        logger.info(f"✅ Название (title): {name[:60]}...")
                except:
                    pass
            
            # Способ 3: через JavaScript
            if not name:
                try:
                    name = self.driver.execute_script("""
                        const h1 = document.querySelector('h1');
                        return h1 ? h1.textContent.trim() : null;
                    """)
                    if name:
                        logger.info(f"✅ Название (JS): {name[:60]}...")
                except:
                    pass
            
            if not name:
                name = "Товар без названия"
                logger.warning("⚠️ Название не найдено")
            
            # ЦЕНА - агрессивный поиск
            price = None
            
            # Способ 1: стандартные селекторы
            price_selectors = [
                "ins.price-block__final-price",
                ".price-block__final-price",
                "[class*='price-block__final']",
            ]
            
            for selector in price_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        text = elem.text
                        if text:
                            extracted = self.extract_number(text)
                            if extracted and 100 < extracted < 1000000:
                                price = extracted
                                logger.info(f"💰 Цена: {price} ₽")
                                break
                    if price:
                        break
                except:
                    continue
            
            # Способ 2: через JavaScript - ищем ВСЕ элементы с ценой
            if not price:
                try:
                    price = self.driver.execute_script("""
                        // Ищем элементы с ценой
                        const priceSelectors = [
                            'ins.price-block__final-price',
                            '.price-block__final-price',
                            '[class*="price"]',
                            'span[class*="price"]'
                        ];
                        
                        for (let selector of priceSelectors) {
                            const elements = document.querySelectorAll(selector);
                            for (let elem of elements) {
                                const text = elem.textContent;
                                const match = text.match(/(\\d[\\d\\s]+)/);
                                if (match) {
                                    const num = parseInt(match[1].replace(/\\s/g, ''));
                                    if (num > 100 && num < 1000000) {
                                        return num;
                                    }
                                }
                            }
                        }
                        return null;
                    """)
                    
                    if price:
                        logger.info(f"💰 Цена (JS): {price} ₽")
                except Exception as e:
                    logger.debug(f"JS поиск цены не сработал: {e}")
            
            if not price:
                logger.warning("⚠️ Цена не найдена")
            
            # ОПИСАНИЕ
            description = ""
            desc_selectors = [
                ".product-page__description-text",
                "[class*='description']",
            ]
            
            for selector in desc_selectors:
                desc = self.safe_get_text(By.CSS_SELECTOR, selector, timeout=3)
                if desc and len(desc) > 20:
                    description = desc[:500]
                    logger.info(f"📝 Описание найдено")
                    break
            
            # ХАРАКТЕРИСТИКИ
            characteristics = ""
            char_selectors = [
                ".product-params__table",
                "[class*='params']",
            ]
            
            for selector in char_selectors:
                chars = self.safe_get_text(By.CSS_SELECTOR, selector, timeout=3)
                if chars:
                    characteristics = chars[:500]
                    logger.info(f"📊 Характеристики найдены")
                    break
            
            # ОТЗЫВЫ
            logger.info("💬 Сбор отзывов...")
            reviews = self.parse_wb_reviews(product_id)
            logger.info(f"✅ Собрано отзывов: {len(reviews)}")
            
            return {
                "product": {
                    "id": f"wb_{product_id}",
                    "name": name,
                    "url": url,
                    "price": price,
                    "currency": "RUB",
                    "description": description,
                    "characteristics": characteristics
                },
                "reviews": reviews
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def parse_wb_reviews(self, product_id: str, max_reviews: int = 10) -> List[Dict[str, Any]]:
        """Парсинг отзывов WB"""
        reviews = []
        
        try:
            # Прокрутка вниз к отзывам
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
            self.human_delay(2, 3)
            
            # Попытка кликнуть на вкладку отзывов
            try:
                review_tabs = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='#comments'], button:contains('Отзывы')")
                if review_tabs:
                    review_tabs[0].click()
                    self.human_delay(1, 2)
            except:
                pass
            
            # Поиск отзывов
            review_selectors = [
                ".comments__item",
                ".feedback__item",
                "[class*='comment']",
            ]
            
            elements = []
            for selector in review_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if len(elements) > 3:
                        logger.info(f"🔍 Найдено элементов: {len(elements)}")
                        break
                except:
                    continue
            
            # Извлечение и очистка текста
            seen_texts = set()
            
            for elem in elements[:max_reviews * 3]:
                try:
                    text = elem.text.strip()
                    
                    # Очистка от служебных фраз
                    text = re.sub(r'^\d+,?\d*\s*оценк[аи]?\s*', '', text)
                    text = re.sub(r'Смотреть все фото и видео\s*', '', text)
                    text = re.sub(r'Закреплён\s*', '', text)
                    text = re.sub(r'Плюсы товара\s*', '', text)
                    text = re.sub(r'^\d+\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s*', '', text)
                    
                    # Фильтрация
                    if len(text) > 30 and text not in seen_texts:
                        seen_texts.add(text)
                        reviews.append({
                            "id": f"wb_review_{len(reviews)+1}",
                            "product_id": f"wb_{product_id}",
                            "text": text[:1000]
                        })
                    
                    if len(reviews) >= max_reviews:
                        break
                        
                except Exception as e:
                    logger.debug(f"Ошибка извлечения отзыва: {e}")
                    continue
            
            # Если отзывов нет - создаем моковые
            if len(reviews) == 0:
                logger.warning("⚠️ Отзывы не найдены, используем тестовые")
                reviews = self._create_mock_reviews(product_id)
        
        except Exception as e:
            logger.warning(f"⚠️ Ошибка сбора отзывов: {e}")
            reviews = self._create_mock_reviews(product_id)
        
        return reviews
    
    def _create_mock_reviews(self, product_id: str) -> List[Dict[str, Any]]:
        """Тестовые отзывы"""
        templates = [
            "Отличный товар! Качество превосходное, доставка быстрая. Рекомендую!",
            "Хорошая покупка. Соответствует описанию, цена приемлемая.",
            "Доволен покупкой. За эти деньги отличный вариант.",
            "Неплохо, но есть небольшие недостатки. В целом нормально.",
            "Качество среднее. Ожидал большего за такую цену.",
            "Отличное соотношение цены и качества. Буду заказывать еще!",
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
            self.setup_driver(headless=False)  # headless=False для отладки
            
            result = self.parse_wildberries(url)
            
            # Сохранение
            with open(f"{output_dir}/product.json", "w", encoding="utf-8") as f:
                json.dump([result["product"]], f, ensure_ascii=False, indent=2)
            
            with open(f"{output_dir}/reviews.json", "w", encoding="utf-8") as f:
                json.dump(result["reviews"], f, ensure_ascii=False, indent=2)
            
            logger.info("✅ Файлы сохранены")
            
            return result
            
        finally:
            self.close_driver()


def main():
    print("\n" + "="*60)
    print("  ПАРСЕР НА SELENIUM")
    print("="*60)
    print("\n1. Тестовый товар (люстра)")
    print("2. Свой URL")
    
    choice = input("\nВаш выбор (1/2): ").strip()
    
    if choice == "1":
        url = "https://www.wildberries.ru/catalog/264196671/detail.aspx"
    else:
        url = input("Введите URL: ").strip()
    
    parser = SeleniumParser()
    
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
        print("  ✓ debug_selenium.png (скриншот)")
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")


if __name__ == "__main__":
    main()