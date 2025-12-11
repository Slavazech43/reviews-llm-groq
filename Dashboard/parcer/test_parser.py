"""
Простая тестовая версия парсера (для проверки работоспособности)
"""

import asyncio
import json
import logging
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def simple_test():
    """Простой тест браузера"""
    
    logger.info("🚀 Запуск теста браузера...")
    
    playwright = None
    browser = None
    
    try:
        # Запуск Playwright
        playwright = await async_playwright().start()
        logger.info("✅ Playwright запущен")
        
        # Запуск браузера
        browser = await playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        logger.info("✅ Браузер запущен")
        
        # Создание страницы
        page = await browser.new_page()
        logger.info("✅ Страница создана")
        
        # Переход на простой сайт для теста
        logger.info("🌐 Загрузка тестовой страницы...")
        await page.goto("https://example.com", timeout=30000)
        logger.info("✅ Страница загружена")
        
        # Получение заголовка
        title = await page.title()
        logger.info(f"📄 Заголовок: {title}")
        
        # Тест завершен успешно
        logger.info("\n" + "="*50)
        logger.info("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        logger.info("="*50)
        logger.info("\nPlaywright работает корректно.")
        logger.info("Можно запускать полный парсер.")
        
    except Exception as e:
        logger.error(f"\n❌ Ошибка: {e}")
        logger.error("\nВозможные решения:")
        logger.error("1. Переустановите браузеры: playwright install chromium")
        logger.error("2. Проверьте права доступа")
        logger.error("3. Попробуйте запустить с sudo (если на Linux)")
        
    finally:
        if browser:
            await browser.close()
            logger.info("🔒 Браузер закрыт")
        
        if playwright:
            await playwright.stop()
            logger.info("🔒 Playwright остановлен")


async def test_wildberries():
    """Тест парсинга WB с минимальными данными"""
    
    logger.info("\n" + "="*50)
    logger.info("🛒 ТЕСТ ПАРСИНГА WILDBERRIES")
    logger.info("="*50)
    
    playwright = None
    browser = None
    
    try:
        playwright = await async_playwright().start()
        
        browser = await playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        
        page = await context.new_page()
        
        # Тестовый товар
        url = "https://www.wildberries.ru/catalog/396501168/detail.aspx"
        
        logger.info(f"📦 Загрузка товара: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        
        logger.info("⏳ Ожидание загрузки контента...")
        await asyncio.sleep(5)
        
        # Получение названия
        try:
            title_elem = await page.query_selector("h1")
            if title_elem:
                title = await title_elem.text_content()
                logger.info(f"✅ Название: {title[:50]}...")
            else:
                logger.warning("⚠️ Заголовок не найден")
                title = "Неизвестно"
        except Exception as e:
            logger.error(f"❌ Ошибка получения названия: {e}")
            title = "Ошибка"
        
        # Простой результат
        result = {
            "product": [{
                "id": "wb_test",
                "name": title.strip() if title else "Тестовый товар",
                "url": url,
                "price": 1298,
                "currency": "RUB",
                "description": "Тестовое описание",
                "characteristics": "Тестовые характеристики"
            }]
        }
        
        # Сохранение
        with open("product.json", "w", encoding="utf-8") as f:
            json.dump(result["product"], f, ensure_ascii=False, indent=2)
        
        logger.info("✅ Файл product.json создан")
        
        # Тестовые отзывы
        reviews = [
            {
                "id": "test_1",
                "product_id": "wb_test",
                "text": "Отличный товар, всем советую!"
            },
            {
                "id": "test_2",
                "product_id": "wb_test",
                "text": "Хорошее качество за свою цену"
            }
        ]
        
        with open("reviews.json", "w", encoding="utf-8") as f:
            json.dump(reviews, f, ensure_ascii=False, indent=2)
        
        logger.info("✅ Файл reviews.json создан")
        
        logger.info("\n" + "="*50)
        logger.info("✅ ТЕСТ УСПЕШНО ЗАВЕРШЕН!")
        logger.info("="*50)
        logger.info("\nСозданы файлы:")
        logger.info("  - product.json")
        logger.info("  - reviews.json")
        
    except Exception as e:
        logger.error(f"\n❌ Ошибка теста: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
    finally:
        if browser:
            await browser.close()
        if playwright:
            await playwright.stop()


async def main():
    """Главная функция"""
    
    print("\n" + "="*60)
    print("  ТЕСТИРОВАНИЕ ПАРСЕРА")
    print("="*60)
    print("\nВыберите тест:")
    print("1. Простой тест браузера (рекомендуется сначала)")
    print("2. Тест парсинга Wildberries")
    print("3. Оба теста")
    print()
    
    choice = input("Ваш выбор (1/2/3): ").strip()
    
    if choice == "1":
        await simple_test()
    elif choice == "2":
        await test_wildberries()
    elif choice == "3":
        await simple_test()
        print("\n" + "="*60 + "\n")
        await test_wildberries()
    else:
        print("❌ Неверный выбор")


if __name__ == "__main__":
    asyncio.run(main())
