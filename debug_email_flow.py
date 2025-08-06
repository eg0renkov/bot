#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Отладка email обработки
"""

import re

def test_new_patterns():
    """Тест новых паттернов"""
    print("=== ТЕСТ НОВЫХ ПАТТЕРНОВ ===")
    
    patterns = [
        # Паттерны с "напиши письмо" - НОВЫЕ
        r"напиш[иь].*письмо\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s*[-–—]\s*об\s+(.+)",
        r"напиш[иь].*письмо\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s+об\s+(.+)",
    ]
    
    test_text = "напиши письмо alexlesley01@yandex.ru - об успешной сдачи контракта"
    print(f"Тестируем: {test_text}")
    
    for i, pattern in enumerate(patterns, 1):
        match = re.search(pattern, test_text, re.IGNORECASE)
        if match:
            print(f"✅ Паттерн {i} сработал!")
            print(f"   Email: {match.group(1)}")
            print(f"   Тема: {match.group(2)}")
            return True
        else:
            print(f"❌ Паттерн {i} НЕ сработал")
    
    return False

def analyze_problem():
    """Анализ возможных проблем"""
    print("\n=== АНАЛИЗ ПРОБЛЕМ ===")
    
    print("ВОЗМОЖНЫЕ ПРИЧИНЫ отсутствия email кнопок:")
    print("1. Команда НЕ распознается (паттерны)")
    print("2. Почта НЕ подключена (can_send_email = False)")
    print("3. Ошибка в обработке (exception в try/catch)")
    print("4. Проблема с temp_emails или email_improver")
    print("5. Ошибка в keyboards.email_confirm_menu()")
    
    print("\nЧТО ДЕЛАТЬ:")
    print("1. Запустить бота и попробовать команду")
    print("2. Смотреть в консоль на DEBUG сообщения")
    print("3. Если DEBUG нет - команда не распознается")
    print("4. Если DEBUG есть - смотреть дальше по логам")

if __name__ == "__main__":
    success = test_new_patterns()
    if success:
        print("\n✅ ПАТТЕРНЫ РАБОТАЮТ!")
    else:
        print("\n❌ ПАТТЕРНЫ НЕ РАБОТАЮТ!")
    
    analyze_problem()