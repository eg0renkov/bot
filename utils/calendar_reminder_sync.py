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
            # Получаем настройки пользователя
            settings = await self.reminder_db.get_user_settings(user_id)
            
            # Используем время предупреждения из настроек или переданное
            advance_time = settings.get('advance_notification', advance_minutes)
            
            # Вычисляем время напоминания
            remind_at = event_time - timedelta(minutes=advance_time)
            
            # Создаем напоминание
            reminder_id = await self.reminder_db.create_reminder(
                user_id=user_id,
                title=f"📅 {event_title}",
                description=f"Событие начнется через {advance_time} минут\n{event_description or ''}",
                remind_at=remind_at,
                repeat_type='none',
                repeat_interval=0
            )
            
            if reminder_id:
                logger.info(f"Создано напоминание {reminder_id} для события календаря")
            
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
                
                # Пропускаем прошедшие события
                if event_time < datetime.now():
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