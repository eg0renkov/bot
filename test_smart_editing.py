#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест умного редактирования email
"""

import asyncio

async def smart_email_edit_test(current_body: str, edit_command: str, edit_text: str) -> str:
    """Тестовая версия умного редактирования"""
    command_lower = edit_command.lower()
    
    # 1. ОБРАЩЕНИЯ - заменяем в начале письма
    greeting_words = ['добрый день', 'доброе утро', 'добрый вечер', 'здравствуйте', 'привет', 'уважаемый']
    if any(word in edit_text.lower() for word in greeting_words):
        lines = current_body.split('\n')
        first_line = lines[0] if lines else ""
        
        if any(word in first_line.lower() for word in greeting_words):
            lines[0] = edit_text + ("!" if not edit_text.endswith(('!', '.', ',')) else "")
            return '\n'.join(lines)
        else:
            return f"{edit_text}!\n\n{current_body}"
    
    # 2. ПОДПИСЬ - заменяем/добавляем в конце
    signature_words = ['с уважением', 'с наилучшими', 'всего доброго', 'до свидания', 'жду ответа']
    if any(word in edit_text.lower() for word in signature_words):
        lines = current_body.split('\n')
        
        signature_found = False
        for i in range(len(lines)-1, max(0, len(lines)-5), -1):
            if any(word in lines[i].lower() for word in signature_words):
                lines[i] = edit_text
                signature_found = True
                break
        
        if not signature_found:
            return f"{current_body}\n\n{edit_text}"
        else:
            return '\n'.join(lines)
    
    # 3. ПОЗИЦИОННЫЕ КОМАНДЫ
    if 'в начал' in command_lower or 'сначал' in command_lower:
        return f"{edit_text}\n\n{current_body}"
    elif 'в конц' in command_lower or 'в конце' in command_lower:
        return f"{current_body}\n\n{edit_text}"
    
    # 4. ПО УМОЛЧАНИЮ - простое добавление
    return f"{current_body}\n\n{edit_text}"

async def test_smart_editing():
    """Тест умного редактирования"""
    print("=== ТЕСТ УМНОГО РЕДАКТИРОВАНИЯ EMAIL ===")
    print()
    
    # Тестовое письмо
    original_email = """Добрый день!

Пишу вам по поводу успешной сдачи контракта.

С уважением,
Алексей"""
    
    test_cases = [
        {
            "command": "допиши добрый день Александр",
            "expected": "Заменить обращение на 'Добрый день, Александр!'"
        },
        {
            "command": "допиши добрый день Александр в начало письма", 
            "expected": "Добавить в самое начало"
        },
        {
            "command": "добавь жду скорого ответа",
            "expected": "Заменить подпись"
        },
        {
            "command": "допиши информацию о сроках в конец",
            "expected": "Добавить в конец"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"ТЕСТ {i}: {test_case['command']}")
        print(f"Ожидается: {test_case['expected']}")
        print()
        
        # Извлекаем текст команды (простая симуляция)
        if "допиши" in test_case['command']:
            edit_text = test_case['command'].replace("допиши ", "").replace(" в начало письма", "").replace(" в конец", "")
        elif "добавь" in test_case['command']:
            edit_text = test_case['command'].replace("добавь ", "")
        else:
            edit_text = test_case['command']
        
        result = await smart_email_edit_test(original_email, test_case['command'], edit_text)
        
        print("РЕЗУЛЬТАТ:")
        print("-" * 40)
        print(result)
        print("-" * 40)
        print()
    
    print("=== ЗАКЛЮЧЕНИЕ ===")
    print("Умное редактирование должно:")
    print("1. Заменять обращения в начале")
    print("2. Заменять подписи в конце") 
    print("3. Понимать позиционные команды")
    print("4. Анализировать контекст")

if __name__ == "__main__":
    asyncio.run(test_smart_editing())