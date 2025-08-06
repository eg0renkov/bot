#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест сохранения в черновики
"""

import sys
import os

# Добавляем путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.drafts import drafts_manager

def test_drafts():
    """Тест создания черновика"""
    print("=== ТЕСТ СОХРАНЕНИЯ В ЧЕРНОВИКИ ===")
    print()
    
    # Тестовые данные письма
    user_id = 123456789
    draft_data = {
        "to": "test@example.com",
        "subject": "Тестовое письмо",
        "body": "Это тестовое письмо для проверки черновиков"
    }
    
    try:
        print(f"Создаем черновик для пользователя {user_id}...")
        draft_id = drafts_manager.create_draft(user_id, draft_data)
        print(f"Черновик создан с ID: {draft_id}")
        
        print("\nПолучаем все черновики пользователя...")
        drafts = drafts_manager.get_all_drafts(user_id)
        print(f"Найдено черновиков: {len(drafts)}")
        
        if drafts:
            latest_draft = drafts[-1]
            print(f"\nПоследний черновик:")
            print(f"- ID: {latest_draft['id']}")
            print(f"- Кому: {latest_draft['to']}")
            print(f"- Тема: {latest_draft['subject']}")
            print(f"- Текст: {latest_draft['body'][:50]}...")
            print(f"- Создан: {latest_draft['created_at']}")
        
        print("\nТест успешен!")
        return True
        
    except Exception as e:
        print(f"ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_drafts()