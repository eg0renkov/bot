from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from utils.auth import auth_manager

router = Router()

class AuthStates(StatesGroup):
    waiting_for_token = State()

@router.message(Command("start"))
async def start_command(message: Message):
    """Обработчик команды /start с проверкой авторизации"""
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "Пользователь"
    
    if auth_manager.is_user_authorized(user_id):
        # Пользователь уже авторизован - показываем главное меню
        from utils.keyboards import keyboards
        welcome_name = f", {user_name}" if user_name != "Пользователь" else ""
        await message.answer(
            f"👋 <b>Добро пожаловать обратно{welcome_name}!</b>\n\n"
            f"🤖 <b>AI Помощник готов к работе!</b>\n\n"
            f"💡 <b>Используйте меню ниже или просто напишите сообщение</b>",
            parse_mode="HTML",
            reply_markup=keyboards.main_menu()
        )
    else:
        # Пользователь не авторизован - требуем токен
        builder = InlineKeyboardBuilder()
        builder.button(text="🔑 Ввести токен доступа", callback_data="enter_token")
        builder.button(text="❓ Как получить доступ?", callback_data="access_help")
        
        await message.answer(
            f"🔒 <b>Доступ ограничен</b>\n\n"
            f"👋 Привет, {user_name}!\n\n"
            f"🤖 Для использования этого AI-помощника требуется <b>токен доступа</b>.\n\n"
            f"🔑 <b>Если у вас есть токен</b> - нажмите кнопку ниже\n"
            f"❓ <b>Если нет токена</b> - обратитесь к администратору",
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )

