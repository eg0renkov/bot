import json
import os
from typing import Set, Optional
from datetime import datetime

class AuthManager:
    """Менеджер авторизации пользователей"""
    
    def __init__(self):
        self.auth_file = "data/authorized_users.json"
        self.access_token = "SECURE_BOT_ACCESS_2024"  # Статичный токен доступа
        self.authorized_users: Set[int] = set()
        self._load_authorized_users()
    
    def _load_authorized_users(self):
        """Загрузить список авторизованных пользователей"""
        try:
            os.makedirs(os.path.dirname(self.auth_file), exist_ok=True)
            
            if os.path.exists(self.auth_file):
                with open(self.auth_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.authorized_users = set(data.get('authorized_users', []))
            else:
                # Создаем пустой файл
                self._save_authorized_users()
                
        except Exception as e:
            print(f"Ошибка загрузки авторизованных пользователей: {e}")
            self.authorized_users = set()
    
    def _save_authorized_users(self):
        """Сохранить список авторизованных пользователей"""
        try:
            data = {
                'authorized_users': list(self.authorized_users),
                'updated_at': datetime.now().isoformat(),
                'access_token_hint': self.access_token[:4] + "***"  # Показываем только первые 4 символа
            }
            
            with open(self.auth_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Ошибка сохранения авторизованных пользователей: {e}")
    
    def is_user_authorized(self, user_id: int) -> bool:
        """Проверить, авторизован ли пользователь"""
        return user_id in self.authorized_users
    
    def authorize_user(self, user_id: int, token: str) -> bool:
        """Авторизовать пользователя по токену"""
        if token.strip() == self.access_token:
            self.authorized_users.add(user_id)
            self._save_authorized_users()
            print(f"Пользователь {user_id} успешно авторизован")
            return True
        else:
            print(f"Неверный токен от пользователя {user_id}: {token[:10]}...")
            return False
    
    def revoke_user_access(self, user_id: int) -> bool:
        """Отозвать доступ пользователя"""
        if user_id in self.authorized_users:
            self.authorized_users.remove(user_id)
            self._save_authorized_users()
            print(f"Доступ пользователя {user_id} отозван")
            return True
        return False
    
    def get_authorized_count(self) -> int:
        """Получить количество авторизованных пользователей"""
        return len(self.authorized_users)
    
    def get_auth_stats(self) -> dict:
        """Получить статистику авторизации"""
        return {
            'total_authorized': len(self.authorized_users),
            'authorized_users': list(self.authorized_users),
            'token_hint': self.access_token[:4] + "***"
        }
    
    def check_token_format(self, token: str) -> dict:
        """Проверить формат токена и дать подсказки"""
        token = token.strip()
        print(f"DEBUG: Проверка токена: '{token}' vs '{self.access_token}' (равны: {token == self.access_token})")
        
        if not token:
            return {
                'valid': False,
                'hint': 'Токен не может быть пустым'
            }
        
        if len(token) < 10:
            return {
                'valid': False,
                'hint': f'Токен слишком короткий (получено {len(token)} символов, ожидается больше)'
            }
        
        if token == self.access_token:
            return {
                'valid': True,
                'hint': 'Токен корректен'
            }
        
        # Анализируем ошибки
        hints = []
        
        if not token.startswith(self.access_token[:4]):
            hints.append('Токен начинается неправильно')
        
        if len(token) != len(self.access_token):
            hints.append(f'Неправильная длина токена (получено {len(token)}, ожидается {len(self.access_token)})')
        
        if token.lower() == self.access_token.lower():
            hints.append('Проверьте регистр символов')
        
        return {
            'valid': False,
            'hint': '; '.join(hints) if hints else 'Токен неверный'
        }

# Глобальный экземпляр
auth_manager = AuthManager()