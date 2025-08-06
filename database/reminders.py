"""
Модуль для работы с напоминаниями в базе данных Supabase
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
from supabase import create_client, Client
from config.settings import settings

logger = logging.getLogger(__name__)

class ReminderDB:
    """Класс для работы с напоминаниями в базе данных"""
    
    def __init__(self):
        """Инициализация подключения к Supabase"""
        try:
            self.supabase: Client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY
            )
            logger.info("Подключение к Supabase для напоминаний установлено")
        except Exception as e:
            logger.error(f"Ошибка подключения к Supabase: {e}")
            self.supabase = None
    
    async def create_reminder(
        self,
        user_id: int,
        title: str,
        remind_at: datetime,
        description: Optional[str] = None,
        repeat_type: str = 'none',
        repeat_interval: int = 0,
        repeat_days: Optional[List[str]] = None
    ) -> Optional[int]:
        """Создание нового напоминания"""
        if not self.supabase:
            logger.error("Нет подключения к Supabase")
            return None
        
        try:
            data = {
                'user_id': user_id,
                'title': title,
                'description': description,
                'remind_at': remind_at.isoformat(),
                'repeat_type': repeat_type,
                'repeat_interval': repeat_interval,
                'repeat_days': repeat_days,
                'is_active': True,
                'is_completed': False,
                'notification_sent': False
            }
            
            result = self.supabase.table('reminders').insert(data).execute()
            
            if result.data:
                reminder_id = result.data[0]['id']
                logger.info(f"Создано напоминание {reminder_id} для пользователя {user_id}")
                
                # Создаем настройки пользователя если их нет
                await self.ensure_user_settings(user_id)
                
                return reminder_id
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка создания напоминания: {e}")
            return None
    
    async def get_user_reminders(
        self,
        user_id: int,
        active_only: bool = False,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Получение напоминаний пользователя"""
        if not self.supabase:
            return []
        
        try:
            query = self.supabase.table('reminders').select('*').eq('user_id', user_id)
            
            if active_only:
                query = query.eq('is_active', True).eq('is_completed', False)
            
            query = query.order('remind_at', desc=False).limit(limit)
            
            result = query.execute()
            
            if result.data:
                # Преобразуем строки в datetime объекты
                for reminder in result.data:
                    reminder['remind_at'] = datetime.fromisoformat(reminder['remind_at'].replace('Z', '+00:00'))
                    if reminder.get('created_at'):
                        reminder['created_at'] = datetime.fromisoformat(reminder['created_at'].replace('Z', '+00:00'))
                
                return result.data
            
            return []
            
        except Exception as e:
            logger.error(f"Ошибка получения напоминаний: {e}")
            return []
    
    async def get_reminder(self, reminder_id: int) -> Optional[Dict[str, Any]]:
        """Получение конкретного напоминания"""
        if not self.supabase:
            return None
        
        try:
            result = self.supabase.table('reminders').select('*').eq('id', reminder_id).execute()
            
            if result.data:
                reminder = result.data[0]
                reminder['remind_at'] = datetime.fromisoformat(reminder['remind_at'].replace('Z', '+00:00'))
                if reminder.get('created_at'):
                    reminder['created_at'] = datetime.fromisoformat(reminder['created_at'].replace('Z', '+00:00'))
                return reminder
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения напоминания {reminder_id}: {e}")
            return None
    
    async def update_reminder(
        self,
        reminder_id: int,
        **kwargs
    ) -> bool:
        """Обновление напоминания"""
        if not self.supabase:
            return False
        
        try:
            # Преобразуем datetime в строку если есть
            if 'remind_at' in kwargs and isinstance(kwargs['remind_at'], datetime):
                kwargs['remind_at'] = kwargs['remind_at'].isoformat()
            
            result = self.supabase.table('reminders').update(kwargs).eq('id', reminder_id).execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Ошибка обновления напоминания {reminder_id}: {e}")
            return False
    
    async def delete_reminder(self, reminder_id: int) -> bool:
        """Удаление напоминания"""
        if not self.supabase:
            return False
        
        try:
            result = self.supabase.table('reminders').delete().eq('id', reminder_id).execute()
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Ошибка удаления напоминания {reminder_id}: {e}")
            return False
    
    async def complete_reminder(self, reminder_id: int) -> bool:
        """Отметить напоминание как выполненное"""
        return await self.update_reminder(
            reminder_id,
            is_completed=True,
            completed_at=datetime.now().isoformat()
        )
    
    async def get_active_reminders(
        self,
        time_window_minutes: int = 5
    ) -> List[Dict[str, Any]]:
        """Получение активных напоминаний для отправки"""
        if not self.supabase:
            return []
        
        try:
            # Вызываем функцию базы данных
            result = self.supabase.rpc(
                'get_active_reminders',
                {'time_window_minutes': time_window_minutes}
            ).execute()
            
            if result.data:
                for reminder in result.data:
                    reminder['remind_at'] = datetime.fromisoformat(reminder['remind_at'].replace('Z', '+00:00'))
                return result.data
            
            return []
            
        except Exception as e:
            logger.error(f"Ошибка получения активных напоминаний: {e}")
            return []
    
    async def mark_reminder_sent(self, reminder_id: int) -> bool:
        """Отметить напоминание как отправленное"""
        if not self.supabase:
            return False
        
        try:
            # Вызываем функцию базы данных
            result = self.supabase.rpc(
                'mark_reminder_sent',
                {'reminder_id': reminder_id}
            ).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отметки напоминания {reminder_id} как отправленного: {e}")
            return False
    
    async def get_user_stats(self, user_id: int) -> Dict[str, int]:
        """Получение статистики напоминаний пользователя"""
        if not self.supabase:
            return {
                'total_reminders': 0,
                'active_reminders': 0,
                'completed_reminders': 0,
                'upcoming_today': 0,
                'upcoming_week': 0
            }
        
        try:
            result = self.supabase.rpc(
                'get_user_reminder_stats',
                {'user_id_param': user_id}
            ).execute()
            
            if result.data:
                return result.data[0]
            
            return {
                'total_reminders': 0,
                'active_reminders': 0,
                'completed_reminders': 0,
                'upcoming_today': 0,
                'upcoming_week': 0
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики для пользователя {user_id}: {e}")
            return {
                'total_reminders': 0,
                'active_reminders': 0,
                'completed_reminders': 0,
                'upcoming_today': 0,
                'upcoming_week': 0
            }
    
    async def ensure_user_settings(self, user_id: int) -> bool:
        """Создание настроек пользователя если их нет"""
        if not self.supabase:
            return False
        
        try:
            # Проверяем существование настроек
            result = self.supabase.table('reminder_settings').select('user_id').eq('user_id', user_id).execute()
            
            if not result.data:
                # Создаем настройки по умолчанию
                self.supabase.table('reminder_settings').insert({
                    'user_id': user_id,
                    'enabled': True,
                    'sound_enabled': True,
                    'timezone': 'Europe/Moscow',
                    'advance_notification': 10,
                    'daily_summary': False
                }).execute()
                
                logger.info(f"Созданы настройки напоминаний для пользователя {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка создания настроек для пользователя {user_id}: {e}")
            return False
    
    async def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """Получение настроек пользователя"""
        if not self.supabase:
            return {}
        
        try:
            # Сначала убеждаемся что настройки существуют
            await self.ensure_user_settings(user_id)
            
            result = self.supabase.table('reminder_settings').select('*').eq('user_id', user_id).execute()
            
            if result.data:
                return result.data[0]
            
            return {}
            
        except Exception as e:
            logger.error(f"Ошибка получения настроек пользователя {user_id}: {e}")
            return {}
    
    async def update_user_settings(self, user_id: int, **kwargs) -> bool:
        """Обновление настроек пользователя"""
        if not self.supabase:
            return False
        
        try:
            # Убеждаемся что настройки существуют
            await self.ensure_user_settings(user_id)
            
            result = self.supabase.table('reminder_settings').update(kwargs).eq('user_id', user_id).execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Ошибка обновления настроек пользователя {user_id}: {e}")
            return False
    
    async def toggle_setting(self, user_id: int, setting_name: str) -> bool:
        """Переключение булевой настройки"""
        settings = await self.get_user_settings(user_id)
        
        if setting_name in settings:
            new_value = not settings.get(setting_name, False)
            return await self.update_user_settings(user_id, **{setting_name: new_value})
        
        return False