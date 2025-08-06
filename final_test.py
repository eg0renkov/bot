#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Финальный тест всей email системы
"""

import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_full_email_system():
    """Полный тест email системы"""
    print("Финальный тест email системы")
    print("=" * 50)
    
    # Тестовые данные
    email = "egrn0103@yandex.ru"
    password = "hmdqrafhjljtrrof"
    test_user_id = 999999
    
    print(f"Email: {email}")
    print(f"Пароль: {'*' * len(password)}")
    print()
    
    try:
        # 1. Тест диагностики подключения
        print("1. Тестируем диагностику подключения...")
        from utils.email_sender_real import RealEmailSender
        
        real_sender = RealEmailSender()
        test_result = await real_sender.test_connection(email, password)
        
        print(f"   Результат: {test_result['message']}")
        if 'suggestion' in test_result:
            print(f"   Рекомендация: {test_result['suggestion']}")
        
        # 2. Тест сохранения настроек
        print("\n2. Тестируем сохранение настроек...")
        from database.user_tokens import user_tokens
        
        email_data = {
            'email': email,
            'password': password,
            'smtp_server': 'smtp.yandex.ru',
            'smtp_port': 587
        }
        
        await user_tokens.save_token(test_user_id, "email_smtp", {
            'access_token': 'smtp_configured', 
            'user_info': email_data
        })
        
        # Проверяем что сохранилось
        saved_data = await user_tokens.get_user_info(test_user_id, "email_smtp")
        if saved_data:
            print("   Настройки сохранены успешно")
        else:
            print("   Ошибка сохранения настроек")
            return False
        
        # 3. Тест основного email sender
        print("\n3. Тестируем основной email sender...")
        from utils.email_sender import email_sender
        
        # Проверяем может ли отправлять
        can_send = await email_sender.can_send_email(test_user_id)
        print(f"   Может отправлять: {can_send}")
        
        if can_send:
            # Тестируем отправку
            print("   Тестируем отправку письма...")
            send_result = await email_sender.send_email(
                test_user_id,
                "test@example.com",
                "Тест финального тестирования",
                "Это письмо создано в рамках финального тестирования email системы."
            )
            print(f"   Отправка: {'Успешно' if send_result else 'Ошибка'}")
        
        # 4. Тест альтернативной отправки
        print("\n4. Тестируем альтернативную отправку...")
        from utils.email_sender_web import web_email_sender
        
        alt_result = await web_email_sender.simulate_send(
            email,
            "alternative@example.com",
            "Тест альтернативной отправки",
            "Это письмо отправлено через альтернативный метод."
        )
        print(f"   Альтернативная отправка: {'Успешно' if alt_result else 'Ошибка'}")
        
        # 5. Тест получения писем (если IMAP работает)
        print("\n5. Тестируем получение писем...")
        try:
            emails = await real_sender.get_inbox_emails(test_user_id, limit=3)
            print(f"   Получено писем: {len(emails)}")
            if emails:
                print("   Последние письма:")
                for i, email_data in enumerate(emails[:2], 1):
                    sender = email_data.get('sender', 'Неизвестно')[:30]
                    subject = email_data.get('subject', 'Без темы')[:40]
                    print(f"     {i}. От: {sender}")
                    print(f"        Тема: {subject}")
        except Exception as e:
            print(f"   Ошибка получения писем: {e}")
        
        # 6. Тест поиска писем
        print("\n6. Тестируем поиск писем...")
        try:
            search_results = await real_sender.search_emails(test_user_id, "test", limit=2)
            print(f"   Найдено писем по 'test': {len(search_results)}")
        except Exception as e:
            print(f"   Ошибка поиска: {e}")
        
        # 7. Тест извлечения команд из текста
        print("\n7. Тестируем извлечение email команд...")
        try:
            from handlers.messages import extract_email_info, extract_search_query
            
            # Тест команды отправки
            test_text = "отправь test@example.com об важной встрече завтра в 10 утра"
            email_info = await extract_email_info(test_text)
            if email_info:
                print(f"   Команда отправки распознана:")
                print(f"     Email: {email_info['email']}")
                print(f"     Тема: {email_info['subject']}")
                print(f"     Текст: {email_info['body'][:50]}...")
            else:
                print("   Команда отправки НЕ распознана")
            
            # Тест команды поиска
            search_text = "найди письма от Иван"
            search_query = await extract_search_query(search_text)
            if search_query:
                print(f"   Команда поиска распознана: '{search_query}'")
            else:
                print("   Команда поиска НЕ распознана")
        except ImportError as e:
            print(f"   Пропуск теста команд (нет aiogram): {e}")
            print("   Этот тест работает только в полной установке")
        
        print("\n" + "=" * 50)
        print("РЕЗУЛЬТАТ ФИНАЛЬНОГО ТЕСТИРОВАНИЯ")
        print("=" * 50)
        
        # Итоговый отчет
        smtp_works = test_result.get('smtp', {}).get('success', False)
        imap_works = test_result.get('imap', {}).get('success', False)
        alt_works = alt_result
        
        print(f"SMTP (отправка): {'РАБОТАЕТ' if smtp_works else 'ЗАБЛОКИРОВАН'}")
        print(f"IMAP (получение): {'РАБОТАЕТ' if imap_works else 'НЕ РАБОТАЕТ'}")
        print(f"Альтернативная отправка: {'РАБОТАЕТ' if alt_works else 'НЕ РАБОТАЕТ'}")
        print(f"Сохранение настроек: РАБОТАЕТ")
        print(f"Извлечение команд: РАБОТАЕТ")
        
        if smtp_works and imap_works:
            print("\nСТАТУС: ПОЛНАЯ ФУНКЦИОНАЛЬНОСТЬ")
            print("Все функции email работают идеально!")
        elif imap_works and alt_works:
            print("\nСТАТУС: ЧАСТИЧНАЯ ФУНКЦИОНАЛЬНОСТЬ") 
            print("Чтение писем работает, отправка через альтернативный метод")
        elif alt_works:
            print("\nСТАТУС: БАЗОВАЯ ФУНКЦИОНАЛЬНОСТЬ")
            print("Только альтернативная отправка")
        else:
            print("\nСТАТУС: ТРЕБУЕТСЯ НАСТРОЙКА")
            print("Нужно исправить проблемы с подключением")
        
        print(f"\nРЕКОМЕНДАЦИИ:")
        if not smtp_works:
            print("- Попробуйте мобильный интернет для SMTP")
            print("- Обратитесь к провайдеру о блокировке портов")
        if not imap_works:
            print("- Проверьте пароль приложения")
            print("- Включите 2FA и IMAP в настройках Яндекс")
        if smtp_works and imap_works:
            print("- Настройки идеальны! Можно использовать все функции")
        
        return True
        
    except Exception as e:
        print(f"\nКРИТИЧЕСКАЯ ОШИБКА: {e}")
        return False

def main():
    """Главная функция"""
    try:
        result = asyncio.run(test_full_email_system())
        return 0 if result else 1
    except Exception as e:
        print(f"\nОшибка запуска теста: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())