"""
Простое тестирование календаря без зависимостей от aiogram
"""
import caldav
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List
from icalendar import Calendar, Event
import uuid

class YandexCalendarTest:
    """Тестовая реализация календаря"""
    
    def __init__(self, app_password: str, username: str):
        self.app_password = app_password
        self.username = username
        self.caldav_url = "https://caldav.yandex.ru"
        
        # НЕ создаем соединение в __init__
        self.client = None
        self.principal = None
        self.calendars = []
        self.default_calendar = None
        self._connection_tested = False
        self._connection_successful = False
        
        print(f"YandexCalendarTest создан для {username}")
    
    def _ensure_connection(self) -> bool:
        """Проверяет и создает подключение если нужно"""
        if self._connection_tested:
            return self._connection_successful
        
        try:
            print(f"Подключение к CalDAV для {self.username}...")
            
            # Создаем клиент с максимальной надежностью
            self.client = caldav.DAVClient(
                url=self.caldav_url,
                username=self.username,
                password=self.app_password,
                ssl_verify_cert=True,
                timeout=30
            )
            
            # Тестируем подключение с повторными попытками
            for attempt in range(3):
                try:
                    self.principal = self.client.principal()
                    self.calendars = self.principal.calendars()
                    break
                except Exception as e:
                    print(f"Попытка {attempt + 1} подключения неудачна: {e}")
                    if attempt == 2:
                        raise e
                    import time
                    time.sleep(2)
            
            if self.calendars and len(self.calendars) > 0:
                self.default_calendar = self.calendars[0]
                self._connection_successful = True
                print(f"CalDAV подключен успешно! Найдено календарей: {len(self.calendars)}")
            else:
                print("CalDAV подключен, но календари не найдены")
                self._connection_successful = False
            
        except Exception as e:
            print(f"Критическая ошибка подключения CalDAV: {e}")
            self.client = None
            self.principal = None
            self.calendars = []
            self.default_calendar = None
            self._connection_successful = False
        
        self._connection_tested = True
        return self._connection_successful
    
    async def ensure_connection_async(self) -> bool:
        """Асинхронная обертка для проверки подключения"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._ensure_connection)
    
    def get_events_sync(self, start_date: str, end_date: str) -> List[Dict]:
        """Получить события"""
        try:
            if not self._ensure_connection():
                print("Не удалось подключиться к календарю")
                return []
            
            if not self.default_calendar:
                print("Календарь не найден")
                return []
            
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            
            print(f"Поиск событий с {start_dt} по {end_dt}")
            
            events = None
            for attempt in range(3):
                try:
                    events = self.default_calendar.date_search(start=start_dt, end=end_dt)
                    break
                except Exception as e:
                    print(f"Попытка {attempt + 1} получения событий неудачна: {e}")
                    if attempt == 2:
                        raise e
                    import time
                    time.sleep(1)
            
            if not events:
                return []
            
            result = []
            for event in events:
                try:
                    cal = Calendar.from_ical(event.data)
                    for component in cal.walk():
                        if component.name == "VEVENT":
                            title = str(component.get('summary', 'Без названия'))
                            start = component.get('dtstart')
                            end = component.get('dtend')
                            
                            event_data = {
                                "summary": title,
                                "start": {
                                    "dateTime": start.dt.isoformat() if start else ""
                                },
                                "end": {
                                    "dateTime": end.dt.isoformat() if end else ""
                                }
                            }
                            result.append(event_data)
                
                except Exception as e:
                    print(f"Ошибка парсинга события: {e}")
                    continue
            
            print(f"Всего найдено событий: {len(result)}")
            return result
            
        except Exception as e:
            print(f"Критическая ошибка получения событий: {e}")
            self._connection_tested = False
            return []
    
    async def get_events(self, start_date: str, end_date: str) -> List[Dict]:
        """Асинхронная обертка"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_events_sync, start_date, end_date)
    
    def create_event_sync(self, title: str, start_time: str, end_time: str, description: str = "") -> bool:
        """Создать событие"""
        try:
            if not self._ensure_connection():
                return False
            
            if not self.default_calendar:
                return False
            
            cal = Calendar()
            cal.add('prodid', '-//Test//CalDAV Event//EN')
            cal.add('version', '2.0')
            
            event = Event()
            event.add('summary', title)
            event.add('description', description)
            
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            event.add('dtstart', start_dt)
            event.add('dtend', end_dt)
            event.add('dtstamp', datetime.now())
            event.add('uid', str(uuid.uuid4()))
            
            cal.add_component(event)
            
            for attempt in range(3):
                try:
                    self.default_calendar.add_event(cal.to_ical().decode('utf-8'))
                    print(f"Событие '{title}' успешно создано")
                    return True
                except Exception as e:
                    print(f"Попытка {attempt + 1} создания события неудачна: {e}")
                    if attempt == 2:
                        raise e
                    import time
                    time.sleep(1)
            
            return False
            
        except Exception as e:
            print(f"Критическая ошибка создания события: {e}")
            self._connection_tested = False
            return False
    
    async def create_event(self, title: str, start_time: str, end_time: str, description: str = "") -> bool:
        """Асинхронная обертка"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.create_event_sync, title, start_time, end_time, description)

async def test_calendar_connection_multiple_times():
    """Тестирование подключения к календарю 3 раза"""
    
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
            calendar = YandexCalendarTest(app_password, email)
            
            print(f"Календарь создан, проверяем подключение...")
            
            start_time = datetime.now()
            connection_result = await calendar.ensure_connection_async()
            end_time = datetime.now()
            
            duration = (end_time - start_time).total_seconds()
            
            if connection_result:
                print(f"УСПЕХ! Подключение за {duration:.2f} сек")
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
                print(f"ОШИБКА подключения за {duration:.2f} сек")
                print(f"   Статус клиента: {'Создан' if calendar.client else 'НЕ создан'}")
                print(f"   Календари: {len(calendar.calendars)}")
            
        except Exception as e:
            print(f"ИСКЛЮЧЕНИЕ: {e}")
        
        print()
        
        # Пауза между тестами
        if test_num < 3:
            print("Пауза 3 секунды...")
            await asyncio.sleep(3)
            print()

async def main():
    """Главная функция тестирования"""
    print("ЗАПУСК ТЕСТОВ КАЛЕНДАРЯ")
    print("=" * 60)
    print(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    await test_calendar_connection_multiple_times()
    
    print()
    print("=" * 60)
    print("ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ")

if __name__ == "__main__":
    asyncio.run(main())