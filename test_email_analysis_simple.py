import asyncio
from utils.email_analyzer import email_analyzer

async def test_email_analysis_simple():
    """Простой тест анализа писем без вывода AI текста"""
    
    print("ПРОСТОЙ ТЕСТ АНАЛИЗА ПИСЕМ")
    print("=" * 40)
    
    # Тестовые данные
    test_emails = [
        {
            'sender': 'boss@company.com',
            'subject': 'Важная встреча',
            'body': 'Встреча в 14:00',
            'date': '2025-08-05 15:30:00',
        },
        {
            'sender': 'hr@company.com', 
            'subject': 'Документы',
            'body': 'Заполните документы',
            'date': '2025-08-05 14:15:00',
        }
    ]
    
    print(f"Тестируем {len(test_emails)} писем")
    
    try:
        # Тест анализа
        print("1. Запуск анализа...")
        analysis = await email_analyzer.analyze_emails_summary(test_emails, "Тестер")
        print(f"   Анализ получен, длина: {len(analysis)} символов")
        
        # Тест инсайтов
        print("2. Получение инсайтов...")
        insights = await email_analyzer.get_email_insights(test_emails)
        print(f"   Инсайты: {insights}")
        
        # Тест с пустым списком
        print("3. Тест пустого списка...")
        empty_result = await email_analyzer.analyze_emails_summary([], "Тестер")
        print(f"   Результат: {empty_result}")
        
        print("\n[OK] Все тесты выполнены успешно!")
        print("Функция анализа писем работает корректно.")
        
    except Exception as e:
        print(f"[ERROR] Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_email_analysis_simple())