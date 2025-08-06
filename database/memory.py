import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from config.settings import settings

class SimpleMemory:
    """Простая файловая система памяти (без Supabase)"""
    
    def __init__(self):
        self.data_dir = "data"
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def _get_user_file(self, user_id: int) -> str:
        return os.path.join(self.data_dir, f"user_{user_id}.json")
    
    def save_message(self, user_id: int, user_message: str, ai_response: str):
        """Сохранить сообщение в память"""
        try:
            file_path = self._get_user_file(user_id)
            
            # Загружаем существующие данные
            history = []
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            
            # Добавляем новое сообщение
            message_data = {
                'user_message': user_message,
                'ai_response': ai_response,
                'timestamp': datetime.now().isoformat()
            }
            history.append(message_data)
            
            # Ограничиваем количество сообщений
            if len(history) > settings.MAX_HISTORY_MESSAGES:
                history = history[-settings.MAX_HISTORY_MESSAGES:]
            
            # Сохраняем
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Ошибка сохранения сообщения: {e}")
    
    def get_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Получить историю сообщений"""
        try:
            file_path = self._get_user_file(user_id)
            
            if not os.path.exists(file_path):
                return []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            # Возвращаем последние сообщения
            return history[-limit:] if len(history) > limit else history
            
        except Exception as e:
            print(f"Ошибка получения истории: {e}")
            return []
    
    def clear_history(self, user_id: int):
        """Очистить историю пользователя"""
        try:
            file_path = self._get_user_file(user_id)
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Ошибка очистки истории: {e}")
    
    def cleanup_old_data(self, days: int = 30):
        """Удалить старые данные"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for file_name in os.listdir(self.data_dir):
                if file_name.startswith('user_') and file_name.endswith('.json'):
                    file_path = os.path.join(self.data_dir, file_name)
                    
                    # Проверяем дату последнего изменения файла
                    if os.path.getmtime(file_path) < cutoff_date.timestamp():
                        os.remove(file_path)
                        print(f"Удален старый файл: {file_name}")
                        
        except Exception as e:
            print(f"Ошибка очистки старых данных: {e}")


class SupabaseMemory:
    """Память через Supabase (если настроен)"""
    
    def __init__(self):
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise ValueError("Supabase не настроен")
        
        try:
            from supabase import create_client
            self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        except ImportError:
            raise ImportError("Установите supabase: pip install supabase")
    
    def save_message(self, user_id: int, user_message: str, ai_response: str):
        """Сохранить сообщение в Supabase"""
        try:
            data = {
                'user_id': user_id,
                'user_message': user_message,
                'ai_response': ai_response,
                'created_at': datetime.now().isoformat()
            }
            
            result = self.client.table('conversations').insert(data).execute()
            return result
            
        except Exception as e:
            print(f"Ошибка сохранения в Supabase: {e}")
    
    def get_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Получить историю из Supabase"""
        try:
            result = self.client.table('conversations')\
                .select('user_message, ai_response, created_at')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data[::-1]  # Разворачиваем для хронологического порядка
            
        except Exception as e:
            print(f"Ошибка получения истории из Supabase: {e}")
            return []


# Фабрика для создания нужного типа памяти
def create_memory():
    """Создать объект памяти в зависимости от настроек"""
    if settings.SUPABASE_URL and settings.SUPABASE_KEY and settings.MEMORY_ENABLED:
        try:
            return SupabaseMemory()
        except (ValueError, ImportError):
            print("Используется простая файловая память")
            return SimpleMemory()
    else:
        return SimpleMemory()

memory = create_memory()