#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест редактирования email
"""

import sys
import os
import asyncio

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from handlers.messages import extract_email_edit_command
from utils.temp_emails import temp_emails

async def test_email_editing():
    """Тестируем редактирование email"""
    print("=== ТЕСТ РЕДАКТИРОВАНИЯ EMAIL ===")
    print()
    
    # Тестируем распознавание команд
    test_commands = [
        "допиши добрый день Александр",
        "добавь информацию о встрече",
        "измени текст на новый",
        "исправь ошибки в письме"
    ]
    
    print("1. ТЕСТ РАСПОЗНАВАНИЯ КОМАНД:")
    for cmd in test_commands:
        result = await extract_email_edit_command(cmd)
        if result:
            print(f"✅ '{cmd}' -> '{result['text']}'")
        else:
            print(f"❌ '{cmd}' -> НЕ РАСПОЗНАНО")
    
    print("\n2. ТЕСТ СОЗДАНИЯ И РЕДАКТИРОВАНИЯ EMAIL:")
    
    # Создаем тестовое письмо
    user_id = 12345
    email_id = temp_emails.create_email(
        user_id=user_id,
        to_email="test@example.com",
        subject="Тестовая тема",
        body="Добрый день!\n\nПишу вам по поводу тестового письма.\n\nС уважением,\nТест"
    )
    
    print(f"Создано письмо ID: {email_id}")
    
    # Получаем последнее письмо
    latest = temp_emails.get_user_latest_email(user_id)
    if latest:
        print(f"✅ Найдено последнее письмо: {latest['id']}")
        print(f"Текст до редактирования:")
        print(latest['body'])
        
        # Симулируем редактирование
        new_body = latest['body'] + "\n\nP.S. Добавлено через редактирование"
        temp_emails.update_email(latest['id'], body=new_body)
        
        updated = temp_emails.get_email(latest['id'])
        print(f"\nТекст после редактирования:")
        print(updated['body'])
        print("\n✅ Редактирование работает!")
    else:
        print("❌ Не найдено последнее письмо")
    
    # Очищаем тестовые файлы
    temp_emails.delete_email(email_id)
    print(f"\nТестовое письмо {email_id} удалено")

if __name__ == "__main__":
    asyncio.run(test_email_editing())