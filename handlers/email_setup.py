from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from utils.keyboards import keyboards
from database.user_tokens import user_tokens
from utils.email_sender import email_sender
from utils.html_utils import escape_html, escape_email
import re

router = Router()

async def send_error_message(callback: CallbackQuery, error_msg: str, details: str = "", state: FSMContext = None):
    """Безопасная отправка сообщения об ошибке"""
    # Простой текст без сложного форматирования
    error_text = f"Ошибка подключения\n\nПроблема: {error_msg[:150]}"
    
    if details:
        error_text += f"\n\nДетали: {details[:80]}"
    
    error_text += "\n\nНажмите /start для новой попытки"

    # ВАЖНО: Очищаем состояние при ошибке
    if state:
        await state.clear()

    try:
        # Полностью без reply_markup и сложного форматирования
        await callback.message.edit_text(error_text)
    except:
        try:
            await callback.message.answer(error_text)
        except:
            await callback.message.answer("Ошибка. Попробуйте /start")

class EmailSetupStates(StatesGroup):
    waiting_for_email = State()
    waiting_for_password = State()
    confirming_setup = State()

def create_fresh_setup_menu():
    """Создает свежее главное меню настройки"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="🚀 Подключить Яндекс.Почту", callback_data="email_setup_start"),
        InlineKeyboardButton(text="📘 Подробная инструкция", url="https://teletype.in/@asterioai/yandex-mail"),
        InlineKeyboardButton(text="🔑 Что такое пароль приложения?", callback_data="email_setup_help"),
        InlineKeyboardButton(text="✅ Проверить подключение", callback_data="email_setup_check"),
        InlineKeyboardButton(text="◀️ Назад в меню", callback_data="menu_back")
    )
    builder.adjust(1, 1, 1, 1, 1)
    return builder.as_markup()

def create_fresh_confirmation_menu():
    """Создает свежее меню подтверждения настройки"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="✅ Сохранить настройки", callback_data="email_setup_save"),
        InlineKeyboardButton(text="✏️ Изменить email", callback_data="email_setup_edit_email"),
        InlineKeyboardButton(text="🔑 Изменить пароль", callback_data="email_setup_edit_password"),
        InlineKeyboardButton(text="❌ Отменить", callback_data="email_setup_cancel")
    )
    builder.adjust(1, 2, 1)
    return builder.as_markup()

class EmailSetupWizard:
    """Мастер настройки email"""
    
    @staticmethod
    def get_setup_menu():
        """Главное меню настройки"""
        return create_fresh_setup_menu()
    
    @staticmethod
    def get_confirmation_menu():
        """Меню подтверждения настройки"""
        return create_fresh_confirmation_menu()

setup_wizard = EmailSetupWizard()

@router.callback_query(F.data == "connect_yandex_mail")
async def start_email_setup(callback: CallbackQuery):
    """Начать настройку почты"""
    # Проверяем, уже подключена ли почта
    user_id = callback.from_user.id
    is_connected = await email_sender.can_send_email(user_id)
    
    if is_connected:
        await callback.message.edit_text(
            "✅ <b>Яндекс.Почта уже подключена!</b>\n\n"
            "🎯 <b>Доступные функции:</b>\n"
            "• ✉️ Отправка писем\n"
            "• 📥 Просмотр входящих\n"
            "• 🔍 Поиск по почте\n"
            "• 📊 Анализ писем с AI\n"
            "• 📋 Работа с черновиками\n\n"
            "💡 <b>Как использовать:</b>\n"
            "Просто напишите: \"отправь email@example.com об важной теме\"",
            reply_markup=setup_wizard.get_setup_menu(),
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            "📧 <b>Подключение Яндекс.Почты</b>\n\n"
            "🚀 <b>После подключения вы сможете:</b>\n"
            "• ✉️ Отправлять письма голосом и текстом\n"
            "• 📥 Читать входящие письма\n"
            "• 🔍 Искать письма по содержимому\n"
            "• 🤖 Анализировать письма с помощью AI\n"
            "• 📝 Генерировать ответы автоматически\n\n"
            "⚡ <b>Настройка займет 3 минуты</b>\n\n"
            "🔒 <b>Безопасность:</b> Используем пароли приложений Яндекс",
            reply_markup=setup_wizard.get_setup_menu(),
            parse_mode="HTML"
        )
    
    await callback.answer()

