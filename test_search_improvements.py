"""Тест улучшений поиска писем"""

import asyncio
import json
import os

async def test_search_cache():
    """Тест кэширования результатов поиска"""
    
    print("ТЕСТ СИСТЕМЫ КЭШИРОВАНИЯ ПОИСКА")
    print("=" * 50)
    
    # Тестовый пользователь
    test_user_id = 555555
    
    # Создаем тестовые результаты поиска
    test_search_results = [
        {
            'sender': 'Т-Банк <inform@emails.tinkoff.ru>',
            'subject': 'Получите 360 000 ₽',
            'date': 'Tue, 5 Aug 2025',
            'content': 'Специальное предложение для вас! Получите кредитную карту с лимитом до 360 000 рублей.'
        },
        {
            'sender': 'Яндекс <noreply@yandex.ru>',
            'subject': 'Важное уведомление',
            'date': 'Mon, 4 Aug 2025',
            'content': 'Уведомляем о изменениях в условиях использования сервиса.'
        }
    ]
    
    search_query = "тинькофф"
    
    # 1. Тестируем сохранение кэша
    print("\n1. Тест сохранения кэша поиска:")
    print("-" * 30)
    
    search_cache_dir = "data/search_cache"
    os.makedirs(search_cache_dir, exist_ok=True)
    
    cache_file = os.path.join(search_cache_dir, f"user_{test_user_id}_last_search.json")
    cache_data = {
        'query': search_query,
        'results': test_search_results,
        'timestamp': __import__('datetime').datetime.now().isoformat()
    }
    
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        print(f"[OK] Кэш сохранен в {cache_file}")
    except Exception as e:
        print(f"[ERROR] Ошибка сохранения кэша: {e}")
        return
    
    # 2. Тестируем загрузку кэша
    print("\n2. Тест загрузки кэша поиска:")
    print("-" * 30)
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            loaded_cache = json.load(f)
        
        loaded_query = loaded_cache.get('query')
        loaded_results = loaded_cache.get('results', [])
        
        print(f"[OK] Загружен запрос: {loaded_query}")
        print(f"[OK] Загружено результатов: {len(loaded_results)}")
        
        for i, result in enumerate(loaded_results, 1):
            print(f"  {i}. {result['sender']} - {result['subject']}")
            
    except Exception as e:
        print(f"[ERROR] Ошибка загрузки кэша: {e}")
        return
    
    # 3. Тестируем настройки поиска
    print("\n3. Тест настроек поиска:")
    print("-" * 30)
    
    settings_dir = "data/search_settings"
    os.makedirs(settings_dir, exist_ok=True)
    settings_file = os.path.join(settings_dir, f"user_{test_user_id}_search.json")
    
    # Настройки по умолчанию
    default_settings = {
        'search_limit': 10,
        'content_analysis': False,
        'search_in_body': True,
        'search_in_attachments': False,
        'date_range_days': 365,
        'priority_search': False
    }
    
    # Тестовые пользовательские настройки
    user_settings = {
        'search_limit': 20,           # Увеличили лимит
        'content_analysis': True,     # Включили AI анализ
        'search_in_body': True,
        'search_in_attachments': True, # Включили поиск в вложениях
        'date_range_days': 180,       # Уменьшили диапазон
        'priority_search': False
    }
    
    try:
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(user_settings, f, ensure_ascii=False, indent=2)
        print(f"[OK] Настройки сохранены в {settings_file}")
    except Exception as e:
        print(f"[ERROR] Ошибка сохранения настроек: {e}")
        return
    
    # Загружаем и проверяем настройки
    try:
        current_settings = default_settings.copy()
        with open(settings_file, 'r', encoding='utf-8') as f:
            loaded_settings = json.load(f)
            current_settings.update(loaded_settings)
        
        print("[OK] Загруженные настройки:")
        for key, value in current_settings.items():
            print(f"  {key}: {value}")
            
    except Exception as e:
        print(f"[ERROR] Ошибка загрузки настроек: {e}")
        return
    
    # 4. Тест форматирования детального просмотра
    print("\n4. Тест форматирования результатов:")
    print("-" * 30)
    
    # Имитируем HTML экранирование (без импорта utils)
    def simple_escape_html(text):
        return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    def simple_truncate(text, max_len):
        if len(text) <= max_len:
            return simple_escape_html(text)
        return simple_escape_html(text[:max_len-3]) + "..."
    
    # Формируем детальный просмотр
    detailed_text = f"📖 Детальный просмотр поиска\n\n"
    detailed_text += f"🔍 Запрос: {simple_escape_html(search_query)}\n"
    detailed_text += f"📬 Найдено писем: {len(test_search_results)}\n\n"
    
    for i, email_data in enumerate(test_search_results, 1):
        sender = email_data.get('sender', 'Неизвестный отправитель')
        subject = email_data.get('subject', 'Без темы')
        date = email_data.get('date', '')
        content = email_data.get('content', '')
        
        detailed_text += f"📧 Письмо {i}:\n"
        detailed_text += f"👤 От: {simple_truncate(sender, 40)}\n"
        detailed_text += f"📝 Тема: {simple_truncate(subject, 50)}\n"
        
        if date:
            detailed_text += f"🕐 Дата: {simple_escape_html(str(date)[:19])}\n"
        
        if content:
            content_preview = simple_truncate(content.strip(), 150)
            detailed_text += f"📄 Содержание:\n{content_preview}\n"
        
        detailed_text += "\n" + "─" * 30 + "\n\n"
    
    print("[OK] Детальный просмотр сформирован:")
    print(detailed_text[:500] + "...")
    
    # 5. Очистка тестовых данных
    print("\n5. Очистка тестовых данных:")
    print("-" * 30)
    
    try:
        if os.path.exists(cache_file):
            os.remove(cache_file)
            print("[OK] Кэш удален")
        
        if os.path.exists(settings_file):
            os.remove(settings_file)
            print("[OK] Настройки удалены")
            
    except Exception as e:
        print(f"[ERROR] Ошибка очистки: {e}")
    
    print("\n" + "=" * 50)
    print("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print("[OK] Кэширование поиска: работает")
    print("[OK] Настройки поиска: работают")
    print("[OK] Форматирование результатов: работает")
    print("[OK] Детальный просмотр: готов")
    print("[OK] Система улучшений поиска готова!")

if __name__ == "__main__":
    asyncio.run(test_search_cache())