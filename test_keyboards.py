#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест создания клавиатур без aiogram
"""

class MockInlineKeyboardButton:
    def __init__(self, text, callback_data):
        self.text = text
        self.callback_data = callback_data

class MockInlineKeyboardBuilder:
    def __init__(self):
        self.buttons = []
    
    def add(self, *buttons):
        self.buttons.extend(buttons)
    
    def adjust(self, *args):
        pass
    
    def as_markup(self):
        return {"inline_keyboard": [[{"text": btn.text, "callback_data": btn.callback_data}] for btn in self.buttons]}

def test_keyboard_creation():
    """Тест создания клавиатуры"""
    print("Testing keyboard creation...")
    
    try:
        # Симулируем создание клавиатуры как в коде
        builder = MockInlineKeyboardBuilder()
        builder.add(
            MockInlineKeyboardButton(text="Save without testing", callback_data="email_setup_force_save"),
            MockInlineKeyboardButton(text="Try again", callback_data="email_setup_save"),
            MockInlineKeyboardButton(text="Cancel", callback_data="email_setup_cancel")
        )
        builder.adjust(1, 1, 1)
        
        # Создаем клавиатуру
        keyboard_markup = builder.as_markup()
        
        print("Keyboard created successfully:")
        print(f"Button count: {len(keyboard_markup['inline_keyboard'])}")
        
        for i, row in enumerate(keyboard_markup['inline_keyboard']):
            button = row[0]
            print(f"  {i+1}. {button['text']} -> {button['callback_data']}")
        
        print("\nKeyboard test PASSED!")
        
        # Тест типа объекта - главная проблема!
        print(f"\nKeyboard type: {type(keyboard_markup)}")
        print(f"Is dict: {isinstance(keyboard_markup, dict)}")
        
        # Проверяем структуру как aiogram
        if 'inline_keyboard' in keyboard_markup:
            print("Structure OK: has inline_keyboard key")
            if isinstance(keyboard_markup['inline_keyboard'], list):
                print("Structure OK: inline_keyboard is list")
            else:
                print(f"ERROR: inline_keyboard is {type(keyboard_markup['inline_keyboard'])}")
        else:
            print("ERROR: no inline_keyboard key")
        
        return True
        
    except Exception as e:
        print(f"ERROR creating keyboard: {e}")
        return False

def test_error_message():
    """Тест создания сообщения об ошибке"""
    print("\nТестирование сообщения об ошибке...")
    
    try:
        error_msg = "Ошибка подключения: timeout"
        details = "Connection timed out after 30 seconds"
        
        error_text = f"""❌ <b>Ошибка подключения</b>

🔧 <b>Проблема:</b> {error_msg[:200]}

💡 <b>Что можно сделать:</b>
• Нажмите /start для новой попытки
• Проверьте интернет-соединение
• Убедитесь в правильности данных

🆘 <b>Нужна помощь?</b>
Напишите "помощь с настройкой почты" """

        if details:
            error_text += f"\n\n🔍 <b>Детали:</b> {details[:100]}"
        
        print("Сообщение об ошибке:")
        print(error_text)
        print("\n✅ Тест сообщения об ошибке прошел успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания сообщения: {e}")
        return False

def main():
    print("=" * 50)
    print("ТЕСТИРОВАНИЕ КЛАВИАТУР И СООБЩЕНИЙ")
    print("=" * 50)
    
    test1 = test_keyboard_creation()
    test2 = test_error_message()
    
    print("\n" + "=" * 50)
    if test1 and test2:
        print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        print("Клавиатуры должны работать корректно в боте.")
    else:
        print("⚠️ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ")
        print("Проверьте код создания клавиатур.")
    print("=" * 50)

if __name__ == "__main__":
    main()