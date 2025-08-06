#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def fix_transcription_errors(text: str) -> str:
    """Исправляет типичные ошибки транскрипции голосовых сообщений"""
    if not text:
        return text
    
    # Словарь типичных ошибок распознавания
    corrections = {
        # Команды добавления
        "добавь туда": "добавь",
        "добавь сюда": "добавь", 
        "дописать туда": "дописать",
        "дописки туда": "дописать",
        "дописка туда": "дописать",
        
        # Команды изменения
        "измени туда": "измени",
        "замени туда": "замени",
        "поменяй туда": "поменяй",
        
        # Обращения
        "добры день": "добрый день",
        "добрый деня": "добрый день",
        "доброе утра": "доброе утро",
        "здравствуй те": "здравствуйте",
        
        # Другие типичные ошибки
        "с уважение": "с уважением",
        "с уважением.": "с уражением,",
    }
    
    result = text
    for error, correction in corrections.items():
        result = result.replace(error, correction)
    
    # Убираем лишние "туда" после команд редактирования
    import re
    result = re.sub(r'\b(добавь|дописать|измени|замени|поменяй)\s+туда\b', r'\1', result, flags=re.IGNORECASE)
    
    if result != text:
        print(f"Fixed: '{text}' -> '{result}'")
    
    return result

def test_fixes():
    test_cases = [
        "добавь туда добрый день Александр",
        "дописать туда с уважением",
        "измени туда здравствуй те",
        "замени туда доброе утра",
        "добавь сюда привет",
        "поменяй туда добры день"
    ]
    
    for test in test_cases:
        fixed = fix_transcription_errors(test)
        print(f"Input:  '{test}'")
        print(f"Output: '{fixed}'")
        print()

if __name__ == "__main__":
    test_fixes()