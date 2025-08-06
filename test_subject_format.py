#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест умного форматирования темы письма
"""

def format_email_subject_test(raw_subject):
    """Тестовая версия форматирования темы"""
    subject = raw_subject.strip()
    
    # Убираем лишние предлоги в начале
    if subject.lower().startswith(('об ', 'о ', 'про ', 'касательно ')):
        preposition = subject.split(' ', 1)[0].lower()
        subject_without_prep = subject.split(' ', 1)[1] if ' ' in subject else subject
        
        # Анализируем падеж и корректируем
        if preposition in ['об', 'о']:
            if 'сдачи контракта' in subject_without_prep.lower():
                return "Успешная сдача контракта"
            elif 'успешной сдачи' in subject_without_prep.lower():
                return "Успешная сдача контракта"
            else:
                # Делаем первую букву заглавной
                return subject_without_prep[0].upper() + subject_without_prep[1:] if subject_without_prep else ""
    
    # Если тема короткая (2-3 слова), делаем более читаемой
    words = subject.split()
    if len(words) <= 3:
        # Убираем падежные окончания для существительных
        if words[-1].endswith(('ой', 'ей', 'ии', 'ия')):
            if 'сдачи' in words:
                idx = words.index('сдачи')
                words[idx] = 'сдача'
        
        # Делаем первое слово с заглавной буквы
        if words:
            words[0] = words[0][0].upper() + words[0][1:] if len(words[0]) > 1 else words[0].upper()
    
    # Собираем обратно
    formatted_subject = ' '.join(words)
    
    # Если тема очень короткая, добавляем контекст
    if len(formatted_subject.split()) == 1:
        formatted_subject = "Касательно: " + formatted_subject
    
    return formatted_subject

def test_subject_formatting():
    """Тест форматирования темы"""
    print("=== ТЕСТ ФОРМАТИРОВАНИЯ ТЕМЫ ПИСЬМА ===")
    print()
    
    test_cases = [
        ("успешной сдачи контракта", "Успешная сдача контракта"),
        ("об успешной сдачи контракта", "Успешная сдача контракта"),
        ("важной встречи", "Важной встречи"),
        ("отчет", "Касательно: отчет"),
        ("про новый проект", "Новый проект"),
        ("о сотрудничестве", "Сотрудничестве"),
    ]
    
    for raw, expected in test_cases:
        result = format_email_subject_test(raw)
        status = "OK" if result == expected else "FAIL"
        print(f"{status} '{raw}' -> '{result}'")
        if result != expected:
            print(f"   Ожидалось: '{expected}'")
        print()
    
    print("=== ДОПОЛНИТЕЛЬНЫЕ ТЕСТЫ ===")
    
    additional_tests = [
        "успешной сдачи",
        "поставки товара",
        "заключения договора",
        "об отпуске",
        "важное сообщение"
    ]
    
    for test in additional_tests:
        result = format_email_subject_test(test)
        print(f"'{test}' -> '{result}'")

if __name__ == "__main__":
    test_subject_formatting()