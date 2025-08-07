import os
import json
from typing import Optional, Dict, Any
from datetime import datetime


class UserSettings:
    """Управление настройками пользователей"""
    
    def __init__(self):
        self.settings_dir = "data/user_settings"
        os.makedirs(self.settings_dir, exist_ok=True)
    
    def _get_user_file(self, user_id: int) -> str:
        """Получить путь к файлу настроек пользователя"""
        return os.path.join(self.settings_dir, f"user_{user_id}.json")
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """Настройки по умолчанию"""
        return {
            "display_name": None,
            "calendar": {
                "auto_sync_reminders": False,
                "sync_interval": 3600,  # секунды (1 час)
                "last_sync": None
            },
            "reminders": {
                "enabled": True,
                "sound_enabled": True,
                "timezone": "Europe/Moscow",  # Московский часовой пояс по умолчанию
                "advance_time": 15,  # За сколько минут предупреждать
                "notify_at_event": False,  # Уведомлять в момент события
                "daily_summary": False
            },
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    
    def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """Получить все настройки пользователя"""
        try:
            user_file = self._get_user_file(user_id)
            default_settings = self._get_default_settings()
            
            if os.path.exists(user_file):
                with open(user_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    # Объединяем с настройками по умолчанию
                    self._merge_settings(default_settings, settings)
                    return default_settings
            else:
                # Создаем файл с настройками по умолчанию
                self._save_user_settings(user_id, default_settings)
                return default_settings
                
        except Exception as e:
            print(f"Error loading settings for user {user_id}: {e}")
            return self._get_default_settings()
    
    def _save_user_settings(self, user_id: int, settings: Dict[str, Any]):
        """Сохранить настройки пользователя"""
        try:
            user_file = self._get_user_file(user_id)
            settings["updated_at"] = datetime.now().isoformat()
            
            with open(user_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Error saving settings for user {user_id}: {e}")
    
    def update_setting(self, user_id: int, key_path: str, value: Any):
        """Обновить конкретную настройку"""
        settings = self.get_user_settings(user_id)
        
        # Разбираем путь к настройке (например, "calendar.auto_sync_reminders")
        keys = key_path.split('.')
        current = settings
        
        # Идем по пути до предпоследнего ключа
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Устанавливаем значение
        current[keys[-1]] = value
        
        # Сохраняем
        self._save_user_settings(user_id, settings)
        return settings
    
    def get_setting(self, user_id: int, key_path: str, default=None):
        """Получить конкретную настройку"""
        settings = self.get_user_settings(user_id)
        
        keys = key_path.split('.')
        current = settings
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    def toggle_setting(self, user_id: int, key_path: str) -> bool:
        """Переключить булеву настройку"""
        current_value = self.get_setting(user_id, key_path, False)
        new_value = not current_value
        self.update_setting(user_id, key_path, new_value)
        return new_value
    
    def _merge_settings(self, default: Dict, user: Dict):
        """Рекурсивно объединяет настройки пользователя с дефолтными"""
        for key, value in user.items():
            if key in default:
                if isinstance(value, dict) and isinstance(default[key], dict):
                    self._merge_settings(default[key], value)
                else:
                    default[key] = value
    
    async def get_user_name(self, user_id: int) -> Optional[str]:
        """Получить сохраненное имя пользователя"""
        try:
            user_file = self._get_user_file(user_id)
            
            if not os.path.exists(user_file):
                return None
            
            with open(user_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return data.get('display_name')
            
        except Exception as e:
            print(f"Ошибка получения имени пользователя {user_id}: {e}")
            return None
    
    async def save_user_name(self, user_id: int, name: str) -> bool:
        """Сохранить имя пользователя"""
        try:
            user_file = self._get_user_file(user_id)
            
            # Загружаем существующие настройки
            data = {}
            if os.path.exists(user_file):
                try:
                    with open(user_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except:
                    pass
            
            # Обновляем имя
            data['display_name'] = name.strip()
            data['updated_at'] = __import__('datetime').datetime.now().isoformat()
            
            # Сохраняем
            with open(user_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Ошибка сохранения имени пользователя {user_id}: {e}")
            return False
    
    async def get_or_request_name(self, user_id: int, telegram_name: str = None) -> str:
        """Получить имя пользователя или создать из telegram данных"""
        # Сначала пытаемся получить сохраненное имя
        saved_name = await self.get_user_name(user_id)
        if saved_name:
            return saved_name
        
        # Если нет сохраненного имени, используем данные из Telegram
        if telegram_name:
            await self.save_user_name(user_id, telegram_name)
            return telegram_name
        
        # Если совсем ничего нет
        return "Пользователь"


# Глобальный экземпляр
user_settings = UserSettings()