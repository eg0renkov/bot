# -*- coding: utf-8 -*-
"""
Простое тестирование SERP API
"""
import asyncio
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Импортируем наш веб-поисковик
from utils.web_search import WebSearcher

async def test_serp():
    """Простой тест SERP API"""
    
    # Проверяем наличие API ключа
    api_key = os.getenv('SERP_API_KEY')
    print(f"API Key: {api_key}")
    
    if not api_key or api_key == 'your_serp_api_key':
        print("ОШИБКА: SERP API ключ не настроен!")
        print("Получите ключ на https://serpapi.com/")
        print("Обновите .env: SERP_API_KEY=ваш_ключ")
        return
    
    # Тестируем поиск
    searcher = WebSearcher()
    print("Тестируем SERP API...")
    
    try:
        async with searcher:
            results = await searcher.search("Python", num_results=2)
            
            if results:
                print(f"УСПЕХ! Найдено {len(results)} результатов:")
                for i, result in enumerate(results, 1):
                    title = result.get('title', 'Без названия')[:50]
                    print(f"  {i}. {title}")
            else:
                print("ОШИБКА: Результатов не найдено")
                
    except Exception as e:
        print(f"ОШИБКА: {e}")

if __name__ == "__main__":
    print("=== SERP API TEST ===")
    asyncio.run(test_serp())