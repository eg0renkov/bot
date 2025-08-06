#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест текущей реализации форматирования темы
"""

# Копируем функцию из handlers/messages.py
def format_email_subject(raw_subject: str) -> str:
    """Умное форматирование темы письма"""
    subject = raw_subject.strip()
    
    # Словарь для замены неправильных падежей
    replacements = {
        'успешной сдачи контракта': 'Успешная сдача контракта',
        'успешной сдачи': 'Успешная сдача',
        'важной встречи': 'Важная встреча',
        'нового проекта': 'Новый проект',
        'срочного вопроса': 'Срочный вопрос',
        'отчета за месяц': 'Отчет за месяц',
        'заключения договора': 'Заключение договора',
        'поставки товара': 'Поставка товара',
    }
    
    # Проверяем точные совпадения
    subject_lower = subject.lower()
    for wrong, correct in replacements.items():
        if wrong in subject_lower:
            return correct
    
    # Убираем предлоги в начале если есть
    prepositions = ['об ', 'о ', 'про ', 'касательно ', 'по поводу ', 'насчет ', 'относительно ']
    for prep in prepositions:
        if subject_lower.startswith(prep):
            subject = subject[len(prep):].strip()
            break
    
    # Преобразуем первое слово в именительный падеж если возможно
    words = subject.split()
    if words:
        first_word = words[0].lower()
        
        # Простые замены для частых случаев
        nominative_map = {
            'успешной': 'Успешная',
            'важной': 'Важная',
            'срочной': 'Срочная',
            'новой': 'Новая',
            'нового': 'Новый',
            'важного': 'Важный',
            'текущего': 'Текущий',
        }
        
        if first_word in nominative_map:
            words[0] = nominative_map[first_word]
        else:
            # Делаем первую букву заглавной
            words[0] = words[0][0].upper() + words[0][1:] if len(words[0]) > 1 else words[0].upper()
    
    # Собираем обратно
    formatted_subject = ' '.join(words)
    
    # Для очень коротких тем (1 слово) можем добавить контекст
    if len(words) == 1 and len(formatted_subject) < 10:
        formatted_subject = f"Тема: {formatted_subject}"
    
    return formatted_subject

def test_current_implementation():
    """Тест текущей реализации"""
    print("=== ТЕСТ ТЕКУЩЕЙ РЕАЛИЗАЦИИ ФОРМАТИРОВАНИЯ ===")
    print()
    
    test_cases = [
        "успешной сдачи контракта",
        "об успешной сдачи контракта", 
        "важной встречи",
        "про новый проект",
        "отчет",
        "нового проекта",
        "касательно важного вопроса"
    ]
    
    for test in test_cases:
        result = format_email_subject(test)
        print(f"'{test}' -> '{result}'")
    
    print()
    print("=== ЗАКЛЮЧЕНИЕ ===")
    print("Основные исправления:")
    print("1. 'успешной сдачи контракта' -> 'Успешная сдача контракта'")
    print("2. Убираются предлоги в начале")
    print("3. Первое слово переводится в именительный падеж")

if __name__ == "__main__":
    test_current_implementation()