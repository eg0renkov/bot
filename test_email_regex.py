#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Быстрый тест регулярных выражений для email команд
"""

import re

def test_email_patterns():
    print("=== ТЕСТ РЕГУЛЯРНЫХ ВЫРАЖЕНИЙ ===")
    
    patterns = [
        # Паттерны с "напиши письмо" - НОВЫЕ
        r"напиш[иь].*письмо\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s*[-–—]\s*об\s+(.+)",
        r"напиш[иь].*письмо\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s+об\s+(.+)",
        
        # Основные паттерны с "об"
        r"отправ[ьи].*письмо\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s+об\s+(.+)",
        r"отправ[ьи]\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s+об\s+(.+)",
        r"письмо\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s+об\s+(.+)",
    ]
    
    test_text = "напиши письмо alexlesley01@yandex.ru о подорожании сыра"
    print(f"Тестовый текст: '{test_text}'")
    print()
    
    for i, pattern in enumerate(patterns):
        print(f"Паттерн {i+1}: {pattern}")
        match = re.search(pattern, test_text, re.IGNORECASE)
        if match:
            print(f"SUCCESS! Email: {match.group(1)}, Тема: {match.group(2)}")
        else:
            print(f"NO MATCH")
        print()

if __name__ == "__main__":
    test_email_patterns()