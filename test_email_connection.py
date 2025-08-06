#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест подключения к Yandex почте отдельно от бота
"""

import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.email_sender_real import RealEmailSender

async def test_email_connection():
    """Тестируем подключение к почте"""
    print("Тест подключения к Yandex почте")
    print("=" * 40)
    
    # Запрашиваем данные
    email = input("Введите ваш email: ").strip()
    password = input("Введите пароль приложения: ").strip()
    
    if not email or not password:
        print("❌ Email и пароль не могут быть пустыми")
        return False
    
    print(f"\n🔄 Тестируем подключение для {email}...")
    print("⏳ Проверяем SMTP и IMAP соединения...")
    
    try:
        sender = RealEmailSender()
        result = await sender.test_connection(email, password)
        
        print(f"\n📊 Результат тестирования:")
        print(f"✅ Успех: {'Да' if result['success'] else 'Нет'}")
        print(f"📝 Сообщение: {result['message']}")
        
        # Подробности по протоколам
        if 'smtp' in result:
            smtp_status = "✅ Работает" if result['smtp']['success'] else "❌ Ошибка"
            print(f"📤 SMTP: {smtp_status} - {result['smtp'].get('message', 'Нет сообщения')}")
            if not result['smtp']['success'] and 'error' in result['smtp']:
                print(f"   Детали: {result['smtp']['error']}")
        
        if 'imap' in result:
            imap_status = "✅ Работает" if result['imap']['success'] else "❌ Ошибка"
            print(f"📥 IMAP: {imap_status} - {result['imap'].get('message', 'Нет сообщения')}")
            if not result['imap']['success'] and 'error' in result['imap']:
                print(f"   Детали: {result['imap']['error']}")
        
        # Специальный случай: SMTP заблокирован, но IMAP работает
        if result.get('suggestion') == 'smtp_blocked':
            print(f"\n🚫 ДИАГНОЗ: SMTP заблокирован провайдером")
            print(f"📥 Хорошие новости: Получение писем работает!")
            print(f"📤 Плохие новости: Отправка писем заблокирована")
            print(f"\n💡 Возможные решения:")
            print(f"• Используйте мобильный интернет")
            print(f"• Отключите VPN/прокси")
            print(f"• Обратитесь к провайдеру")
            print(f"• Бот может работать в режиме 'только чтение'")
            
            # Предлагаем тест альтернативной отправки
            test_alt = input("\nПротестировать альтернативную отправку (сохранение в файл)? (y/n): ").strip().lower()
            if test_alt == 'y':
                from utils.email_sender_web import web_email_sender
                to_email = input("Введите email получателя для теста: ").strip()
                if to_email:
                    print("💾 Тестируем альтернативную отправку (сохранение в файл)...")
                    alt_result = await web_email_sender.simulate_send(
                        email, to_email, 
                        "Тест альтернативной отправки",
                        "Это тестовое письмо сохранено в файл, так как SMTP заблокирован."
                    )
                    if alt_result:
                        print("✅ Альтернативная отправка работает!")
                    else:
                        print("❌ Ошибка альтернативной отправки")
            
            return False  # Технически не полный успех, но частично работает
            
        elif result['success']:
            print(f"\n🎉 Полное подключение успешно!")
            
            # Тестируем отправку тестового письма
            test_send = input("\nОтправить тестовое письмо? (y/n): ").strip().lower()
            if test_send == 'y':
                to_email = input("Введите email получателя: ").strip()
                if to_email:
                    print("📤 Отправляем тестовое письмо...")
                    
                    # Создаем временную запись пользователя
                    from database.user_tokens import user_tokens
                    test_user_id = 999999  # Тестовый ID
                    
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
                    
                    send_result = await sender.send_email(
                        test_user_id,
                        to_email,
                        "Тестовое письмо от бота",
                        "Это тестовое письмо от Telegram AI бота.\n\nЕсли вы получили это письмо, значит подключение работает корректно!"
                    )
                    
                    if send_result:
                        print("✅ Тестовое письмо отправлено успешно!")
                    else:
                        print("❌ Ошибка отправки тестового письма")
            
            return True
        else:
            print(f"\n❌ Ошибка подключения:")
            print(f"🔧 Проблема: {result.get('error', 'Неизвестная ошибка')}")
            
            print(f"\n💡 Рекомендации:")
            if '10060' in str(result.get('error', '')) or 'timeout' in str(result.get('error', '')).lower():
                print(f"• Проверьте интернет-соединение")
                print(f"• Возможна блокировка провайдером")
                print(f"• Попробуйте мобильный интернет")
                print(f"• Отключите VPN/прокси")
            else:
                print(f"• Проверьте правильность пароля приложения")
                print(f"• Убедитесь что двухфакторная аутентификация включена")
                print(f"• Проверьте правильность email")
                print(f"• Создайте новый пароль приложения")
            
            return False
            
    except Exception as e:
        print(f"\n❌ Техническая ошибка: {e}")
        return False

def main():
    """Главная функция"""
    try:
        result = asyncio.run(test_email_connection())
        print(f"\n{'='*40}")
        if result:
            print("🎉 Тест завершен успешно!")
            print("💡 Теперь вы можете использовать эти данные в боте")
        else:
            print("⚠️ Тест не прошел. Проверьте настройки.")
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ Тест прерван пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()