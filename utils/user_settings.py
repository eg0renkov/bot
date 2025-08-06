import os
import json
from typing import Optional, Dict


class UserSettings:
    """Управление настройками пользователей"""
    
    def __init__(self):
        self.settings_dir = "data/user_settings"
        os.makedirs(self.settings_dir, exist_ok=True)
    
    def _get_user_file(self, user_id: int) -> str:
        """Получить путь к файлу настроек пользователя"""
        return os.path.join(self.settings_dir, f"user_{user_id}.json")
    
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