@router.callback_query(F.data == "enter_token")
async def enter_token_callback(callback: CallbackQuery, state: FSMContext):
    """Запрос ввода токена"""
    user_id = callback.from_user.id
    
    if auth_manager.is_user_authorized(user_id):
        await callback.message.edit_text(
            "✅ <b>Вы уже авторизованы!</b>\n\n"
            "Используйте команду /start для входа в меню.",
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    # Создаем кнопку отмены
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="cancel_auth")
    
    await callback.message.edit_text(
        f"🔑 <b>Введите токен доступа</b>\n\n"
        f"✏️ <b>Отправьте токен в следующем сообщении</b>\n\n"
        f"⚠️ <b>Важно:</b>\n"
        f"• Токен чувствителен к регистру\n"
        f"• Убедитесь в правильности ввода\n"
        f"• После ввода токен будет скрыт в целях безопасности\n\n"
        f"💡 <b>Формат:</b> Просто отправьте токен как обычное сообщение",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    
    await state.set_state(AuthStates.waiting_for_token)
    await callback.answer("Жду ваш токен...")

@router.callback_query(F.data == "access_help")
async def access_help_callback(callback: CallbackQuery):
    """Помощь по получению доступа"""
    stats = auth_manager.get_auth_stats()
    
    await callback.message.edit_text(
        f"❓ <b>Как получить доступ к боту</b>\n\n"
        f"🔐 <b>Этот бот использует токен-авторизацию для безопасности</b>\n\n"
        f"📞 <b>Для получения токена доступа:</b>\n"
        f"• Обратитесь к администратору бота\n"
        f"• Объясните цель использования\n"
        f"• Получите персональный токен доступа\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"• Авторизованных пользователей: {stats['total_authorized']}\n"
        f"• Формат токена: {stats['token_hint']}\n\n"
        f"🔒 <b>Безопасность:</b>\n"
        f"• Не передавайте токен третьим лицам\n"
        f"• Токен привязывается к вашему аккаунту\n"
        f"• В случае компрометации - сообщите администратору",
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "cancel_auth")
async def cancel_auth_callback(callback: CallbackQuery, state: FSMContext):
    """Отмена авторизации"""
    await state.clear()
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔑 Попробовать снова", callback_data="enter_token")
    builder.button(text="❓ Помощь", callback_data="access_help")
    
    await callback.message.edit_text(
        f"❌ <b>Авторизация отменена</b>\n\n"
        f"🔒 Для доступа к боту необходим токен\n\n"
        f"💡 Попробуйте снова или обратитесь к администратору",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await callback.answer("Авторизация отменена")

@router.message(AuthStates.waiting_for_token)
async def process_token(message: Message, state: FSMContext):
    """Обработка введенного токена"""
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "Пользователь"
    token = message.text.strip()
    
    # Удаляем сообщение пользователя с токеном в целях безопасности
    try:
        await message.delete()
    except:
        pass  # Игнорируем ошибку если нет прав на удаление
    
    # Отладочная информация
    print(f"DEBUG: Получен токен от пользователя {user_id}: '{token}' (длина: {len(token)})")
    
    # Проверяем токен
    token_check = auth_manager.check_token_format(token)
    print(f"DEBUG: Результат проверки токена: {token_check}")
    
    if token_check['valid']:
        # Токен правильный - авторизуем пользователя
        success = auth_manager.authorize_user(user_id, token)
        
        if success:
            await state.clear()
            
            from utils.keyboards import keyboards
            await message.answer(
                f"✅ <b>Авторизация успешна!</b>\n\n"
                f"🎉 <b>Добро пожаловать{', ' + user_name if user_name != 'Пользователь' else ''}!</b>\n\n"
                f"🤖 <b>AI Помощник теперь доступен для использования!</b>\n\n"
                f"💡 <b>Что я умею:</b>\n"
                f"• 💬 Отвечать на вопросы с помощью AI\n"
                f"• 📧 Отправлять и управлять письмами\n"
                f"• 📅 Работать с календарем\n"
                f"• 👥 Управлять контактами\n"
                f"• ⏰ Создавать напоминания\n"
                f"• 🧠 Запоминать наши разговоры\n\n"
                f"🚀 <b>Используйте меню ниже или просто напишите сообщение!</b>",
                parse_mode="HTML",
                reply_markup=keyboards.main_menu()
            )
            
            # Логируем успешную авторизацию
            print(f"✅ Успешная авторизация: user_id={user_id}, username=@{message.from_user.username}, name={user_name}")
        else:
            await message.answer(
                f"❌ <b>Ошибка авторизации</b>\n\n"
                f"Произошла внутренняя ошибка. Попробуйте позже.",
                parse_mode="HTML"
            )
    else:
        # Токен неверный
        builder = InlineKeyboardBuilder()
        builder.button(text="🔑 Попробовать снова", callback_data="enter_token")
        builder.button(text="❓ Помощь", callback_data="access_help")
        builder.button(text="❌ Отмена", callback_data="cancel_auth")
        
        await message.answer(
            f"❌ <b>Неверный токен доступа</b>\n\n"
            f"🔍 <b>Проблема:</b> {token_check['hint']}\n\n"
            f"💡 <b>Проверьте:</b>\n"
            f"• Правильность ввода токена\n"
            f"• Регистр символов\n"
            f"• Отсутствие лишних пробелов\n\n"
            f"🔒 <b>Ваше сообщение с токеном было удалено для безопасности</b>",
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )
        
        # Логируем неудачную попытку
        print(f"❌ Неудачная авторизация: user_id={user_id}, username=@{message.from_user.username}, hint={token_check['hint']}")

# Команда для администраторов (можно расширить)
@router.message(Command("auth_stats"))
async def auth_stats_command(message: Message):
    """Статистика авторизации (для администраторов)"""
    user_id = message.from_user.id
    
    # Простая проверка админа (можно расширить)
    if not auth_manager.is_user_authorized(user_id):
        await message.answer("❌ Команда доступна только авторизованным пользователям")
        return
    
    stats = auth_manager.get_auth_stats()
    
    await message.answer(
        f"📊 <b>Статистика авторизации</b>\n\n"
        f"👥 <b>Всего авторизованных:</b> {stats['total_authorized']}\n"
        f"🔑 <b>Токен (подсказка):</b> {stats['token_hint']}\n\n"
        f"📝 <b>ID авторизованных пользователей:</b>\n" +
        '\n'.join([f"• {uid}" for uid in stats['authorized_users'][:10]]) +
        (f"\n... и еще {len(stats['authorized_users']) - 10}" if len(stats['authorized_users']) > 10 else ""),
        parse_mode="HTML"
    )

@router.message(Command("reset_auth"))
async def reset_auth_command(message: Message):
    """Сброс авторизации для тестирования"""
    user_id = message.from_user.id
    
    # Удаляем пользователя из списка авторизованных
    if auth_manager.revoke_user_access(user_id):
        await message.answer(
            f"🔄 <b>Авторизация сброшена</b>\n\n"
            f"Теперь вы можете заново пройти авторизацию с помощью /start"
        )
    else:
        await message.answer("❌ Вы не были авторизованы")

@router.message(Command("debug_token"))
async def debug_token_command(message: Message):
    """Отладочная команда для проверки токена"""
    if len(message.text.split()) < 2:
        await message.answer(
            "🔍 <b>Отладка токена</b>\n\n"
            f"Использование: <code>/debug_token ВАШ_ТОКЕН</code>\n\n"
            f"Эта команда поможет понять, почему токен не проходит проверку.",
            parse_mode="HTML"
        )
        return
    
    token = ' '.join(message.text.split()[1:])  # Всё после команды
    check_result = auth_manager.check_token_format(token)
    
    await message.answer(
        f"🔍 <b>Результат проверки токена</b>\n\n"
        f"✅ <b>Валидный:</b> {'Да' if check_result['valid'] else 'Нет'}\n"
        f"💡 <b>Подсказка:</b> {check_result['hint']}\n\n"
        f"📝 <b>Детали:</b>\n"
        f"• Длина введенного: {len(token)}\n"
        f"• Длина ожидаемого: {len(auth_manager.access_token)}\n"
        f"• Начинается правильно: {token.strip().startswith(auth_manager.access_token[:4])}\n"
        f"• Правильный токен: <code>SECURE_BOT_ACCESS_2024</code>",
        parse_mode="HTML"
    )