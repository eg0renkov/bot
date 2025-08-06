#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простой тест подключения без интерактивного ввода
"""

import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.email_sender_real import RealEmailSender

async def test_email_simple():
    """Простой тест с захардкоженными данными"""
    email = "egrn0103@yandex.ru"
    password = "hmdqrafhjljtrrof"
    
    print("Тест подключения к Yandex почте")
    print("=" * 40)
    print(f"Email: {email}")
    print(f"Пароль: {'*' * len(password)}")
    
    try:
        sender = RealEmailSender()
        result = await sender.test_connection(email, password)
        
        print(f"\nРезультат тестирования:")
        print(f"Успех: {'Да' if result['success'] else 'Нет'}")
        print(f"Сообщение: {result['message']}")
        
        # Подробности по протоколам
        if 'smtp' in result:
            smtp_status = "Работает" if result['smtp']['success'] else "Ошибка"
            print(f"SMTP: {smtp_status} - {result['smtp'].get('message', 'Нет сообщения')}")
            if not result['smtp']['success'] and 'error' in result['smtp']:
                print(f"   Детали SMTP: {result['smtp']['error']}")
        
        if 'imap' in result:
            imap_status = "Работает" if result['imap']['success'] else "Ошибка"
            print(f"IMAP: {imap_status} - {result['imap'].get('message', 'Нет сообщения')}")
            if not result['imap']['success'] and 'error' in result['imap']:
                print(f"   Детали IMAP: {result['imap']['error']}")
        
        # Специальный случай: SMTP заблокирован, но IMAP работает
        if result.get('suggestion') == 'smtp_blocked':
            print(f"\nДИАГНОЗ: SMTP заблокирован провайдером")
            print(f"Получение писем: РАБОТАЕТ")
            print(f"Отправка писем: ЗАБЛОКИРОВАНА")
            print(f"\nВозможные решения:")
            print(f"• Используйте мобильный интернет")
            print(f"• Отключите VPN/прокси")
            print(f"• Обратитесь к провайдеру")
            print(f"• Бот может работать в режиме 'только чтение'")
            
            # Тестируем альтернативную отправку
            print(f"\nТестируем альтернативную отправку (сохранение в файл)...")
            from utils.email_sender_web import web_email_sender
            alt_result = await web_email_sender.simulate_send(
                email, "test@example.com", 
                "Тест альтернативной отправки",
                "Это тестовое письмо сохранено в файл, так как SMTP заблокирован."
            )
            if alt_result:
                print("Альтернативная отправка: РАБОТАЕТ")
            else:
                print("Альтернативная отправка: ОШИБКА")
            
            return True  # Частично работает
            
        elif result['success']:
            print(f"\nПолное подключение: УСПЕШНО")
            return True
        else:
            print(f"\nОшибка подключения:")
            print(f"Проблема: {result.get('error', 'Неизвестная ошибка')}")
            
            if '10060' in str(result.get('error', '')) or 'timeout' in str(result.get('error', '')).lower():
                print(f"Рекомендации:")
                print(f"• Проверьте интернет-соединение")
                print(f"• Возможна блокировка провайдером")
                print(f"• Попробуйте мобильный интернет")
                print(f"• Отключите VPN/прокси")
            else:
                print(f"Рекомендации:")
                print(f"• Проверьте правильность пароля приложения")
                print(f"• Убедитесь что 2FA включена")
                print(f"• Проверьте правильность email")
                print(f"• Создайте новый пароль приложения")
            
            return False
            
    except Exception as e:
        print(f"\nТехническая ошибка: {e}")
        return False

def main():
    """Главная функция"""
    try:
        result = asyncio.run(test_email_simple())
        print(f"\n{'='*40}")
        if result:
            print("ИТОГ: Подключение работает (полностью или частично)")
            print("Можно использовать настройки в боте")
        else:
            print("ИТОГ: Подключение не работает")
            print("Нужно исправить настройки или сеть")
        return 0 if result else 1
    except Exception as e:
        print(f"\nКритическая ошибка: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())