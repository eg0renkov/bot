#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест озвучки текста
"""

import asyncio
import sys
import os

# Добавляем путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.openai_client import openai_client

async def test_text_to_speech():
    """Тест озвучки текста"""
    print("=== ТЕСТ ОЗВУЧКИ ТЕКСТА ===")
    print()
    
    test_text = "Привет! Это тест озвучки от бота."
    
    try:
        print(f"Озвучиваем текст: '{test_text}'")
        voice_data = await openai_client.text_to_speech(test_text)
        
        if voice_data:
            print(f"Получено {len(voice_data)} байт аудио данных")
            
            # Сохраняем в файл для проверки
            test_file = "test_voice.mp3"
            with open(test_file, 'wb') as f:
                f.write(voice_data)
            print(f"Аудио сохранено в {test_file}")
            
            # Проверяем размер файла
            file_size = os.path.getsize(test_file)
            print(f"Размер файла: {file_size} байт")
            
            if file_size > 100:
                print("✅ Озвучка работает!")
            else:
                print("❌ Файл слишком мал - возможно ошибка")
                
        else:
            print("❌ Не получены аудио данные")
            
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_text_to_speech())