@router.callback_query(F.data == "email_setup_start")
async def email_setup_step1(callback: CallbackQuery, state: FSMContext):
    """Шаг 1: Ввод email"""
    navigation_keyboard = InlineKeyboardBuilder()
    navigation_keyboard.add(
        InlineKeyboardButton(text="📘 Подробная инструкция", url="https://teletype.in/@asterioai/yandex-mail"),
        InlineKeyboardButton(text="◀️ Назад", callback_data="connect_yandex_mail"),
        InlineKeyboardButton(text="❌ Отменить", callback_data="email_setup_cancel")
    )
    navigation_keyboard.adjust(1, 2)
    
    await callback.message.edit_text(
        "📧 <b>Шаг 1 из 3: Ваш email</b>\n\n"
        "📝 Введите ваш email от Яндекс:\n"
        "(например: your_name@yandex.ru)\n\n"
        "⚠️ <b>Поддерживаются только адреса:</b>\n"
        "• @yandex.ru • @yandex.com • @ya.ru • @narod.ru\n\n"
        "📚 <b>Нужна помощь?</b> Нажмите \"Подробная инструкция\"\n\n"
        "✏️ <i>Напишите ваш email в следующем сообщении</i>",
        reply_markup=navigation_keyboard.as_markup(),
        parse_mode="HTML"
    )
    
    await state.set_state(EmailSetupStates.waiting_for_email)
    await callback.answer()

@router.callback_query(F.data == "email_setup_help")
async def email_setup_help(callback: CallbackQuery):
    """Справка по паролю приложения"""
    help_keyboard = InlineKeyboardBuilder()
    help_keyboard.add(
        InlineKeyboardButton(text="📘 Подробная инструкция с картинками", url="https://teletype.in/@asterioai/yandex-mail"),
        InlineKeyboardButton(text="🚀 Продолжить настройку", callback_data="email_setup_start"),
        InlineKeyboardButton(text="◀️ Назад", callback_data="connect_yandex_mail")
    )
    help_keyboard.adjust(1, 2)
    
    await callback.message.edit_text(
        "🔑 <b>Пароль приложения - что это?</b>\n\n"
        "🤖 Это специальный пароль для подключения почты к боту.\n"
        "🛡️ <b>Безопасно:</b> отдельный от основного пароля, можно отозвать.\n\n"
        "🚀 <b>Быстрое создание (3 минуты):</b>\n\n"
        "1️⃣ Откройте <code>id.yandex.ru</code>\n"
        "2️⃣ Войдите в аккаунт → Безопасность\n"
        "3️⃣ Включите 2FA (если не включена)\n"
        "4️⃣ Пароли приложений → Создать\n"
        "5️⃣ Название: \"Telegram Bot\"\n"
        "6️⃣ Скопируйте пароль в бот\n\n"
        "💡 <b>Пароль:</b> 16 символов, например <code>abcd1234abcd1234</code>\n\n"
        "📚 <b>Нужна помощь?</b> Посмотрите подробную инструкцию с картинками!",
        reply_markup=help_keyboard.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "email_setup_check")
async def email_setup_check(callback: CallbackQuery):
    """Проверить подключение"""
    user_id = callback.from_user.id
    is_connected = await email_sender.can_send_email(user_id)
    
    if is_connected:
        # Получаем сохранённые данные
        email_data = await user_tokens.get_user_info(user_id, "email_smtp")
        
        if email_data:
            await callback.message.edit_text(
                "✅ <b>Почта подключена успешно!</b>\n\n"
                f"📧 <b>Email:</b> {escape_email(email_data.get('email', 'Не указан'))}\n"
                f"🔗 <b>Сервер:</b> smtp.yandex.ru:587\n"
                f"🔐 <b>Пароль:</b> ••••••••••••••••\n\n"
                "🎯 <b>Доступные команды:</b>\n"
                "• \"отправь test@example.com об важной теме\"\n"
                "• \"покажи входящие письма\"\n"
                "• \"найди письма от Иван\"\n\n"
                "💡 <b>Попробуйте:</b> Закройте меню и напишите команду!",
                reply_markup=setup_wizard.get_setup_menu(),
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                "⚠️ <b>Данные подключения повреждены</b>\n\n"
                "🔧 Рекомендуется переподключить почту заново.",
                reply_markup=setup_wizard.get_setup_menu(),
                parse_mode="HTML"
            )
    else:
        await callback.message.edit_text(
            "❌ <b>Почта не подключена</b>\n\n"
            "📝 <b>Для подключения:</b>\n"
            "1. Нажмите \"📧 Подключить Яндекс.Почту\"\n"
            "2. Следуйте инструкциям\n\n"
            "❓ <b>Нужна помощь?</b> Нажмите \"🔑 Что такое пароль приложения?\"",
            reply_markup=setup_wizard.get_setup_menu(),
            parse_mode="HTML"
        )
    
    await callback.answer()

