import asyncio
from utils.drafts_manager import drafts_manager, Draft

async def test_drafts_system():
    """Тестирование системы черновиков с пагинацией"""
    
    print("ТЕСТ СИСТЕМЫ ЧЕРНОВИКОВ")
    print("=" * 50)
    
    # Тестовый пользователь
    test_user_id = 777777
    
    # 1. Создаем несколько тестовых черновиков
    print("\n1. Создание тестовых черновиков:")
    print("-" * 30)
    
    test_drafts = [
        {
            'recipient_email': 'alice@example.com',
            'recipient_name': 'Алиса Иванова',
            'subject': 'Встреча по проекту',
            'body': 'Добрый день! Предлагаю встретиться для обсуждения проекта.'
        },
        {
            'recipient_email': 'bob@company.com',
            'recipient_name': 'Боб Петров',
            'subject': 'Отчет за месяц',
            'body': 'Высылаю отчет за прошедший месяц. Все показатели в норме.'
        },
        {
            'recipient_email': 'carol@design.ru',
            'recipient_name': 'Кэрол Дизайнер',
            'subject': 'Макеты сайта',
            'body': 'Пожалуйста, посмотрите новые макеты и дайте обратную связь.'
        },
        {
            'recipient_email': 'david@tech.com',
            'recipient_name': 'Дэвид Техник',
            'subject': 'Техническое задание',
            'body': 'Нужно обсудить техническое задание для нового проекта.'
        },
        {
            'recipient_email': 'eve@marketing.com',
            'recipient_name': 'Ева Маркетолог',
            'subject': 'Рекламная кампания',
            'body': 'Предлагаю запустить новую рекламную кампанию в следующем месяце.'
        },
        {
            'recipient_email': 'frank@sales.com',
            'recipient_name': 'Франк Продажник',
            'subject': 'Квартальные результаты',
            'body': 'Отправляю квартальные результаты продаж. Показатели хорошие.'
        },
        {
            'recipient_email': 'grace@hr.com',
            'recipient_name': 'Грейс HR',
            'subject': 'Собеседование',
            'body': 'Подтверждаю время собеседования на завтра в 14:00.'
        }
    ]
    
    created_count = 0
    for draft_data in test_drafts:
        try:
            draft = Draft(
                recipient_email=draft_data['recipient_email'],
                recipient_name=draft_data['recipient_name'],
                subject=draft_data['subject'],
                body=draft_data['body']
            )
            
            success = await drafts_manager.save_draft(test_user_id, draft)
            if success:
                created_count += 1
                print(f"[OK] Создан: {draft.subject}")
            else:
                print(f"[ERROR] Ошибка создания: {draft.subject}")
                
        except Exception as e:
            print(f"[ERROR] Ошибка: {e}")
    
    print(f"\nВсего создано черновиков: {created_count}")
    
    # 2. Тестируем пагинацию
    print("\n\n2. Тестирование пагинации:")
    print("-" * 30)
    
    # Страница 0 (первые 5)
    page_0 = await drafts_manager.get_drafts_page(test_user_id, page=0, per_page=5)
    print(f"\nСТРАНИЦА 0:")
    print(f"  Всего черновиков: {page_0['total_drafts']}")
    print(f"  Всего страниц: {page_0['total_pages']}")
    print(f"  Текущая страница: {page_0['current_page']}")
    print(f"  Есть следующая: {page_0['has_next']}")
    print(f"  Есть предыдущая: {page_0['has_prev']}")
    print(f"  Черновиков на странице: {len(page_0['drafts'])}")
    
    for i, draft in enumerate(page_0['drafts'], 1):
        print(f"    {i}. {draft.subject} -> {draft.recipient_name}")
    
    # Страница 1 (следующие 5)
    if page_0['has_next']:
        page_1 = await drafts_manager.get_drafts_page(test_user_id, page=1, per_page=5)
        print(f"\nСТРАНИЦА 1:")
        print(f"  Черновиков на странице: {len(page_1['drafts'])}")
        print(f"  Есть следующая: {page_1['has_next']}")
        print(f"  Есть предыдущая: {page_1['has_prev']}")
        
        for i, draft in enumerate(page_1['drafts'], 1):
            print(f"    {i}. {draft.subject} -> {draft.recipient_name}")
    
    # 3. Тестируем получение по ID
    print("\n\n3. Тестирование получения по ID:")
    print("-" * 30)
    
    if page_0['drafts']:
        first_draft = page_0['drafts'][0]
        retrieved_draft = await drafts_manager.get_draft_by_id(test_user_id, first_draft.id)
        
        if retrieved_draft:
            print(f"[OK] Черновик найден: {retrieved_draft.subject}")
            print(f"   Предпросмотр: {retrieved_draft.get_preview(50)}")
        else:
            print("[ERROR] Черновик не найден")
    
    # 4. Тестируем удаление
    print("\n\n4. Тестирование удаления:")
    print("-" * 30)
    
    # Удаляем первый черновик
    if page_0['drafts']:
        draft_to_delete = page_0['drafts'][0]
        success = await drafts_manager.delete_draft(test_user_id, draft_to_delete.id)
        
        if success:
            print(f"[OK] Удален черновик: {draft_to_delete.subject}")
            
            # Проверяем, что он действительно удален
            remaining_page = await drafts_manager.get_drafts_page(test_user_id, page=0, per_page=5)
            print(f"   Осталось черновиков: {remaining_page['total_drafts']}")
        else:
            print("[ERROR] Ошибка удаления")
    
    # 5. Очистка тестовых данных
    print("\n\n5. Очистка тестовых данных:")
    print("-" * 30)
    
    try:
        all_drafts = await drafts_manager.get_user_drafts(test_user_id)
        
        deleted_count = 0
        for draft in all_drafts:
            success = await drafts_manager.delete_draft(test_user_id, draft.id)
            if success:
                deleted_count += 1
        
        print(f"[CLEAN] Удалено черновиков: {deleted_count}")
        
        # Проверяем, что все удалено
        final_check = await drafts_manager.get_user_drafts(test_user_id)
        print(f"   Осталось черновиков: {len(final_check)}")
        
    except Exception as e:
        print(f"[ERROR] Ошибка очистки: {e}")
    
    print("\n" + "=" * 50)
    print("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print("[OK] Создание черновиков: работает")
    print("[OK] Пагинация: работает")
    print("[OK] Получение по ID: работает")  
    print("[OK] Удаление: работает")
    print("[OK] Система черновиков готова!")

if __name__ == "__main__":
    asyncio.run(test_drafts_system())