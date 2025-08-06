#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простой тест распознавания email команд без aiogram
"""

import re

def extract_email_info_simple(text):
    """Извлечь информацию о письме из текста"""
    # Ищем паттерны для отправки письма
    patterns = [
        # Основные паттерны с "об"
        r"отправ[ьи].*письмо\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s+об\s+(.+)",
        r"отправ[ьи]\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s+об\s+(.+)",
        r"письмо\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s+об\s+(.+)",
        
        # Паттерны с "тема"
        r"отправ[ьи].*письмо.*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}).*тема[:\s]+(.+)",
        r"отправ[ьи].*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}).*тема[:\s]+(.+)",
        r"письмо.*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}).*тема[:\s]+(.+)",
        
        # Паттерны с "на"
        r"отправ[ьи].*письмо.*на\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}).*(?:тема|об)[:\s]+(.+)",
        r"письмо.*на\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}).*(?:тема|об)[:\s]+(.+)",
        
        # Дополнительные паттерны
        r"напиш[иь].*письмо\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s*[-–—]\s*об\s+(.+)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            email = match.group(1)
            subject = match.group(2).strip()
            
            return {
                "email": email,
                "subject": subject,
                "pattern": pattern
            }
    
    return None

def test_email_recognition():
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
        
        result = extract_email_info_simple(text)
        
        if result:
            print(f"✅ РАСПОЗНАНО:")
            print(f"   Email: {result['email']}")
            print(f"   Тема: {result['subject']}")
            print(f"   Паттерн: {result['pattern']}")
        else:
            print(f"❌ НЕ РАСПОЗНАНО")
        
        print()
    
    print("=== РЕЗУЛЬТАТ ===")
    print("Если первый тест НЕ распознается, нужно добавить паттерн для 'напиши письмо'")

if __name__ == "__main__":
    test_email_recognition()