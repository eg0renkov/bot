import json
import os
from typing import Dict, Optional
from datetime import datetime

class UserTokenStorage:
    """Простое хранение токенов пользователей в файлах"""
    
    def __init__(self):
        self.storage_dir = "data/user_tokens"
        os.makedirs(self.storage_dir, exist_ok=True)
    
    def _get_user_file(self, user_id: int) -> str:
        """Получить путь к файлу пользователя"""
        return os.path.join(self.storage_dir, f"user_{user_id}.json")
    
    async def save_token(self, user_id: int, service: str, token_data: Dict):
        """Сохранить токен пользователя"""
        user_file = self._get_user_file(user_id)
        
        # Загружаем существующие данные
        user_data = {}
        if os.path.exists(user_file):
            try:
                with open(user_file, 'r', encoding='utf-8') as f:
                    user_data = json.load(f)
            except:
                pass
        
        # Добавляем новый токен
        user_data[service] = {
            **token_data,
            'saved_at': datetime.now().isoformat()
        }
        
        # Сохраняем обратно
        with open(user_file, 'w', encoding='utf-8') as f:
            json.dump(user_data, f, ensure_ascii=False, indent=2)
    
    async def get_token(self, user_id: int, service: str) -> Optional[str]:
        """Получить токен пользователя"""
        user_file = self._get_user_file(user_id)
        
        if not os.path.exists(user_file):
            return None
        
        try:
            with open(user_file, 'r', encoding='utf-8') as f:
                user_data = json.load(f)
            
            service_data = user_data.get(service, {})
            return service_data.get('access_token')
        except:
            return None
    
    async def get_user_info(self, user_id: int, service: str) -> Optional[Dict]:
        """Получить информацию о пользователе для сервиса"""
        user_file = self._get_user_file(user_id)
        
        if not os.path.exists(user_file):
            return None
        
        try:
            with open(user_file, 'r', encoding='utf-8') as f:
                user_data = json.load(f)
            
            return user_data.get(service, {}).get('user_info')
        except:
            return None
    
    async def get_token_data(self, user_id: int, service: str) -> Optional[Dict]:
        """Получить полные данные токена для сервиса"""
        user_file = self._get_user_file(user_id)
        
        if not os.path.exists(user_file):
            return None
        
        try:
            with open(user_file, 'r', encoding='utf-8') as f:
                user_data = json.load(f)
            
            return user_data.get(service, {})
        except:
            return None

    async def is_connected(self, user_id: int, service: str) -> bool:
        """Проверить, подключен ли сервис"""
        token = await self.get_token(user_id, service)
        return token is not None

# Глобальный экземпляр
user_tokens = UserTokenStorage()