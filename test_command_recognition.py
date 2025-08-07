#!/usr/bin/env python3
"""
Тест исправления распознавания команд контактов и календаря
"""
import asyncio
import re
import sys
import os

# Добавляем путь к модулям
sys.path.append('.')

async def extract_calendar_command(text: str) -> dict:
    """Извлечь команду создания события календаря"""
    text_lower = text.lower()
    
    # Проверяем что это НЕ email команда (содержит @ символ)
    if '@' in text:
        return None
    
    # ВАЖНО: Проверяем что это НЕ команда контакта
    contact_exclusions = ['контакт', 'номер', 'телефон', '+7', '+3', '+8', '+9']
    if any(exclusion in text_lower for exclusion in contact_exclusions):
        return None
    
    calendar_patterns = [
        # Паттерны с "добавь" и временем (более специфичные)
        r"добав[ьи].*(?:что\s+)?(?:сегодня|завтра|в\s+\w+)\s+(?:в\s+)?(\d{1,2}:?\d{0,2}?)\s*(.+)",
        r"добав[ьи].*(?:что\s+)?(.+)\s+(?:сегодня|завтра|в\s+\w+)\s+(?:в\s+)?(\d{1,2}:?\d{0,2}?)",
        
        # Паттерны со "встреча"
        r"встреча\s+(.+)",
        r"(.+)\s+встреча",
        
        # Паттерны с указанием времени
        r"(.+)\s+в\s+(\d{1,2}:?\d{0,2}?)",
        
        # Общие паттерны создания событий
        r"создай\s+событие\s+(.+)",
        r"запланируй\s+(.+)",
        r"напомни\s+(.+)",
        
        # УБРАЛИ общий паттерн r"добав[ьи].*(?:что\s+)?(.+)" который ловил все команды "добавь"
        # Теперь "добавь" работает только с конкретными временными указаниями выше
    ]
    
    # Проверяем календарные ключевые слова (но исключаем "добавь" как единственный признак)
    calendar_keywords = ['встреча', 'событие', 'запланируй', 'напомни', 'сегодня', 'завтра']
    has_calendar_keywords = any(word in text_lower for word in calendar_keywords)
    
    # Для команд с "добавь" требуем дополнительные календарные признаки
    if 'добавь' in text_lower and not has_calendar_keywords:
        return None
    
    if not has_calendar_keywords and 'добавь' not in text_lower:
        return None
    
    for pattern in calendar_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return {
                "text": text,
                "match": match.groups(),
                "is_calendar": True
            }
    
    return None

async def test_commands():
    """Тестируем различные команды"""
    
    print("=== ТЕСТИРОВАНИЕ РАСПОЗНАВАНИЯ КОМАНД ===\n")
    
    # Команды контактов (НЕ должны распознаваться как календарные)
    contact_commands = [
        "добавь контакт Анны +79186057593",
        "добавь контакт Петр email@test.com",
        "создай контакт Мария +79123456789",
        "сохрани контакт Иван номер 123456",
        "добавь телефон Светлана +79998887766"
    ]
    
    # Команды календаря (ДОЛЖНЫ распознаваться как календарные)
    calendar_commands = [
        "добавь встречу завтра в 15:00",
        "добавь что сегодня встреча с клиентом",
        "создай событие презентация",
        "запланируй встречу завтра",
        "напомни про совещание",
        "встреча с командой завтра",
        "добавь событие завтра в 12:30 обед с партнерами"
    ]
    
    # Обычные команды добавления (НЕ должны быть календарными)
    regular_commands = [
        "добавь в список покупок молоко",
        "добавь заметку про проект",
        "добавь файл в папку",
    ]
    
    print("КОМАНДЫ КОНТАКТОВ (должны быть НЕ календарными):")
    for cmd in contact_commands:
        result = await extract_calendar_command(cmd)
        status = "ОШИБКА: распознано как календарь!" if result else "Правильно: НЕ календарь"
        print(f"  {status} - '{cmd}'")
    
    print(f"\nКОМАНДЫ КАЛЕНДАРЯ (должны быть календарными):")
    for cmd in calendar_commands:
        result = await extract_calendar_command(cmd)
        status = "Правильно: календарь" if result else "ОШИБКА: НЕ распознано как календарь!"
        print(f"  {status} - '{cmd}'")
    
    print(f"\nОБЫЧНЫЕ КОМАНДЫ (должны быть НЕ календарными):")
    for cmd in regular_commands:
        result = await extract_calendar_command(cmd)
        status = "ОШИБКА: распознано как календарь!" if result else "Правильно: НЕ календарь"
        print(f"  {status} - '{cmd}'")

if __name__ == "__main__":
    asyncio.run(test_commands())