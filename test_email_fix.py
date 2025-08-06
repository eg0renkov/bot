"""
Тестирование исправлений обработки email команд
"""
import asyncio
import sys
import os

# Добавляем корневую папку в sys.path для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from handlers.email_fix import extract_email_info_fixed, format_email_subject_safe

async def test_email_extraction():
    """Тестирование извлечения данных письма"""
    print("ТЕСТИРОВАНИЕ ИЗВЛЕЧЕНИЯ EMAIL ДАННЫХ")
    print("=" * 50)
    
    test_cases = [
        # Проблемный случай из скриншота
        "отправь письмо леониду egr0103@yandex.ru о потеплении",
        
        # Другие тест-кейсы
        "отправь письмо test@example.com об важной встрече",
        "напиши письмо manager@company.com о новом проекте",
        "отправь user@domain.com - о завершении работ",
        "письмо admin@site.ru об ошибке в системе",
        
        # Пограничные случаи
        "отправь test@test.com о",
        "отправь @yandex.ru о чем-то",
        "отправь письмо об чем-то важном",
        "",
        "просто текст без email"
    ]
    
    for i, test_text in enumerate(test_cases, 1):
        print(f"\nТЕСТ {i}: '{test_text}'")
        print("-" * 30)
        
        try:
            result = await extract_email_info_fixed(test_text, "Тестовый Пользователь")
            
            if result:
                print(f"УСПЕХ!")
                print(f"   Email: {result['email']}")
                print(f"   Тема: {result['subject']}")
                print(f"   Тело (длина): {len(result['body'])}")
                print(f"   Тело (превью): {result['body'][:100]}...")
            else:
                print(f"НЕ РАСПОЗНАНО")
        
        except Exception as e:
            print(f"ОШИБКА: {e}")

async def test_subject_formatting():
    """Тестирование форматирования тем"""
    print("\n\nТЕСТИРОВАНИЕ ФОРМАТИРОВАНИЯ ТЕМ")
    print("=" * 50)
    
    test_subjects = [
        "потеплении",
        "об важной встрече", 
        "о новом проекте",
        "успешной сдачи контракта",
        "касательно встречи",
        "про обновление системы",
        "",
        "а",
        "очень длинная тема письма которая содержит много слов и должна быть обработана корректно"
    ]
    
    for subject in test_subjects:
        print(f"\nИСХОДНАЯ ТЕМА: '{subject}'")
        try:
            # Без AI - просто используем базовую очистку
            formatted = await format_email_subject_safe(subject)
            print(f"ФОРМАТИРОВАННАЯ: '{formatted}'")
        except Exception as e:
            print(f"ОШИБКА: {e}")

async def main():
    """Главная функция тестирования"""
    print("ЗАПУСК ТЕСТОВ ИСПРАВЛЕНИЙ EMAIL")
    print("=" * 60)
    
    await test_email_extraction()
    await test_subject_formatting()
    
    print("\n" + "=" * 60)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")

if __name__ == "__main__":
    asyncio.run(main())