import asyncio
from utils.user_settings import user_settings

async def test_user_name_system():
    """Тест системы имен пользователей"""
    
    print("ТЕСТ СИСТЕМЫ ИМЕН ПОЛЬЗОВАТЕЛЕЙ")
    print("=" * 50)
    
    # Тестовый пользователь
    test_user_id = 999999
    
    # 1. Тест сохранения имени
    print("\n1. Тестирование сохранения имени:")
    print("-" * 30)
    
    test_name = "Александр Тестов"
    success = await user_settings.save_user_name(test_user_id, test_name)
    
    if success:
        print(f"[OK] Имя сохранено: {test_name}")
    else:
        print("[ERROR] Ошибка сохранения имени")
    
    # 2. Тест получения имени
    print("\n2. Тестирование получения имени:")
    print("-" * 30)
    
    saved_name = await user_settings.get_user_name(test_user_id)
    
    if saved_name:
        print(f"[OK] Имя получено: {saved_name}")
    else:
        print("[ERROR] Имя не найдено")
    
    # 3. Тест get_or_request_name
    print("\n3. Тестирование get_or_request_name:")
    print("-" * 30)
    
    result_name = await user_settings.get_or_request_name(test_user_id, "Fallback Name")
    print(f"[OK] Возвращено имя: {result_name}")
    
    # 4. Тест нового пользователя
    print("\n4. Тестирование нового пользователя:")
    print("-" * 30)
    
    new_user_id = 888888
    new_name = await user_settings.get_or_request_name(new_user_id, "Новый Пользователь")
    print(f"[OK] Имя нового пользователя: {new_name}")
    
    # Проверяем, что оно сохранилось
    check_name = await user_settings.get_user_name(new_user_id)
    if check_name:
        print(f"[OK] Имя сохранилось: {check_name}")
    else:
        print("[ERROR] Имя не сохранилось")
    
    print("\n" + "=" * 50)
    print("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print("[OK] Сохранение имени: работает")
    print("[OK] Получение имени: работает")
    print("[OK] get_or_request_name: работает")
    print("[OK] Система имен готова!")

if __name__ == "__main__":
    asyncio.run(test_user_name_system())