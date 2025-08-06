import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

class Settings:
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    # OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
    
    # Supabase
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    
    # Yandex (опционально)
    YANDEX_CLIENT_ID = os.getenv('YANDEX_CLIENT_ID')
    YANDEX_CLIENT_SECRET = os.getenv('YANDEX_CLIENT_SECRET')
    
    # SERP API (опционально)
    SERP_API_KEY = os.getenv('SERP_API_KEY')
    
    # Настройки бота
    MAX_MESSAGE_LENGTH = 4000
    MAX_HISTORY_MESSAGES = 20
    VOICE_ENABLED = True
    MEMORY_ENABLED = True
    VECTOR_MEMORY_ENABLED = os.getenv('VECTOR_MEMORY_ENABLED', 'false').lower() == 'true'
    
    # Логирование
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    @classmethod
    def validate(cls):
        """Проверка обязательных настроек"""
        required_settings = [
            'TELEGRAM_BOT_TOKEN',
            'OPENAI_API_KEY'
        ]
        
        missing = []
        for setting in required_settings:
            if not getattr(cls, setting):
                missing.append(setting)
        
        if missing:
            raise ValueError(f"Отсутствуют обязательные настройки: {', '.join(missing)}")
        
        return True

settings = Settings()