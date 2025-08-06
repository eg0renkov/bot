#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестирование основных функций бота
"""

import asyncio
import sys
import os
sys.path.append('.')

# Тест 1: Проверка извлечения email команд
async def test_email_extraction():
    print("=== ТЕСТ 1: Извлечение email команд ===")
    
    from handlers.messages import extract_email_info
    
    test_cases = [
        "напиши письмо alexlesley01@yandex.ru о подорожании сыра",
        "отправь письмо test@example.com об важной встрече",
        "письмо manager@company.ru о проекте"
    ]
    
    for test_text in test_cases:
        try:
            result = await extract_email_info(test_text, "Тестовый Пользователь")
            print(f"✅ '{test_text}' -> {result}")
        except Exception as e:
            print(f"❌ '{test_text}' -> Ошибка: {e}")

# Тест 2: Проверка создания временных писем
def test_temp_emails():
    print("\n=== ТЕСТ 2: Создание временных писем ===")
    
    from utils.temp_emails import temp_emails
    
    try:
        email_id = temp_emails.create_email(
            user_id=123456,
            to_email="test@example.com", 
            subject="Тестовое письмо",
            body="Это тестовое письмо для проверки функционала"
        )
        print(f"✅ Письмо создано с ID: {email_id}")
        
        # Проверяем получение письма
        email_data = temp_emails.get_email(email_id)
        if email_data:
            print(f"✅ Письмо получено: {email_data['subject']}")
        else:
            print("❌ Не удалось получить созданное письмо")
            
        # Удаляем тестовое письмо
        temp_emails.delete_email(email_id)
        print("✅ Тестовое письмо удалено")
        
    except Exception as e:
        print(f"❌ Ошибка создания временного письма: {e}")

# Тест 3: Проверка подключения email
async def test_email_connection():
    print("\n=== ТЕСТ 3: Проверка подключения email ===")
    
    from utils.email_sender import email_sender
    
    try:
        # Тестируем для пользователя из токенов
        user_id = 1224080736
        can_send = await email_sender.can_send_email(user_id)
        print(f"✅ Пользователь {user_id} может отправлять email: {can_send}")
        
        # Тестируем для несуществующего пользователя
        user_id = 999999999
        can_send = await email_sender.can_send_email(user_id)
        print(f"✅ Пользователь {user_id} может отправлять email: {can_send}")
        
    except Exception as e:
        print(f"❌ Ошибка проверки подключения email: {e}")

# Тест 4: Проверка календарных команд
async def test_calendar_extraction():
    print("\n=== ТЕСТ 4: Извлечение календарных команд ===")
    
    from handlers.messages import extract_calendar_command
    
    test_cases = [
        "добавь что сегодня в 23 встреча с артемом",
        "встреча завтра в 15:00",
        "создай событие обед с партнерами"
    ]
    
    for test_text in test_cases:
        try:
            result = await extract_calendar_command(test_text)
            print(f"✅ '{test_text}' -> {result}")
        except Exception as e:
            print(f"❌ '{test_text}' -> Ошибка: {e}")

# Тест 5: Проверка клавиатур
def test_keyboards():
    print("\n=== ТЕСТ 5: Проверка клавиатур ===")
    
    from utils.keyboards import keyboards
    
    try:
        # Тестируем главное меню
        main_menu = keyboards.main_menu()
        print(f"✅ Главное меню создано: {type(main_menu)}")
        
        # Тестируем email подтверждение
        email_confirm = keyboards.email_confirm_menu("test123")
        print(f"✅ Email подтверждение создано: {type(email_confirm)}")
        
        # Тестируем полное меню
        full_menu = keyboards.full_menu()
        print(f"✅ Полное меню создано: {type(full_menu)}")
        
    except Exception as e:
        print(f"❌ Ошибка создания клавиатур: {e}")

# Основная функция тестирования
async def run_all_tests():
    print("🧪 ЗАПУСК КОМПЛЕКСНОГО ТЕСТИРОВАНИЯ БОТА")
    print("=" * 50)
    
    # Запускаем все тесты
    await test_email_extraction()
    test_temp_emails()
    await test_email_connection()
    await test_calendar_extraction()
    test_keyboards()
    
    print("\n" + "=" * 50)
    print("🏁 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")

if __name__ == "__main__":
    asyncio.run(run_all_tests())