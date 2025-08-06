#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import asyncio

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from handlers.email_fix import format_email_subject_safe

async def test_subject_formatting():
    """Тест AI форматирования темы письма"""
    print("=== ТЕСТ AI ФОРМАТИРОВАНИЯ ТЕМЫ ПИСЬМА ===")
    print()
    
    test_cases = [
        "об успешной сдаче проекта",
        "о важной встрече", 
        "про новый проект",
        "касательно отчета",
        "по поводу работы",
        "об успешной сдаче контракта"
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"ТЕСТ {i}: '{test_case}'")
        try:
            result = await format_email_subject_safe(test_case)
            print(f"РЕЗУЛЬТАТ: '{result}'")
            print(f"СТАТУС: {'✅ OK' if 'успешная сдача' in result.lower() and 'об ' not in result.lower() else '❌ FAIL'}")
        except Exception as e:
            print(f"ОШИБКА: {e}")
        print("-" * 40)
        print()

if __name__ == "__main__":
    asyncio.run(test_subject_formatting())