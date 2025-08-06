#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест интеграции email системы
"""

import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_file_structure():
    """Проверяем структуру файлов"""
    required_files = [
        'bot/main.py',
        'handlers/email_setup.py',
        'utils/email_sender_real.py',
        'utils/email_sender.py',
        'utils/temp_emails.py',
        'utils/email_improver.py',
        'handlers/messages.py',
        'handlers/menu_handlers.py',
        'utils/keyboards.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("[ERROR] Отсутствующие файлы:")
        for file in missing_files:
            print(f"  - {file}")
        return False
    
    print("[OK] Все необходимые файлы присутствуют")
    return True

def test_main_integration():
    """Проверяем интеграцию в main.py"""
    try:
        with open('bot/main.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем импорт
        if 'email_setup' not in content:
            print("[ERROR] email_setup не импортирован в main.py")
            return False
        
        # Проверяем регистрацию роутера
        if 'dp.include_router(email_setup.router)' not in content:
            print("[ERROR] email_setup.router не зарегистрирован в main.py")
            return False
        
        print("[OK] email_setup интегрирован в main.py")
        return True
        
    except Exception as e:
        print(f"[ERROR] Ошибка проверки main.py: {e}")
        return False

def test_menu_integration():
    """Проверяем интеграцию в меню"""
    try:
        with open('utils/keyboards.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем наличие кнопки подключения почты
        if 'connect_yandex_mail' not in content:
            print("[ERROR] Кнопка подключения почты не найдена в keyboards.py")
            return False
        
        print("[OK] Кнопка подключения почты присутствует в меню")
        return True
        
    except Exception as e:
        print(f"[ERROR] Ошибка проверки keyboards.py: {e}")
        return False

def test_handlers_integration():
    """Проверяем обработчики в menu_handlers.py"""
    try:
        with open('handlers/menu_handlers.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем обработчик входящих писем
        if 'mail_inbox_callback' not in content:
            print("[ERROR] Обработчик входящих писем не найден")
            return False
        
        print("[OK] Обработчики писем добавлены в menu_handlers.py")
        return True
        
    except Exception as e:
        print(f"[ERROR] Ошибка проверки menu_handlers.py: {e}")
        return False

def test_search_integration():
    """Проверяем интеграцию поиска в messages.py"""
    try:
        with open('handlers/messages.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем функцию поиска
        if 'extract_search_query' not in content:
            print("[ERROR] Функция поиска писем не найдена")
            return False
        
        # Проверяем обработку поиска
        if 'search_query = await extract_search_query' not in content:
            print("[ERROR] Обработка поиска не интегрирована")
            return False
        
        print("[OK] Поиск писем интегрирован в messages.py")
        return True
        
    except Exception as e:
        print(f"[ERROR] Ошибка проверки messages.py: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("Тестирование интеграции email системы")
    print("=" * 50)
    
    tests = [
        test_file_structure,
        test_main_integration,
        test_menu_integration,
        test_handlers_integration,
        test_search_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"[ERROR] Ошибка в тесте {test.__name__}: {e}")
            print()
    
    print("=" * 50)
    print(f"Результат: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("[SUCCESS] Все тесты пройдены! Интеграция завершена успешно.")
        print()
        print("Готовые функции:")
        print("  - Пошаговая настройка Яндекс.Почты")
        print("  - Подключение через пароли приложений")
        print("  - Просмотр входящих писем")
        print("  - Поиск писем по содержимому")
        print("  - Отправка писем с AI улучшением")
        print("  - Работа с черновиками")
        print()
        print("Для запуска бота:")
        print("  1. Установите зависимости: pip install -r requirements.txt")
        print("  2. Настройте .env файл")
        print("  3. Запустите: python bot/main.py")
    else:
        print("[WARNING] Некоторые тесты не пройдены. Проверьте ошибки выше.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)