@router.message(EmailSetupStates.waiting_for_email)
async def email_setup_step2_email(message: Message, state: FSMContext):
    """Обработка ввода email"""
    email = message.text.strip().lower()
    
    # Проверяем корректность email
    email_pattern = r'^[a-zA-Z0-9._%+-]+@(yandex\.(ru|com)|ya\.ru|narod\.ru)$'
    
    if not re.match(email_pattern, email):
        await message.answer(
            "❌ <b>Некорректный email</b>\n\n"
            "📝 <b>Поддерживаются только адреса Яндекс:</b>\n"
            "• your_name@yandex.ru\n"
            "• your_name@yandex.com\n"
            "• your_name@ya.ru\n"
            "• your_name@narod.ru\n\n"
            "✏️ <i>Попробуйте ещё раз:</i>",
            parse_mode="HTML"
        )
        return
    
    # Сохраняем email в состояние
    await state.update_data(email=email)
    
    navigation_keyboard = InlineKeyboardBuilder()
    navigation_keyboard.add(
        InlineKeyboardButton(text="📘 Подробная инструкция", url="https://teletype.in/@asterioai/yandex-mail"),
        InlineKeyboardButton(text="◀️ Изменить email", callback_data="email_setup_edit_email"),
        InlineKeyboardButton(text="❌ Отменить", callback_data="email_setup_cancel")
    )
    navigation_keyboard.adjust(1, 2)
    
    await message.answer(
        "✅ <b>Email принят!</b>\n\n"
        f"📧 <b>Ваш email:</b> {email}\n\n"
        "🔑 <b>Шаг 2 из 3: Пароль приложения</b>\n\n"
        "📋 <b>Что такое пароль приложения?</b>\n"
        "Это специальный пароль для безопасного подключения почты к боту.\n\n"
        "🚀 <b>Как получить:</b>\n"
        "1. Откройте <code>id.yandex.ru</code>\n"
        "2. Безопасность → Пароли приложений\n"
        "3. Создайте пароль для \"Telegram Bot\"\n\n"
        "📚 <b>Подробная инструкция</b> с картинками доступна по кнопке выше\n\n"
        "🔐 <i>Введите пароль приложения в следующем сообщении:</i>",
        reply_markup=navigation_keyboard.as_markup(),
        parse_mode="HTML"
    )
    
    await state.set_state(EmailSetupStates.waiting_for_password)

