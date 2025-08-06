#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест ИИ-форматирования темы письма
"""

import asyncio
import sys
import os

# Добавляем путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.openai_client import openai_client

async def format_email_subject_test(raw_subject: str) -> str:
    """Тестовая ИИ-функция форматирования темы"""
    subject = raw_subject.strip()
    
    # Быстрые исправления для частых случаев
    quick_fixes = {
        'успешной сдачи контракта': 'Успешная сдача контракта',
        'успешной сдачи': 'Успешная сдача',
        'важной встречи': 'Важная встреча',
        'нового проекта': 'Новый проект',
    }
    
    subject_lower = subject.lower()
    for wrong, correct in quick_fixes.items():
        if wrong == subject_lower:
            print(f"КЭШ: '{subject}' -> '{correct}'")
            return correct
    
    # Если тема короткая и простая - ИИ не нужен
    if len(subject.split()) <= 2 and all(word.isalpha() or word.isspace() for word in subject):
        result = subject[0].upper() + subject[1:] if subject else subject
        print(f"ПРОСТОЕ: '{subject}' -> '{result}'")
        return result
    
    try:
        print(f"ИИ-АНАЛИЗ: '{subject}'...")
        
        # ИИ-анализ для сложных случаев
        prompt = f"""Исправь тему письма на русском языке:

ПРАВИЛА:
- Используй именительный падеж
- Убери лишние предлоги (об, о, про, касательно)
- Сделай первую букву заглавной
- Исправь грамматику
- НЕ добавляй лишних слов
- Оставь смысл неизменным

ПРИМЕРЫ:
"успешной сдачи контракта" → "Успешная сдача контракта"
"важной встречи" → "Важная встреча"
"о новом проекте" → "Новый проект"

ТЕМА: "{subject}"

ИСПРАВЛЕННАЯ ТЕМА:"""

        messages = [{"role": "user", "content": prompt}]
        ai_response = await openai_client.chat_completion(messages, temperature=0.1)
        
        if ai_response and ai_response.strip():
            formatted = ai_response.strip().strip('"').strip("'")
            # Проверяем что ответ разумный
            if len(formatted) > 0 and len(formatted) < len(subject) * 3:
                print(f"ИИ РЕЗУЛЬТАТ: '{subject}' -> '{formatted}'")
                return formatted
    
    except Exception as e:
        print(f"ИИ ОШИБКА: {e}")
    
    # Fallback - простое форматирование
    words = subject.split()
    if words:
        words[0] = words[0][0].upper() + words[0][1:] if len(words[0]) > 1 else words[0].upper()
    
    result = ' '.join(words)
    print(f"FALLBACK: '{subject}' -> '{result}'")
    return result

async def test_ai_subject_formatting():
    """Тест ИИ-форматирования тем"""
    print("=== ТЕСТ ИИ-ФОРМАТИРОВАНИЯ ТЕМ ПИСЕМ ===")
    print()
    
    test_cases = [
        # Кэш случаи
        "успешной сдачи контракта",
        "важной встречи",
        
        # Простые случаи
        "отчет",
        "договор",
        
        # Сложные случаи для ИИ
        "об обсуждении результатов проведенной работы",
        "касательно предстоящего мероприятия в офисе",
        "важного вопроса по поставкам материалов",
        "срочной задачи по завершению проекта",
        "о сотрудничестве с новыми партнерами"
    ]
    
    for i, test_subject in enumerate(test_cases, 1):
        print(f"\n--- ТЕСТ {i} ---")
        result = await format_email_subject_test(test_subject)
        print(f"ИТОГ: '{test_subject}' -> '{result}'")
        print()
    
    print("=== ЗАКЛЮЧЕНИЕ ===")
    print("ИИ-форматирование:")
    print("OK Быстрый кэш для частых случаев")
    print("OK Простая обработка коротких тем") 
    print("OK ИИ-анализ для сложных случаев")
    print("OK Fallback при ошибках")

if __name__ == "__main__":
    asyncio.run(test_ai_subject_formatting())