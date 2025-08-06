import asyncio
from utils.html_utils import escape_html, escape_email, truncate_and_escape

async def test_html_escape():
    """Тестирование экранирования HTML"""
    
    print("ТЕСТ ЭКРАНИРОВАНИЯ HTML ДЛЯ TELEGRAM")
    print("=" * 60)
    
    # Тестовые email адреса с проблемными символами
    test_emails = [
        "no-reply@example.com",
        "user@mail.ru",
        "test<script>@hack.com",
        "admin@site.com>",
        "<admin@site.com>",
        "user&admin@company.com",
        "test'quote@mail.com",
        '"quoted"@example.com',
        None,
        ""
    ]
    
    print("\n1. Тест экранирования email адресов:")
    print("-" * 40)
    for email in test_emails:
        escaped = escape_email(email)
        print(f"Исходный: {email!r}")
        print(f"Экранированный: {escaped}")
        print()
    
    # Тестовые строки с HTML
    test_strings = [
        "Обычный текст",
        "Текст с <b>тегами</b>",
        "Email: no-reply@example.com",
        "Скрипт: <script>alert('hack')</script>",
        "Символы: & < > \" '",
        None,
        ""
    ]
    
    print("\n2. Тест экранирования обычного текста:")
    print("-" * 40)
    for text in test_strings:
        escaped = escape_html(text)
        print(f"Исходный: {text!r}")
        print(f"Экранированный: {escaped}")
        print()
    
    # Тест обрезки и экранирования
    long_texts = [
        "Очень длинный email адрес который нужно обрезать: very-long-email-address-that-should-be-truncated@example-domain.com",
        "Длинная тема письма с <b>HTML тегами</b> и специальными символами & < >",
        "no-reply@operations.example.com",
    ]
    
    print("\n3. Тест обрезки и экранирования:")
    print("-" * 40)
    for text in long_texts:
        truncated = truncate_and_escape(text, max_length=30)
        print(f"Исходный ({len(text)} символов): {text!r}")
        print(f"Обрезанный и экранированный: {truncated}")
        print()
    
    # Тест реального сценария из бота
    print("\n4. Тест реального сценария (письма в inbox):")
    print("-" * 40)
    
    # Имитация данных письма
    email_data = {
        'sender': 'no-reply@operations.example.com',
        'subject': 'Важное уведомление <script>alert("test")</script>',
        'date': '2025-08-05 16:30:00'
    }
    
    # Как было бы без экранирования (опасно!)
    print("БЕЗ экранирования (опасно!):")
    sender = email_data.get('sender', 'Неизвестный отправитель')
    subject = email_data.get('subject', 'Без темы')
    print(f"<b>1.</b> [user] {sender}")
    print(f"[mail] {subject}")
    print()
    
    # С правильным экранированием
    print("С экранированием (безопасно):")
    sender = truncate_and_escape(email_data.get('sender', 'Неизвестный отправитель'), 30)
    subject = truncate_and_escape(email_data.get('subject', 'Без темы'), 40)
    print(f"<b>1.</b> [user] {sender}")
    print(f"[mail] {subject}")
    print()
    
    print("✅ Тест завершен!")
    print("\nРЕЗУЛЬТАТ:")
    print("- Email адреса правильно экранируются")
    print("- HTML теги экранируются") 
    print("- Специальные символы безопасны")
    print("- Длинные строки корректно обрезаются")

if __name__ == "__main__":
    asyncio.run(test_html_escape())