@router.message(EmailSetupStates.waiting_for_password)
async def email_setup_step3_password(message: Message, state: FSMContext):
    """Обработка ввода пароля"""
    password = message.text.strip()
    
    # Удаляем сообщение с паролем для безопасности
    try:
        await message.delete()
    except:
        pass
    
    # Проверяем формат пароля (обычно 16 символов)
    if len(password) < 8:
        await message.answer(
            "❌ <b>Пароль слишком короткий</b>\n\n"
            "🔑 <b>Пароль приложения Яндекс:</b>\n"
            "• Обычно 16 символов\n"
            "• Содержит буквы и цифры\n"
            "• Без пробелов и спецсимволов\n\n"
            "💡 <b>Пример:</b> <code>abcdabcdabcdabcd</code>\n\n"
            "🔐 <i>Введите корректный пароль:</i>",
            parse_mode="HTML"
        )
        return
    
    # Получаем email из состояния
    data = await state.get_data()
    email = data.get('email')
    
    if not email:
        await message.answer(
            "❌ <b>Ошибка:</b> Email потерян\n\n"
            "🔄 Начните настройку заново"
        )
        await state.clear()
        return
    
    # Сохраняем данные в состояние
    await state.update_data(password=password)
    
    # Показываем подтверждение
    masked_password = password[:4] + '••••••••••••'
    
    confirmation_keyboard = InlineKeyboardBuilder()
    confirmation_keyboard.add(
        InlineKeyboardButton(text="✅ Подключить почту", callback_data="email_setup_save"),
        InlineKeyboardButton(text="📘 Подробная инструкция", url="https://teletype.in/@asterioai/yandex-mail"),
        InlineKeyboardButton(text="✏️ Изменить email", callback_data="email_setup_edit_email"),
        InlineKeyboardButton(text="🔑 Изменить пароль", callback_data="email_setup_edit_password"),
        InlineKeyboardButton(text="❌ Отменить", callback_data="email_setup_cancel")
    )
    confirmation_keyboard.adjust(1, 1, 2, 1)
    
    await message.answer(
        "🔍 <b>Шаг 3 из 3: Подтверждение</b>\n\n"
        f"📧 <b>Email:</b> {escape_email(email)}\n"
        f"🔐 <b>Пароль:</b> {masked_password}\n"
        f"🌐 <b>Сервер:</b> smtp.yandex.ru:587\n\n"
        "⚡ <b>Готово к подключению!</b>\n\n"
        "✅ Нажмите <b>\"Подключить почту\"</b> для завершения\n"
        "✏️ Или измените данные при необходимости\n\n"
        "📚 <b>Возникли проблемы?</b> Посмотрите подробную инструкцию",
        reply_markup=confirmation_keyboard.as_markup(),
        parse_mode="HTML"
    )
    
    await state.set_state(EmailSetupStates.confirming_setup)

@router.callback_query(F.data == "email_setup_save")
async def email_setup_save(callback: CallbackQuery, state: FSMContext):
    """Сохранить настройки"""
    # Сразу отвечаем на callback чтобы избежать timeout
    await callback.answer()
    
    # Проверяем текущее состояние для отладки
    current_state = await state.get_state()
    print(f"DEBUG: Current state: {current_state}")
    
    data = await state.get_data()
    email = data.get('email')
    password = data.get('password')
    
    print(f"DEBUG: Email: {email}, Password length: {len(password) if password else 0}")
    
    if not email or not password:
        await callback.message.edit_text(
            "❌ <b>Ошибка: данные потеряны</b>\n\n"
            "🔄 Начните настройку заново",
            parse_mode="HTML"
        )
        return
    
    # Показываем процесс тестирования
    await callback.message.edit_text(
        "🔄 <b>Тестируем подключение...</b>\n\n"
        "⏳ Проверяем настройки SMTP...\n"
        "💡 Это может занять до 30 секунд",
        parse_mode="HTML"
    )
    
    try:
        # Импортируем здесь для тестирования
        from utils.email_sender_real import RealEmailSender
        
        real_sender = RealEmailSender()
        
        # Тестируем подключение с увеличенным таймаутом
        test_result = await real_sender.test_connection(email, password)
        
        if test_result['success']:
            # Сохраняем настройки
            user_id = callback.from_user.id
            email_data = {
                'email': email,
                'password': password,
                'smtp_server': 'smtp.yandex.ru',
                'smtp_port': 587,
                'setup_date': data.get('setup_date', ''),
                'test_result': test_result
            }
            
            await user_tokens.save_token(user_id, "email_smtp", {'access_token': 'smtp_configured', 'user_info': email_data})
            
            await callback.message.edit_text(
                "🎉 <b>Почта подключена успешно!</b>\n\n"
                f"📧 <b>Email:</b> {escape_email(email)}\n"
                f"✅ <b>Статус:</b> Активна\n"
                f"🕐 <b>Протестировано:</b> Только что\n\n"
                "🚀 <b>Теперь доступны все функции:</b>\n"
                "• ✉️ Отправка писем\n"
                "• 📥 Чтение входящих\n"
                "• 🔍 Поиск по почте\n"
                "• 🤖 AI анализ писем\n\n"
                "💡 <b>Попробуйте прямо сейчас:</b>\n"
                "\"отправь test@example.com об тестовом письме\"",
                parse_mode="HTML"
            )
            
            # КРИТИЧЕСКИ ВАЖНО: Очистить состояние при успехе
            await state.clear()
            return
            
        else:
            error_msg = test_result.get('error', 'Неизвестная ошибка')
            
            # Определяем тип ошибки для более точного совета
            suggestion = test_result.get('suggestion', '')
            
            if suggestion == 'smtp_blocked':
                advice = "SMTP заблокирован провайдером. Попробуйте мобильный интернет или отключите VPN."
            elif 'timeout' in error_msg.lower() or 'timed out' in error_msg.lower() or '10060' in error_msg:
                advice = "Проблема с таймаутом. Проверьте интернет или отключите VPN/прокси."
            elif 'authentication' in error_msg.lower() or 'login' in error_msg.lower():
                advice = "Проблема с аутентификацией. Проверьте пароль приложения и включите 2FA."
            else:
                advice = "Проверьте пароль приложения, 2FA и интернет-соединение."
            
            # Используем безопасную функцию отправки ошибки
            await send_error_message(callback, advice, error_msg, state)
    
    except Exception as e:
        error_detail = str(e)[:150]
        # Используем безопасную функцию отправки ошибки
        await send_error_message(callback, "Техническая ошибка при тестировании", error_detail, state)

