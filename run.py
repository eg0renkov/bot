#!/usr/bin/env python3
"""
Скрипт запуска Telegram AI бота
Запуск: python run.py
"""

import sys
import os

# Добавляем текущую директорию в PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.main import main
import asyncio

if __name__ == "__main__":
    print("Запуск Telegram AI бота...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nБот остановлен. До свидания!")
    except Exception as e:
        print(f"Ошибка запуска: {e}")
        sys.exit(1)