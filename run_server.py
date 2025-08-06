#!/usr/bin/env python3
"""
Основной файл запуска бота на сервере
"""
import sys
import os

# Добавляем корневую папку в путь Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Импортируем и запускаем бота
if __name__ == "__main__":
    from bot.main import main
    import asyncio
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен пользователем")
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        sys.exit(1)