@router.callback_query(F.data == "email_setup_force_save")
async def email_setup_force_save(callback: CallbackQuery, state: FSMContext):
    """Принудительно сохранить настройки без тестирования"""
    await callback.answer()
    
    data = await state.get_data()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        await callback.message.edit_text(
            "❌ <b>Ошибка: данные потеряны</b>\n\n"
            "🔄 Начните настройку заново",
            parse_mode="HTML"
        )
        return
    
    try:
        # Сохраняем настройки без тестирования
        user_id = callback.from_user.id
        email_data = {
            'email': email,
            'password': password,
            'smtp_server': 'smtp.yandex.ru',
            'smtp_port': 587,
            'setup_date': data.get('setup_date', ''),
            'test_result': {'success': False, 'message': 'Сохранено без тестирования'}
        }
        
        await user_tokens.save_token(user_id, "email_smtp", {'access_token': 'smtp_configured', 'user_info': email_data})
        
        await callback.message.edit_text(
            "💾 <b>Настройки сохранены!</b>\n\n"
            f"📧 <b>Email:</b> {escape_email(email)}\n"
            f"⚠️ <b>Статус:</b> Сохранено без тестирования\n\n"
            "🚀 <b>Доступные функции:</b>\n"
            "• ✉️ Отправка писем\n"
            "• 📥 Чтение входящих\n"
            "• 🔍 Поиск по почте\n"
            "• 🤖 AI анализ писем\n\n"
            "💡 <b>Попробуйте отправить письмо:</b>\n"
            "\"отправь test@example.com об тестовом письме\"\n\n"
            "🔧 <b>Если возникнут проблемы:</b>\n"
            "Переподключите почту через меню с правильными данными",
            parse_mode="HTML"
        )
        
    except Exception as e:
        await callback.message.edit_text(
            "❌ <b>Ошибка сохранения настроек</b>\n\n"
            f"🔧 Детали: {str(e)[:100]}...\n\n"
            "Попробуйте настройку заново",
            reply_markup=setup_wizard.get_setup_menu(),
            parse_mode="HTML"
        )
    
    await state.clear()

