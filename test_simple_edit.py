#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простой тест редактирования без aiogram
"""

import re

def extract_email_edit_command_simple(text):
    """Простое извлечение команды редактирования"""
    edit_patterns = [
        r"допиш[иь].*?(.+)",
        r"доба[вь].*?(.+)", 
        r"измен[иь].*?(.+)",
        r"исправ[ьи].*?(.+)",
        r"перепиш[иь].*?(.+)"
    ]
    
    for pattern in edit_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            edit_text = match.group(1).strip()
            return {
                "type": "edit",
                "text": edit_text,
                "original_command": text
            }
    
    return None

def test_edit_commands():
    """Тест команд редактирования"""
    print("=== ТЕСТ КОМАНД РЕДАКТИРОВАНИЯ ===")
    print()
    
    test_commands = [
        "допиши добрый день Александр",
        "добавь информацию о встрече", 
        "измени текст на новый",
        "исправь ошибки в письме",
        "перепиши это письмо"
    ]
    
    for cmd in test_commands:
        result = extract_email_edit_command_simple(cmd)
        if result:
            print(f"✅ '{cmd}'")
            print(f"   -> Текст: '{result['text']}'")
        else:
            print(f"❌ '{cmd}' -> НЕ РАСПОЗНАНО")
        print()
    
    print("РЕЗУЛЬТАТ: Все команды должны распознаваться")

if __name__ == "__main__":
    test_edit_commands()