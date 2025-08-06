"""
Тестирование исправлений календаря - 3 проверки подключения
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Добавляем корневую папку в sys.path для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from handlers.yandex_integration import YandexCalendar

async def test_calendar_connection_multiple_times():
    """Тестирование подключения к календарю 3 раза"""
    
    # Данные для тестирования (используем реальные данные из файла токенов)
    email = "alexlesley01@yandex.ru"
    app_password = "hcrfrbsxjrxdcagn"
    
    print("ТЕСТИРОВАНИЕ ПОДКЛЮЧЕНИЯ К ЯНДЕКС.КАЛЕНДАРЮ")
    print("=" * 60)
    print(f"Email: {email}")
    print(f"Пароль приложения: {app_password[:4]}{'*' * (len(app_password) - 4)}")
    print()
    
    # Проводим 3 теста
    for test_num in range(1, 4):
        print(f"ТЕСТ #{test_num}")
        print("-" * 30)
        
        try:
            # Создаем новый экземпляр календаря для каждого теста
            calendar = YandexCalendar(app_password, email)
            
            print(f"Календарь создан, проверяем подключение...")
            
            # Тестируем подключение
            start_time = datetime.now()
            connection_result = await calendar.ensure_connection_async()
            end_time = datetime.now()
            
            duration = (end_time - start_time).total_seconds()
            
            if connection_result:
                print(f"✅ УСПЕХ! Подключение за {duration:.2f} сек")
                print(f"   Найдено календарей: {len(calendar.calendars)}")
                print(f"   Основной календарь: {'Найден' if calendar.default_calendar else 'НЕ найден'}")
                
                # Тестируем получение событий
                print(f"   Тестируем получение событий...")
                today = datetime.now()
                start_date = today.strftime("%Y-%m-%dT00:00:00")
                end_date = (today + timedelta(days=7)).strftime("%Y-%m-%dT23:59:59")
                
                events = await calendar.get_events(start_date, end_date)
                print(f"   События на неделю: {len(events) if events else 0}")
                
                # Показываем первые 3 события
                if events:
                    for i, event in enumerate(events[:3]):
                        title = event.get('summary', 'Без названия')
                        start = event.get('start', {}).get('dateTime', '')
                        print(f"   - {title} ({start})")
                
            else:
                print(f"❌ ОШИБКА подключения за {duration:.2f} сек")
                print(f"   Статус клиента: {'Создан' if calendar.client else 'НЕ создан'}")
                print(f"   Календари: {len(calendar.calendars)}")
            
        except Exception as e:
            print(f"❌ ИСКЛЮЧЕНИЕ: {e}")
        
        print()
        
        # Пауза между тестами
        if test_num < 3:
            print("Пауза 3 секунды...")
            await asyncio.sleep(3)
            print()

async def test_calendar_create_event():
    """Тестирование создания события"""
    print("ТЕСТИРОВАНИЕ СОЗДАНИЯ СОБЫТИЯ")
    print("=" * 60)
    
    email = "alexlesley01@yandex.ru"
    app_password = "hcrfrbsxjrxdcagn"
    
    try:
        calendar = YandexCalendar(app_password, email)
        
        # Подключаемся
        if not await calendar.ensure_connection_async():
            print("❌ Не удалось подключиться для создания события")
            return
        
        # Создаем тестовое событие
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=15, minute=0, second=0).isoformat()
        end_time = tomorrow.replace(hour=16, minute=0, second=0).isoformat()
        
        print(f"Создаем событие на {start_time}...")
        
        success = await calendar.create_event(
            title="Тест подключения календаря",
            start_time=start_time,
            end_time=end_time,
            description="Автоматический тест от Telegram бота"
        )
        
        if success:
            print("✅ Событие создано успешно!")
        else:
            print("❌ Ошибка создания события")
            
    except Exception as e:
        print(f"❌ ИСКЛЮЧЕНИЕ при создании события: {e}")

async def main():
    """Главная функция тестирования"""
    print("ЗАПУСК ТЕСТОВ КАЛЕНДАРЯ")
    print("=" * 60)
    print(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Тест 1: Многократное подключение
    await test_calendar_connection_multiple_times()
    
    print()
    print("=" * 60)
    
    # Тест 2: Создание события
    await test_calendar_create_event()
    
    print()
    print("=" * 60)
    print("ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ")

if __name__ == "__main__":
    asyncio.run(main())