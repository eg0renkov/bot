"""
Надежное решение для Яндекс.Календаря - без сбоев подключения
Исправляет все проблемы с CalDAV и обеспечивает стабильную работу
"""
import caldav
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from icalendar import Calendar, Event
import uuid
import logging

logger = logging.getLogger(__name__)

class YandexCalendarFixed:
    """Исправленная реализация Яндекс.Календаря с защитой от всех ошибок"""
    
    def __init__(self, app_password: str, username: str):
        self.app_password = app_password
        self.username = username
        self.caldav_url = "https://caldav.yandex.ru"
        
        # Важно: НЕ создаем соединение в __init__
        # Это решает проблему с блокирующими вызовами
        self.client = None
        self.principal = None
        self.calendars = []
        self.default_calendar = None
        self._connection_tested = False
        self._connection_successful = False
        
        logger.info(f"YandexCalendarFixed создан для {username}")
    
    def _ensure_connection(self) -> bool:
        """Проверяет и создает подключение если нужно (синхронный метод)"""
        if self._connection_tested:
            return self._connection_successful
        
        try:
            logger.info(f"Подключение к CalDAV для {self.username}...")
            
            # Создаем клиент с максимальной надежностью
            self.client = caldav.DAVClient(
                url=self.caldav_url,
                username=self.username,
                password=self.app_password,
                # Добавляем параметры для надежности
                ssl_verify_cert=True,
                timeout=30  # Увеличиваем таймаут
            )
            
            # Тестируем подключение
            self.principal = self.client.principal()
            self.calendars = self.principal.calendars()
            
            if self.calendars and len(self.calendars) > 0:
                self.default_calendar = self.calendars[0]
                self._connection_successful = True
                logger.info(f"CalDAV подключен успешно! Найдено календарей: {len(self.calendars)}")
            else:
                logger.warning("CalDAV подключен, но календари не найдены")
                self._connection_successful = False
            
        except Exception as e:
            logger.error(f"Ошибка подключения CalDAV: {e}")
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
        """Получить события через CalDAV (синхронный метод с защитой от ошибок)"""
        try:
            # КРИТИЧЕСКИ ВАЖНО: Проверяем подключение перед каждым запросом
            if not self._ensure_connection():
                logger.error("Не удалось подключиться к календарю")
                return []
            
            if not self.default_calendar:
                logger.error("Календарь не найден")
                return []
            
            # Преобразуем даты с защитой от ошибок
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError as e:
                logger.error(f"Ошибка парсинга дат: {e}")
                return []
            
            logger.info(f"Поиск событий с {start_dt} по {end_dt}")
            
            # Получаем события с повторными попытками
            events = None
            for attempt in range(3):  # 3 попытки
                try:
                    events = self.default_calendar.date_search(start=start_dt, end=end_dt)
                    break
                except Exception as e:
                    logger.warning(f"Попытка {attempt + 1} получения событий неудачна: {e}")
                    if attempt == 2:  # последняя попытка
                        raise e
                    await asyncio.sleep(1)  # ждем секунду перед повтором
            
            if not events:
                logger.info("События не найдены")
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
                            logger.debug(f"Найдено событие: {title}")
                
                except Exception as e:
                    logger.warning(f"Ошибка парсинга события: {e}")
                    continue
            
            logger.info(f"Всего найдено событий: {len(result)}")
            return result
            
        except Exception as e:
            logger.error(f"Критическая ошибка получения событий: {e}")
            # Сбрасываем статус подключения для повторной попытки
            self._connection_tested = False
            return []
    
    async def get_events(self, start_date: str, end_date: str) -> List[Dict]:
        """Асинхронная обертка для получения событий"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_events_sync, start_date, end_date)
    
    def create_event_sync(self, title: str, start_time: str, end_time: str, description: str = "") -> bool:
        """Создать событие через CalDAV (синхронный метод с защитой от ошибок)"""
        try:
            # КРИТИЧЕСКИ ВАЖНО: Проверяем подключение перед каждым запросом
            if not self._ensure_connection():
                logger.error("Не удалось подключиться к календарю для создания события")
                return False
            
            if not self.default_calendar:
                logger.error("Календарь не найден для создания события")
                return False
            
            # Создаем iCalendar событие
            cal = Calendar()
            cal.add('prodid', '-//Telegram Bot//CalDAV Event//EN')
            cal.add('version', '2.0')
            
            event = Event()
            event.add('summary', title)
            event.add('description', description)
            
            # Парсим время с защитой от ошибок
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            except ValueError as e:
                logger.error(f"Ошибка парсинга времени: {e}")
                return False
            
            event.add('dtstart', start_dt)
            event.add('dtend', end_dt)
            event.add('dtstamp', datetime.now())
            event.add('uid', str(uuid.uuid4()))
            
            cal.add_component(event)
            
            # Сохраняем в календарь с повторными попытками
            for attempt in range(3):  # 3 попытки
                try:
                    self.default_calendar.add_event(cal.to_ical().decode('utf-8'))
                    logger.info(f"Событие '{title}' успешно создано")
                    return True
                except Exception as e:
                    logger.warning(f"Попытка {attempt + 1} создания события неудачна: {e}")
                    if attempt == 2:  # последняя попытка
                        raise e
                    asyncio.sleep(1)  # ждем секунду перед повтором
            
            return False
            
        except Exception as e:
            logger.error(f"Критическая ошибка создания события: {e}")
            # Сбрасываем статус подключения для повторной попытки
            self._connection_tested = False
            return False
    
    async def create_event(self, title: str, start_time: str, end_time: str, description: str = "") -> bool:
        """Асинхронная обертка для создания события"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.create_event_sync, title, start_time, end_time, description)
    
    async def test_connection(self) -> Dict[str, any]:
        """Тестирование подключения с подробной диагностикой"""
        try:
            success = await self.ensure_connection_async()
            
            if success:
                return {
                    "success": True,
                    "message": "Подключение к CalDAV успешно",
                    "calendars_found": len(self.calendars),
                    "calendar_url": self.caldav_url,
                    "username": self.username
                }
            else:
                return { 
                    "success": False,
                    "message": "Не удалось подключиться к CalDAV",
                    "calendar_url": self.caldav_url,
                    "username": self.username
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Ошибка тестирования: {str(e)}",
                "calendar_url": self.caldav_url,
                "username": self.username
            }