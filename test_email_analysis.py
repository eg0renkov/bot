import asyncio
from utils.email_analyzer import email_analyzer

async def test_email_analysis():
    """Тестирование анализа писем"""
    
    print("ТЕСТ АНАЛИЗА ПИСЕМ С AI")
    print("=" * 60)
    
    # Тестовые данные писем
    test_emails = [
        {
            'sender': 'no-reply@bank.com',
            'subject': 'СРОЧНО: Подозрительная активность на счете',
            'body': 'Обнаружена подозрительная активность на вашем банковском счете. Немедленно подтвердите операции.',
            'date': '2025-08-05 15:30:00',
        },
        {
            'sender': 'boss@company.com',
            'subject': 'Важная встреча завтра',
            'body': 'Не забудьте о важной встрече с клиентами завтра в 14:00. Подготовьте презентацию.',
            'date': '2025-08-05 14:15:00',
        },
        {
            'sender': 'promo@shop.ru',
            'subject': 'Скидка 50% на все товары!',
            'body': 'Успейте купить со скидкой 50%! Акция действует только сегодня. Бесплатная доставка.',
            'date': '2025-08-05 12:00:00',
        },
        {
            'sender': 'hr@company.com',
            'subject': 'Документы по отпуску',
            'body': 'Пожалуйста, заполните заявление на отпуск и отправьте до конца недели.',
            'date': '2025-08-05 10:30:00',
        },
        {
            'sender': 'newsletter@techblog.com',
            'subject': 'Новости технологий: AI в 2025',
            'body': 'Читайте в нашем еженедельном дайджесте: последние новости AI, машинного обучения и разработки.',
            'date': '2025-08-05 09:00:00',
        }
    ]
    
    print(f"\n[EMAIL] Тестируем анализ {len(test_emails)} писем:")
    print("-" * 40)
    
    for i, email in enumerate(test_emails, 1):
        print(f"{i}. От: {email['sender']}")
        print(f"   Тема: {email['subject']}")
        print()
    
    print("\n[AI] Запускаем AI анализ...")
    print("-" * 40)
    
    try:
        # Тест основного анализа
        print("1. Основной анализ с AI:")
        analysis = await email_analyzer.analyze_emails_summary(test_emails, "Алекс Лесли")
        print(analysis)
        print()
        
        # Тест дополнительных инсайтов
        print("2. Дополнительные инсайты:")
        insights = await email_analyzer.get_email_insights(test_emails)
        
        for key, value in insights.items():
            print(f"   {key}: {value}")
        print()
        
        # Тест с пустым списком
        print("3. Тест с пустым списком:")
        empty_analysis = await email_analyzer.analyze_emails_summary([], "Тестовый пользователь")
        print(f"   Результат: {empty_analysis}")
        print()
        
        # Тест инсайтов с пустым списком
        empty_insights = await email_analyzer.get_email_insights([])
        print("   Инсайты для пустого списка:", empty_insights)
        print()
        
        print("[OK] Все тесты пройдены успешно!")
        
    except Exception as e:
        print(f"[ERROR] Ошибка в тестах: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_email_analysis())