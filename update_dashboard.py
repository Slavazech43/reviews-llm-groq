#!/usr/bin/env python3
"""
Скрипт для копирования JSON файлов в dashboard
Автоматически обновляет данные в React приложении
"""

import os
import shutil
import json
from pathlib import Path


def find_dashboard_directory():
    """Поиск папки dashboard"""
    possible_paths = [
        './audience-lens-app/public',
        '../audience-lens-app/public',
        './Dashboard/audience-lens-app/public',
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # Создаем если не существует
    if os.path.exists('./audience-lens-app'):
        public_dir = './audience-lens-app/public'
        os.makedirs(public_dir, exist_ok=True)
        return public_dir
    
    return None


def copy_files_to_dashboard():
    """Копирование JSON файлов в dashboard"""
    
    print("\n" + "="*60)
    print("  📦 КОПИРОВАНИЕ ФАЙЛОВ В DASHBOARD")
    print("="*60)
    
    # Файлы для копирования
    files_to_copy = [
        'audience_analysis_results.json',
        'product.json',
        'reviews.json',
        'results.json'  # Добавлен results.json
    ]
    
    # Поиск dashboard
    dashboard_dir = find_dashboard_directory()
    
    if not dashboard_dir:
        print("\n❌ Папка dashboard не найдена!")
        print("\nСоздайте приложение:")
        print("  npm create vite@latest audience-lens-app -- --template react")
        print("  cd audience-lens-app")
        print("  npm install")
        return False
    
    print(f"\n✅ Dashboard найден: {dashboard_dir}")
    
    # Копирование файлов
    copied = []
    missing = []
    
    for filename in files_to_copy:
        if os.path.exists(filename):
            dest = os.path.join(dashboard_dir, filename)
            shutil.copy2(filename, dest)
            print(f"✅ {filename} → {dest}")
            copied.append(filename)
        else:
            print(f"⚠️  {filename} не найден")
            missing.append(filename)
    
    # Итог
    print(f"\n" + "="*60)
    print(f"  📊 СТАТУС")
    print("="*60)
    print(f"✅ Скопировано: {len(copied)} файлов")
    if missing:
        print(f"⚠️  Отсутствуют: {', '.join(missing)}")
    
    # Инструкции
    if copied:
        print(f"\n🚀 Запустите dashboard:")
        print(f"  cd audience-lens-app")
        print(f"  npm run dev")
        print(f"\nИли обновите страницу если уже запущен!")
    
    return len(copied) > 0


def create_sample_data():
    """Создание примеров данных если их нет"""
    
    print("\n📝 Создание примеров данных...")
    
    # product.json
    if not os.path.exists('product.json'):
        product = [{
            "id": "wb_drill",
            "name": "Дрель-шуруповерт аккумуляторный 2 в 1",
            "url": "https://www.wildberries.ru/catalog/396501168/detail.aspx",
            "price": 1298,
            "currency": "RUB",
            "description": "Легкий и удобный шуруповерт",
            "characteristics": "Li-Ion, 2 АКБ"
        }]
        with open('product.json', 'w', encoding='utf-8') as f:
            json.dump(product, f, ensure_ascii=False, indent=2)
        print("✅ product.json создан")
    
    # reviews.json
    if not os.path.exists('reviews.json'):
        reviews = [
            {
                "id": "wb_1",
                "product_id": "wb_drill",
                "review": "Отличный товар! Качество супер."
            },
            {
                "id": "wb_2",
                "product_id": "wb_drill",
                "review": "Хорошая покупка за свои деньги."
            }
        ]
        with open('reviews.json', 'w', encoding='utf-8') as f:
            json.dump(reviews, f, ensure_ascii=False, indent=2)
        print("✅ reviews.json создан")
    
    # results.json
    if not os.path.exists('results.json'):
        results = [
            {
                "id": "wb_1",
                "product_id": "wb_drill",
                "review_text": "Отличный товар! Качество супер.",
                "overall_sentiment": "positive",
                "criteria_scores": {
                    "quality": 5.0,
                    "price": 4.5,
                    "delivery": 4.0,
                    "packaging": 4.5
                },
                "key_points": ["Высокое качество", "Соответствует описанию"]
            },
            {
                "id": "wb_2",
                "product_id": "wb_drill",
                "review_text": "Хорошая покупка за свои деньги.",
                "overall_sentiment": "positive",
                "criteria_scores": {
                    "quality": 4.0,
                    "price": 5.0,
                    "delivery": 4.0,
                    "packaging": 4.0
                },
                "key_points": ["Хорошая цена"]
            }
        ]
        with open('results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print("✅ results.json создан")
    
    # audience_analysis_results.json
    if not os.path.exists('audience_analysis_results.json'):
        analysis = {
            "product": {
                "id": "wb_drill",
                "name": "Дрель-шуруповерт аккумуляторный 2 в 1"
            },
            "segments": [
                {
                    "name": "Домашние мастера",
                    "size": 45,
                    "percentage": 45,
                    "description": "Люди для домашнего ремонта",
                    "pain_points": ["Нужен надежный инструмент", "Ограниченный бюджет"],
                    "desires": ["Качество", "Доступная цена"],
                    "criteria_scores": {
                        "quality": 4.2,
                        "price": 4.5,
                        "delivery": 4.0
                    }
                }
            ],
            "recommendations": [
                "Добавить видео с примерами использования",
                "Указать гарантию в описании",
                "Сделать акцент на соотношение цена-качество"
            ]
        }
        with open('audience_analysis_results.json', 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        print("✅ audience_analysis_results.json создан")


def main():
    """Главная функция"""
    
    # Создаем примеры если нужно
    create_sample_data()
    
    # Копируем файлы
    success = copy_files_to_dashboard()
    
    if success:
        print("\n✨ Готово! Данные обновлены в dashboard!")
    else:
        print("\n⚠️  Не удалось скопировать файлы")


if __name__ == "__main__":
    main()