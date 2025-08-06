#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Симуляция AI функции для тестирования
def mock_ai_edit(current_body: str, edit_command: str, edit_text: str) -> str:
    """Имитация AI редактирования для тестирования логики"""
    
    # Примеры того, как AI должен анализировать команды
    examples = {
        "добавь добрый день Александр": {
            "action": "replace_greeting",
            "result": lambda body: f"Добрый день, Александр!\n\n{body.split('\\n', 1)[1] if '\\n' in body else body}"
        },
        "добавь с уважением Алексей": {
            "action": "add_signature", 
            "result": lambda body: f"{body}\n\nС уважением,\nАлексей"
        },
        "дописать важную информацию": {
            "action": "append_content",
            "result": lambda body: f"{body}\n\nВажная информация."
        }
    }
    
    # Простая логика определения типа команды
    edit_lower = edit_text.lower()
    
    if any(greeting in edit_lower for greeting in ['добрый день', 'здравствуйте', 'привет']):
        # Это обращение - заменяем первую строку
        lines = current_body.split('\n')
        name = edit_text.split()[-1] if len(edit_text.split()) > 2 else ""
        if name and name.lower() not in ['день', 'утро', 'вечер']:
            greeting = f"Добрый день, {name}!"
        else:
            greeting = "Добрый день!"
        lines[0] = greeting
        return '\n'.join(lines)
    
    elif any(sig in edit_lower for sig in ['с уважением', 'всего доброго']):
        # Это подпись - добавляем в конец
        name = edit_text.split()[-1] if len(edit_text.split()) > 2 else ""
        if name and name.lower() not in ['уважением', 'доброго']:
            signature = f"С уважением,\n{name}"
        else:
            signature = "С уважением"
        return f"{current_body}\n\n{signature}"
    
    else:
        # Обычное добавление в конец
        return f"{current_body}\n\n{edit_text}"

def test_ai_edit():
    current_body = """Добрый день!

Пишу вам по поводу подорожании сыра.

С уважением,
Алексей"""

    test_cases = [
        ("добавь", "добрый день Александр"),
        ("добавь", "с уважением Петр"),
        ("дописать", "важная информация о ценах"),
        ("замени", "здравствуйте Мария")
    ]
    
    for command, text in test_cases:
        result = mock_ai_edit(current_body, command, text)
        print(f"Команда: '{command} {text}'")
        print(f"Результат:\n{result}")
        print("-" * 50)

if __name__ == "__main__":
    test_ai_edit()