"""
Модуль синхронизации календаря с напоминаниями
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from database.reminders import ReminderDB

logger = logging.getLogger(__name__)

class CalendarReminderSync:
    """Класс для синхронизации событий календаря с напоминаниями"""
    
    def __init__(self):
        """Инициализация синхронизатора"""
        self.reminder_db = ReminderDB()
    
    async def sync_calendar_event(
        self,
        user_id: int,
        event_title: str,
        event_time: datetime,
        event_description: Optional[str] = None,
        advance_minutes: int = 15,
        create_reminder: bool = True
    ) -> Optional[int]:
        """
        Синхронизировать событие календаря с напоминанием
        
        Args:
            user_id: ID пользователя
            event_title: Название события
            event_time: Время события
            event_description: Описание события
            advance_minutes: За сколько минут напомнить
            create_reminder: Создавать ли напоминание
            
        Returns:
            ID созданного напоминания или None
        """
        if not create_reminder:
            return None
        
        try:
            # Проверяем нет ли уже напоминания для этого события
            existing_reminders = await self.reminder_db.get_user_reminders(user_id)
            event_title_lower = event_title.lower()
            
            for reminder in existing_reminders:
                if (event_title_lower in reminder.get('title', '').lower() or 
                    reminder.get('title', '').lower() in event_title_lower):
                    # Проверяем время - если разница меньше 5 минут, считаем дубликатом
                    from datetime import timedelta
                    reminder_time = reminder.get('remind_at')
                    if isinstance(reminder_time, str):
                        from datetime import datetime
                        reminder_time = datetime.fromisoformat(reminder_time.replace('Z', '+00:00'))
                    
                    if reminder_time and abs((event_time - reminder_time).total_seconds()) < 300:  # 5 минут
                        logger.info(f"Пропуск создания дублированного напоминания для события: {event_title}")
                        return None
            
            # Получаем настройки пользователя
            from utils.user_settings import user_settings as usr_settings
            settings = usr_settings.get_user_settings(user_id)
            reminder_settings = settings.get('reminders', {})
            
            # Используем время предупреждения из настроек или переданное
            advance_time = reminder_settings.get('advance_time', advance_minutes)
            notify_at_event = reminder_settings.get('notify_at_event', False)
            
            # Создаем предварительное напоминание
            remind_at = event_time - timedelta(minutes=advance_time)
            
            # Вычисляем реальное время до события в момент напоминания
            time_to_event_minutes = int((event_time - remind_at).total_seconds() / 60)
            
            reminder_id = await self.reminder_db.create_reminder(
                user_id=user_id,
                title=f"📅 Скоро: {event_title}",
                description=f"Событие начнется через {time_to_event_minutes} минут\n{event_description or ''}",
                remind_at=remind_at,
                repeat_type='none',
                repeat_interval=0
            )
            
            if reminder_id:
                logger.info(f"Создано предварительное напоминание {reminder_id} для события календаря")
            
            # Создаем напоминание в момент события, если включено
            if notify_at_event:
                at_event_id = await self.reminder_db.create_reminder(
                    user_id=user_id,
                    title=f"🎯 Началось: {event_title}",
                    description=f"Событие началось!\n{event_description or ''}",
                    remind_at=event_time,
                    repeat_type='none',
                    repeat_interval=0
                )
                
                if at_event_id:
                    logger.info(f"Создано напоминание в момент события {at_event_id}")
            
            return reminder_id
            
        except Exception as e:
            logger.error(f"Ошибка синхронизации события календаря: {e}")
            return None
    
    async def create_recurring_event_reminder(
        self,
        user_id: int,
        event_title: str,
        event_time: datetime,
        repeat_type: str = 'weekly',
        repeat_days: Optional[List[str]] = None,
        event_description: Optional[str] = None
    ) -> Optional[int]:
        """
        Создать повторяющееся напоминание для события календаря
        
        Args:
            user_id: ID пользователя
            event_title: Название события
            event_time: Время первого события
            repeat_type: Тип повторения (daily, weekly, monthly)
            repeat_days: Дни недели для еженедельных событий
            event_description: Описание события
            
        Returns:
            ID созданного напоминания
        """
        try:
            # Получаем настройки пользователя
            settings = await self.reminder_db.get_user_settings(user_id)
            advance_time = settings.get('advance_notification', 15)
            
            # Вычисляем время напоминания
            remind_at = event_time - timedelta(minutes=advance_time)
            
            # Создаем повторяющееся напоминание
            reminder_id = await self.reminder_db.create_reminder(
                user_id=user_id,
                title=f"📅 {event_title}",
                description=f"Повторяющееся событие\n{event_description or ''}",
                remind_at=remind_at,
                repeat_type=repeat_type,
                repeat_interval=1,
                repeat_days=repeat_days
            )
            
            if reminder_id:
                logger.info(f"Создано повторяющееся напоминание {reminder_id}")
            
            return reminder_id
            
        except Exception as e:
            logger.error(f"Ошибка создания повторяющегося напоминания: {e}")
            return None
    
    async def sync_all_calendar_events(
        self,
        user_id: int,
        events: List[Dict[str, Any]]
    ) -> int:
        """
        Синхронизировать все события календаря
        
        Args:
            user_id: ID пользователя
            events: Список событий календаря
            
        Returns:
            Количество созданных напоминаний
        """
        created_count = 0
        
        for event in events:
            try:
                # Извлекаем данные события
                title = event.get('summary', 'Событие календаря')
                description = event.get('description', '')
                
                # Парсим время события
                start_time = event.get('start')
                if not start_time:
                    continue
                
                # Преобразуем время в datetime
                if isinstance(start_time, str):
                    event_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                elif isinstance(start_time, dict):
                    # Для событий из Google Calendar
                    date_time = start_time.get('dateTime') or start_time.get('date')
                    if date_time:
                        event_time = datetime.fromisoformat(date_time.replace('Z', '+00:00'))
                    else:
                        continue
                else:
                    event_time = start_time
                
                # Делаем текущее время timezone-aware для корректного сравнения
                from datetime import timezone
                now_aware = datetime.now(timezone.utc)
                
                # Если event_time не имеет timezone, считаем его локальным
                if event_time.tzinfo is None:
                    # Считаем что это московское время (UTC+3)
                    moscow_tz = timezone(timedelta(hours=3))
                    event_time = event_time.replace(tzinfo=moscow_tz)
                
                # Пропускаем прошедшие события
                if event_time < now_aware:
                    logger.info(f"Skipping past event: {title} at {event_time}")
                    continue
                
                # Проверяем повторяющееся ли событие
                recurrence = event.get('recurrence')
                if recurrence:
                    # Обрабатываем повторяющееся событие
                    repeat_type = self._parse_recurrence(recurrence)
                    reminder_id = await self.create_recurring_event_reminder(
                        user_id=user_id,
                        event_title=title,
                        event_time=event_time,
                        repeat_type=repeat_type,
                        event_description=description
                    )
                else:
                    # Обычное событие
                    reminder_id = await self.sync_calendar_event(
                        user_id=user_id,
                        event_title=title,
                        event_time=event_time,
                        event_description=description
                    )
                
                if reminder_id:
                    created_count += 1
                    
            except Exception as e:
                logger.error(f"Ошибка синхронизации события: {e}")
                continue
        
        logger.info(f"Синхронизировано {created_count} событий календаря")
        return created_count
    
    def _parse_recurrence(self, recurrence: Any) -> str:
        """
        Парсить правило повторения события
        
        Args:
            recurrence: Правило повторения из календаря
            
        Returns:
            Тип повторения для напоминаний
        """
        if isinstance(recurrence, list):
            rule = recurrence[0] if recurrence else ''
        else:
            rule = str(recurrence)
        
        rule_lower = rule.lower()
        
        if 'daily' in rule_lower:
            return 'daily'
        elif 'weekly' in rule_lower:
            return 'weekly'
        elif 'monthly' in rule_lower:
            return 'monthly'
        elif 'yearly' in rule_lower:
            return 'yearly'
        else:
            return 'none'
    
    async def sync_calendar_to_reminders(self, user_id: int, token_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Синхронизировать календарь с напоминаниями
        
        Args:
            user_id: ID пользователя
            token_data: Данные токена календаря (содержит app_password и username)
            
        Returns:
            Результат синхронизации
        """
        try:
            # Импортируем необходимые модули
            from handlers.yandex_integration import YandexCalendar
            from datetime import datetime, timedelta
            
            # DEBUG: Логируем содержимое token_data
            logger.info(f"Token data keys: {list(token_data.keys())}")
            logger.info(f"Token data content: {token_data}")
            
            # Получаем данные для подключения
            app_password = token_data.get("app_password")
            username = token_data.get("username") or token_data.get("email")
            
            logger.info(f"App password found: {bool(app_password)}")
            logger.info(f"Username found: {bool(username)}")
            
            if not app_password:
                return {
                    "success": False,
                    "error": "Не найден пароль приложения",
                    "events_processed": 0,
                    "reminders_created": 0
                }
            
            if not username:
                return {
                    "success": False,
                    "error": "Не найдено имя пользователя или email",
                    "events_processed": 0,
                    "reminders_created": 0
                }
            
            # Создаем экземпляр календаря
            calendar = YandexCalendar(app_password, username)
            
            # Получаем события на следующие 30 дней
            start_date = datetime.now()
            end_date = start_date + timedelta(days=30)
            
            events = await calendar.get_events(
                start_date.strftime('%Y-%m-%dT%H:%M:%S'),
                end_date.strftime('%Y-%m-%dT%H:%M:%S')
            )
            
            if not events:
                return {
                    "success": True,
                    "events_processed": 0,
                    "reminders_created": 0,
                    "message": "Нет событий для синхронизации"
                }
            
            # Синхронизируем события
            reminders_created = await self.sync_all_calendar_events(user_id, events)
            
            return {
                "success": True,
                "events_processed": len(events),
                "reminders_created": reminders_created,
                "message": f"Синхронизировано {reminders_created} напоминаний из {len(events)} событий"
            }
            
        except Exception as e:
            logger.error(f"Ошибка синхронизации календаря: {e}")
            return {
                "success": False,
                "error": str(e),
                "events_processed": 0,
                "reminders_created": 0
            }

    async def remove_event_reminders(self, user_id: int, event_id: str) -> int:
        """
        Удалить напоминания, связанные с конкретным событием
        
        Args:
            user_id: ID пользователя
            event_id: ID события календаря
            
        Returns:
            Количество удаленных напоминаний
        """
        try:
            # Получаем все напоминания пользователя
            reminders = await self.reminder_db.get_user_reminders(user_id)
            
            deleted_count = 0
            for reminder in reminders:
                # Проверяем, что напоминание связано с событием
                # (содержит ID события в описании или создано из календаря)
                reminder_title = reminder.get('title', '').lower()
                reminder_desc = reminder.get('description', '').lower()
                
                if (reminder_title.startswith('📅') or 
                    event_id.lower() in reminder_desc or
                    any(word in reminder_title for word in event_id.lower().split('_'))):
                    success = await self.reminder_db.delete_reminder(reminder['id'])
                    if success:
                        deleted_count += 1
                        logger.info(f"Удалено напоминание {reminder['id']} для события {event_id}")
            
            logger.info(f"Удалено {deleted_count} напоминаний для события {event_id}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Ошибка удаления напоминаний события {event_id}: {e}")
            return 0

    async def remove_calendar_reminders(self, user_id: int) -> int:
        """
        Удалить все напоминания, созданные из календаря
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Количество удаленных напоминаний
        """
        try:
            # Получаем все напоминания пользователя
            reminders = await self.reminder_db.get_user_reminders(user_id)
            
            deleted_count = 0
            for reminder in reminders:
                # Проверяем, что напоминание создано из календаря
                if reminder.get('title', '').startswith('📅'):
                    success = await self.reminder_db.delete_reminder(reminder['id'])
                    if success:
                        deleted_count += 1
            
            logger.info(f"Удалено {deleted_count} напоминаний календаря")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Ошибка удаления напоминаний календаря: {e}")
            return 0