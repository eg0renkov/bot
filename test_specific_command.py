#!/usr/bin/env python3
"""
Тест конкретной команды "добавь контакт Анны +79186057593"
"""
import asyncio
import re
import sys

# Копируем точную функцию из messages.py
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

async def test_specific_command():
    """Тест конкретной проблемной команды"""
    test_command = "добавь контакт Анны +79186057593"
    print(f"Тестируем команду: '{test_command}'")
    
    text_lower = test_command.lower()
    print(f"text_lower: '{text_lower}'")
    
    # Проверяем исключения
    contact_exclusions = ['контакт', 'номер', 'телефон', '+7', '+3', '+8', '+9']
    print(f"contact_exclusions: {contact_exclusions}")
    
    exclusion_found = [exclusion for exclusion in contact_exclusions if exclusion in text_lower]
    print(f"Найденные исключения: {exclusion_found}")
    
    if exclusion_found:
        print(f"✅ ДОЛЖНА вернуть None из-за исключений: {exclusion_found}")
    else:
        print(f"❌ НЕ найдено исключений!")
    
    result = await extract_calendar_command(test_command)
    print(f"Результат extract_calendar_command: {result}")
    
    if result is None:
        print("✅ ОТЛИЧНО: Команда контакта НЕ распознана как календарная")
    else:
        print("❌ ПРОБЛЕМА: Команда контакта распознана как календарная!")
        print(f"Подробности: {result}")

if __name__ == "__main__":
    asyncio.run(test_specific_command())