#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестирование SERP API подключения
"""
import asyncio
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Импортируем наш веб-поисковик
from utils.web_search import WebSearcher

async def test_serp_api():
    """Тестирование SERP API"""
    
    # Проверяем наличие API ключа
    api_key = os.getenv('SERP_API_KEY')
    print(f"[KEY] SERP API Key: {api_key[:10] + '...' + api_key[-5:] if api_key and len(api_key) > 15 else 'НЕ НАСТРОЕН'}")
    
    if not api_key or api_key == 'your_serp_api_key':
        print("❌ SERP API ключ не настроен!")
        print("📝 Получите ключ на https://serpapi.com/")
        print("🔧 Обновите файл .env: SERP_API_KEY=ваш_ключ")
        return
    
    # Создаем поисковик
    searcher = WebSearcher()
    
    print("\n🧪 Тестируем подключение к SERP API...")
    
    try:
        # Тест обычного поиска
        print("\n1. 📊 Тестируем обычный поиск...")
        async with searcher:
            results = await searcher.search("Москва погода", num_results=3)
            
            if results:
                print(f"✅ Обычный поиск работает! Найдено {len(results)} результатов:")
                for i, result in enumerate(results[:3], 1):
                    title = result.get('title', 'Без названия')[:50]
                    source = result.get('source', 'web')
                    print(f"   {i}. [{source}] {title}...")
            else:
                print("❌ Обычный поиск не вернул результатов")
        
        # Тест поиска новостей
        print("\n2. 📰 Тестируем поиск новостей...")
        async with searcher:
            news_results = await searcher.search_news("технологии", num_results=2)
            
            if news_results:
                print(f"✅ Поиск новостей работает! Найдено {len(news_results)} результатов:")
                for i, result in enumerate(news_results[:2], 1):
                    title = result.get('title', 'Без названия')[:50]
                    source = result.get('source', 'news')
                    print(f"   {i}. [{source}] {title}...")
            else:
                print("❌ Поиск новостей не вернул результатов")
        
        # Тест быстрого поиска
        print("\n3. ⚡ Тестируем быстрый поиск...")
        formatted_result = await searcher.quick_search("Python programming")
        
        if "результаты веб-поиска" in formatted_result.lower():
            print("✅ Быстрый поиск работает!")
            print(f"📄 Длина результата: {len(formatted_result)} символов")
        else:
            print("❌ Быстрый поиск вернул неожиданный результат")
            print(f"📄 Результат: {formatted_result[:100]}...")
        
        # Тест умного поиска
        print("\n4. 🧠 Тестируем умный поиск...")
        smart_result = await searcher.search_and_summarize("искусственный интеллект новости")
        
        if smart_result and len(smart_result) > 50:
            print("✅ Умный поиск работает!")
            print(f"📄 Длина результата: {len(smart_result)} символов")
        else:
            print("❌ Умный поиск вернул слишком короткий результат")
        
        print("\n🎉 Все тесты SERP API завершены!")
        
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании SERP API: {e}")
        print("🔍 Проверьте:")
        print("   - Правильность API ключа")  
        print("   - Доступность интернета")
        print("   - Лимиты на аккаунте SerpApi")

if __name__ == "__main__":
    print("🔍 SERP API Тестирование")
    print("=" * 40)
    
    asyncio.run(test_serp_api())