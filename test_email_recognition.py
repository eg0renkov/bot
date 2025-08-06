#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест распознавания email команд
"""

import sys
import os
import asyncio

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from handlers.messages import extract_email_info

async def test_email_recognition():
    """Тестируем распознавание email команд"""
    print("=== ТЕСТ РАСПОЗНАВАНИЯ EMAIL КОМАНД ===")
    print()
    
    test_messages = [
        "напиши письмо alexlesley01@yandex.ru - об успешной сдачи контракта",
        "отправь alexlesley01@yandex.ru об важной встрече",
        "отправить письмо test@example.com об тестовом письме",
        "письмо someone@mail.ru об работе",
        "надо отправить это письмо"
    ]
    
    for i, text in enumerate(test_messages, 1):
        print(f"ТЕСТ {i}: {text}")
        
        result = await extract_email_info(text)
        
        if result:
            print(f"✅ РАСПОЗНАНО:")
            print(f"   Email: {result['email']}")
            print(f"   Тема: {result['subject']}")
            print(f"   Текст: {result['body'][:100]}...")
        else:
            print(f"❌ НЕ РАСПОЗНАНО")
        
        print()
    
    print("=== РЕЗУЛЬТАТ ===")
    print("Если команды НЕ распознаются, проблема в регулярных выражениях")
    print("Если команды распознаются, проблема в другом месте кода")

if __name__ == "__main__":
    asyncio.run(test_email_recognition())