@router.callback_query(F.data == "email_setup_troubleshoot")
async def email_setup_troubleshoot(callback: CallbackQuery):
    """Показать инструкции по решению проблем"""
    await callback.answer()
    
    troubleshoot_text = """
🔧 <b>Решение проблем с подключением</b>

<b>🚫 SMTP заблокирован провайдером:</b>
• 📱 Попробуйте мобильный интернет
• 🛡️ Отключите VPN/прокси
• 🔥 Проверьте брандмауэр
• 📞 Обратитесь к провайдеру

<b>🔐 Проблемы с аутентификацией:</b>
1. Зайдите на <code>id.yandex.ru</code>
2. Включите двухфакторную аутентификацию
3. Создайте новый пароль приложения
4. Включите IMAP в настройках почты

<b>📧 Настройка IMAP в Яндекс:</b>
1. Откройте <code>mail.yandex.ru</code>
2. Настройки → Почтовые программы
3. Включите "Доступ по IMAP"

<b>🎯 Проверка портов:</b>
Выполните в PowerShell:
<code>Test-NetConnection smtp.yandex.ru -Port 587</code>
<code>Test-NetConnection imap.yandex.ru -Port 993</code>

💡 <b>Совет:</b> Если SMTP не работает, можете сохранить настройки для чтения писем. Отправка будет работать в режиме сохранения в файлы.
    """
    
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="🔄 Попробовать еще раз", callback_data="email_setup_save"),
        InlineKeyboardButton(text="💾 Сохранить без тестирования", callback_data="email_setup_force_save"),
        InlineKeyboardButton(text="◀️ Назад", callback_data="email_setup_save")
    )
    builder.adjust(1, 1, 1)
    
    try:
        await callback.message.edit_text(
            troubleshoot_text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    except Exception as edit_error:
        # Если редактирование не удалось, отправляем новое сообщение
        await callback.message.answer(
            troubleshoot_text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )

@router.callback_query(F.data.startswith("email_setup_edit_"))
async def email_setup_edit(callback: CallbackQuery, state: FSMContext):
    """Редактирование данных настройки"""
    edit_type = callback.data.split("_")[-1]
    
    if edit_type == "email":
        navigation_keyboard = InlineKeyboardBuilder()
        navigation_keyboard.add(
            InlineKeyboardButton(text="📘 Подробная инструкция", url="https://teletype.in/@asterioai/yandex-mail"),
            InlineKeyboardButton(text="◀️ Назад", callback_data="connect_yandex_mail"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="email_setup_cancel")
        )
        navigation_keyboard.adjust(1, 2)
        
        await callback.message.edit_text(
            "✏️ <b>Изменить email</b>\n\n"
            "📝 Введите новый email от Яндекс:\n"
            "(например: your_name@yandex.ru)\n\n"
            "⚠️ <b>Поддерживаются только адреса:</b>\n"
            "• @yandex.ru • @yandex.com • @ya.ru • @narod.ru",
            reply_markup=navigation_keyboard.as_markup(),
            parse_mode="HTML"
        )
        await state.set_state(EmailSetupStates.waiting_for_email)
    
    elif edit_type == "password":
        navigation_keyboard = InlineKeyboardBuilder()
        navigation_keyboard.add(
            InlineKeyboardButton(text="📘 Подробная инструкция", url="https://teletype.in/@asterioai/yandex-mail"),
            InlineKeyboardButton(text="◀️ Изменить email", callback_data="email_setup_edit_email"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="email_setup_cancel")
        )
        navigation_keyboard.adjust(1, 2)
        
        await callback.message.edit_text(
            "🔑 <b>Изменить пароль приложения</b>\n\n"
            "🔐 Введите новый пароль приложения:\n\n"
            "💡 <b>Где получить:</b>\n"
            "1. <code>id.yandex.ru</code> → Безопасность\n"
            "2. Создайте пароль для \"Telegram Bot\"\n\n"
            "📚 Подробная инструкция доступна по кнопке выше",
            reply_markup=navigation_keyboard.as_markup(),
            parse_mode="HTML"
        )
        await state.set_state(EmailSetupStates.waiting_for_password)
    
    await callback.answer()

@router.callback_query(F.data == "email_setup_cancel")
async def email_setup_cancel(callback: CallbackQuery, state: FSMContext):
    """Отменить настройку"""
    await callback.message.edit_text(
        "❌ <b>Настройка отменена</b>\n\n"
        "💡 Вы можете начать настройку заново в любое время через меню\n"
        "\"📧 Подключить Почту\"",
        parse_mode="HTML"
    )
    
    await state.clear()
    await callback.answer()

@router.message(F.text.contains("помощь с настройкой почты"))
async def email_help_command(message: Message):
    """Помощь с настройкой почты"""
    help_text = """
🆘 <b>Помощь с настройкой Яндекс.Почты</b>

<b>🔐 Создание пароля приложения:</b>
1. Зайдите на <code>id.yandex.ru</code>
2. Перейдите в "Безопасность"
3. Включите "Двухфакторную аутентификацию"
4. Найдите "Пароли приложений"
5. Создайте пароль с названием "Telegram Bot"

<b>📧 Включение IMAP:</b>
1. Откройте <code>mail.yandex.ru</code>
2. Настройки → Почтовые программы
3. Включите "Доступ по IMAP"

<b>🔧 Если SMTP заблокирован:</b>
• Попробуйте мобильный интернет
• Отключите VPN/прокси
• Обратитесь к провайдеру

<b>💡 Альтернатива:</b>
Можете использовать режим "только чтение" - получение писем работает даже если отправка заблокирована.

Для повторной настройки нажмите /start
    """
    
    await message.answer(help_text, parse_mode="HTML")