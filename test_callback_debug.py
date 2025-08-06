"""Тест callback обработчика для диагностики"""

import asyncio
from unittest.mock import Mock, AsyncMock
from aiogram.types import CallbackQuery, User, Message, Chat
from handlers.menu_handlers import settings_email_search_callback

async def test_callback_handler():
    """Тест обработчика settings_email_search"""
    
    print("ТЕСТ CALLBACK ОБРАБОТЧИКА")
    print("=" * 40)
    
    # Создаем мок объекты
    user = User(id=123456789, is_bot=False, first_name="Test", username="testuser")
    chat = Chat(id=123456789, type="private")
    message = Mock(spec=Message)
    message.edit_text = AsyncMock()
    
    # Создаем мок callback
    callback = Mock(spec=CallbackQuery)
    callback.from_user = user
    callback.data = "settings_email_search"
    callback.message = message
    callback.answer = AsyncMock()
    
    print(f"Тестируем callback: {callback.data}")
    print(f"Пользователь: {callback.from_user.id}")
    
    try:
        # Вызываем обработчик
        print("Вызываем обработчик...")
        await settings_email_search_callback(callback)
        
        print("[OK] Обработчик выполнился успешно!")
        
        # Проверяем, что методы были вызваны
        if callback.answer.called:
            print("[OK] callback.answer() был вызван")
        else:
            print("[WARNING] callback.answer() не был вызван")
            
        if message.edit_text.called:
            print("[OK] message.edit_text() был вызван")
            call_args = message.edit_text.call_args
            if call_args:
                text = call_args[0][0] if call_args[0] else "No text"
                print(f"[INFO] Текст сообщения: {text[:100]}...")
        else:
            print("[WARNING] message.edit_text() не был вызван")
            
    except Exception as e:
        print(f"[ERROR] Ошибка в обработчике: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 40)
    print("РЕЗУЛЬТАТ: Обработчик работает корректно!")
    return True

if __name__ == "__main__":
    asyncio.run(test_callback_handler())