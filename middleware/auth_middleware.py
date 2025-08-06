from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from utils.auth import auth_manager
from aiogram.utils.keyboard import InlineKeyboardBuilder

class AuthMiddleware(BaseMiddleware):
    """Middleware для проверки авторизации пользователей"""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        
        # Получаем user_id из события
        user_id = None
        if hasattr(event, 'from_user') and event.from_user:
            user_id = event.from_user.id
        
        if not user_id:
            # Не можем определить пользователя - пропускаем
            return await handler(event, data)
        
        # Список команд и callback'ов, которые разрешены без авторизации
        allowed_without_auth = {
            '/start',
            'enter_token',
            'access_help', 
            'cancel_auth'
        }
        
        # Проверяем, нужна ли авторизация для этого события
        needs_auth = True
        
        # Проверяем состояние FSM - если пользователь в процессе авторизации, разрешаем
        if isinstance(event, Message):
            state = data.get('state')
            if state:
                current_state = await state.get_state()
                if current_state and 'waiting_for_token' in current_state:
                    needs_auth = False  # Разрешаем ввод токена
            
            if event.text and any(event.text.startswith(cmd) for cmd in ['/start']):
                needs_auth = False
        elif isinstance(event, CallbackQuery):
            if event.data in allowed_without_auth:
                needs_auth = False
        
        # Если авторизация не нужна или пользователь авторизован - продолжаем
        if not needs_auth or auth_manager.is_user_authorized(user_id):
            return await handler(event, data)
        
        # Пользователь не авторизован - блокируем доступ
        user_name = event.from_user.first_name or "Пользователь"
        
        builder = InlineKeyboardBuilder()
        builder.button(text="🔑 Ввести токен доступа", callback_data="enter_token")
        builder.button(text="❓ Как получить доступ?", callback_data="access_help")
        
        user_greeting = f"{user_name}, " if user_name != "Пользователь" else ""
        unauthorized_message = (
            f"🔒 <b>Доступ ограничен</b>\n\n"
            f"❌ <b>{user_greeting}для использования бота требуется авторизация</b>\n\n"
            f"🤖 <b>Этот AI-помощник защищен токеном доступа</b>\n\n"
            f"💡 <b>Что делать:</b>\n"
            f"• Используйте команду /start для авторизации\n"
            f"• Введите правильный токен доступа\n"
            f"• Обратитесь к администратору за токеном"
        )
        
        if isinstance(event, Message):
            try:
                await event.answer(
                    unauthorized_message,
                    parse_mode="HTML",
                    reply_markup=builder.as_markup()
                )
            except Exception as e:
                print(f"Ошибка отправки сообщения о блокировке: {e}")
        elif isinstance(event, CallbackQuery):
            try:
                await event.message.edit_text(
                    unauthorized_message,
                    parse_mode="HTML",
                    reply_markup=builder.as_markup()
                )
                await event.answer("❌ Доступ запрещен")
            except Exception as e:
                print(f"Ошибка редактирования сообщения о блокировке: {e}")
        
        # Логируем попытку несанкционированного доступа
        print(f"🚫 Блокировка доступа: user_id={user_id}, username=@{event.from_user.username}, name={user_name}")
        
        # НЕ вызываем handler - блокируем выполнение
        return None