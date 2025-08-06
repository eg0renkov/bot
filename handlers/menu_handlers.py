from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from utils.keyboards import keyboards
from database.vector_memory import vector_memory
from config.settings import settings
from utils.html_utils import escape_html, escape_email, truncate_and_escape
from utils.email_analyzer import email_analyzer

router = Router()

# Обработчик /start перенесен в handlers/auth.py для системы авторизации

@router.message(F.text == "📱 Меню")
async def show_full_menu(message: Message):
    """Показать главное меню с категориями"""
    menu_text = """
🏠 <b>Главное меню</b>

🎯 Выберите категорию для продолжения:

<i>💡 Совет: Используйте категории для быстрого доступа к нужным функциям</i>
    """
    
    await message.answer(
        menu_text,
        reply_markup=keyboards.full_menu(),
        parse_mode="HTML"
    )

# Обработчики callback кнопок из меню
@router.callback_query(F.data == "close_menu")
async def close_menu(callback: CallbackQuery):
    """Закрыть меню"""
    await callback.message.delete()
    await callback.answer("Меню закрыто")

@router.callback_query(F.data == "menu_chat")
async def menu_chat_callback(callback: CallbackQuery):
    """Информация о чате с AI"""
    await callback.message.edit_text(
        "💬 <b>Чат с AI</b>\n\n"
        "Просто пишите мне сообщения, и я буду отвечать с помощью ChatGPT!\n\n"
        "🎯 <b>Возможности:</b>\n"
        "• Отвечаю на любые вопросы\n"
        "• Помогаю с задачами\n"
        "• Генерирую тексты\n"
        "• Объясняю сложные темы\n\n"
        "💡 <i>Просто закройте это меню и начните писать!</i>",
        reply_markup=keyboards.back_button("menu_back"),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "menu_voice")
async def menu_voice_callback(callback: CallbackQuery):
    """Информация о голосовых функциях"""
    await callback.message.edit_text(
        "🎤 <b>Голосовые сообщения</b>\n\n"
        "Отправьте мне голосовое сообщение, и я:\n"
        "• 🎧 Распознаю вашу речь\n"
        "• 🤖 Обработаю через AI\n"
        "• 🔊 Отвечу голосом и текстом\n\n"
        "📝 <b>Как использовать:</b>\n"
        "1. Нажмите на микрофон в Telegram\n"
        "2. Запишите сообщение\n"
        "3. Отправьте мне\n\n"
        "✨ <i>Также после моего текстового ответа можно нажать «🎤 Озвучить»</i>",
        reply_markup=keyboards.back_button("menu_back"),
        parse_mode="HTML"
    )
    await callback.answer()

# Обработчик настроек поиска - ДОЛЖЕН БЫТЬ ПЕРВЫМ
@router.callback_query(F.data == "settings_email_search")
async def settings_email_search_callback(callback: CallbackQuery):
    """Настройки поиска писем"""
    user_id = callback.from_user.id
    
    # Загружаем текущие настройки поиска
    import json
    import os
    
    settings_dir = "data/search_settings"
    os.makedirs(settings_dir, exist_ok=True)
    settings_file = os.path.join(settings_dir, f"user_{user_id}_search.json")
    
    # Настройки по умолчанию
    default_settings = {
        'search_limit': 10,           # Количество результатов
        'content_analysis': False,    # Анализ содержимого писем
        'search_in_body': True,       # Поиск в тексте письма
        'search_in_attachments': False, # Поиск в вложениях
        'date_range_days': 365,       # Диапазон поиска в днях
        'priority_search': False      # Приоритетный поиск (быстрее, но менее точно)
    }
    
    # Загружаем настройки пользователя
    current_settings = default_settings.copy()
    if os.path.exists(settings_file):
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                user_settings = json.load(f)
                current_settings.update(user_settings)
        except Exception as e:
            # Если ошибка загрузки, используем настройки по умолчанию
            pass
    
    # Формируем текст настроек
    text = "🔍 <b>Настройки поиска писем</b>\n\n"
    text += "📊 <b>Текущие настройки:</b>\n\n"
    
    text += f"📈 Количество результатов: <b>{current_settings['search_limit']}</b>\n"
    text += f"🔍 Поиск в содержимом: {'✅' if current_settings['search_in_body'] else '❌'}\n"
    text += f"🧠 AI анализ содержания: {'✅' if current_settings['content_analysis'] else '❌'}\n"
    text += f"📎 Поиск в вложениях: {'✅' if current_settings['search_in_attachments'] else '❌'}\n"
    text += f"📅 Диапазон поиска: <b>{current_settings['date_range_days']}</b> дней\n"
    text += f"⚡ Быстрый поиск: {'✅' if current_settings['priority_search'] else '❌'}\n\n"
    
    text += "💡 <b>Подсказки:</b>\n"
    text += "• AI анализ содержания - более точный поиск, но медленнее\n"
    text += "• Быстрый поиск - ищет только в заголовках и отправителях\n"
    text += "• Больше результатов - может замедлить поиск"
    
    # Создаем клавиатуру настроек
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    
    builder = InlineKeyboardBuilder()
    
    # Настройка количества результатов
    builder.add(InlineKeyboardButton(
        text=f"📈 Результатов: {current_settings['search_limit']}", 
        callback_data="search_setting_limit"
    ))
    
    # Переключатели
    body_text = "🔍 Поиск в содержимом: " + ("✅" if current_settings['search_in_body'] else "❌")
    builder.add(InlineKeyboardButton(text=body_text, callback_data="search_toggle_body"))
    
    ai_text = "🧠 AI анализ: " + ("✅" if current_settings['content_analysis'] else "❌")
    builder.add(InlineKeyboardButton(text=ai_text, callback_data="search_toggle_ai"))
    
    attach_text = "📎 Поиск в вложениях: " + ("✅" if current_settings['search_in_attachments'] else "❌")
    builder.add(InlineKeyboardButton(text=attach_text, callback_data="search_toggle_attachments"))
    
    days_text = f"📅 Диапазон: {current_settings['date_range_days']} дн"
    builder.add(InlineKeyboardButton(text=days_text, callback_data="search_setting_days"))
    
    priority_text = "⚡ Быстрый поиск: " + ("✅" if current_settings['priority_search'] else "❌")
    builder.add(InlineKeyboardButton(text=priority_text, callback_data="search_toggle_priority"))
    
    # Кнопки управления
    builder.add(
        InlineKeyboardButton(text="💾 Сохранить", callback_data="search_save_settings"),
        InlineKeyboardButton(text="🔄 Сбросить", callback_data="search_reset_settings")
    )
    
    builder.add(InlineKeyboardButton(text="◀️ К настройкам", callback_data="category_settings"))
    
    # Компоновка: по 1 кнопке в ряд для настроек, по 2 для управления
    builder.adjust(1, 1, 1, 1, 1, 1, 2, 1)
    
    await callback.message.edit_text(
        text, 
        reply_markup=builder.as_markup(), 
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "menu_back")
async def menu_back_callback(callback: CallbackQuery):
    """Вернуться в главное меню"""
    await callback.message.edit_text(
        "🏠 <b>Главное меню</b>\n\n🎯 Выберите категорию для продолжения:",
        reply_markup=keyboards.full_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

# Обработчики категорий
@router.callback_query(F.data == "category_mail")
async def category_mail_callback(callback: CallbackQuery):
    """Категория: Почта"""
    user_id = callback.from_user.id
    from utils.email_sender import email_sender
    is_connected = await email_sender.can_send_email(user_id)
    
    status = "✅ Подключена" if is_connected else "❌ Не подключена"
    
    await callback.message.edit_text(
        f"📧 <b>Почта</b>\n\n"
        f"📊 <b>Статус:</b> {status}\n\n"
        "🎯 <b>Возможности:</b>\n"
        "• Чтение и отправка писем\n"
        "• Умный поиск по содержимому\n"
        "• Работа с черновиками\n"
        "• AI-помощник для писем\n\n"
        "📌 <b>Выберите действие:</b>",
        reply_markup=keyboards.mail_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "category_calendar")
async def category_calendar_callback(callback: CallbackQuery):
    """Категория: Календарь"""
    user_id = callback.from_user.id
    from database.user_tokens import user_tokens
    
    # Проверяем подключение календаря
    token_data = await user_tokens.get_token_data(user_id, "calendar")
    is_connected = bool(token_data and token_data.get("app_password"))
    
    status = "✅ Подключен" if is_connected else "❌ Не подключен"
    
    await callback.message.edit_text(
        f"📅 <b>Календарь</b>\n\n"
        f"📊 <b>Статус:</b> {status}\n\n"
        "🎯 <b>Возможности:</b>\n"
        "• Создание событий голосом\n"
        "• Умные напоминания\n"
        "• Анализ расписания\n"
        "• Планирование встреч\n\n"
        "📌 <b>Выберите действие:</b>",
        reply_markup=keyboards.calendar_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "category_memory")
async def category_memory_callback(callback: CallbackQuery):
    """Категория: Память"""
    status = "✅ Активна" if vector_memory else "❌ Не настроена"
    
    await callback.message.edit_text(
        f"🧠 <b>Память бота</b>\n\n"
        f"📊 <b>Статус:</b> {status}\n\n"
        "🎯 <b>Возможности:</b>\n"
        "• Запоминание всех разговоров\n"
        "• Поиск по истории общения\n"
        "• Сохранение важных знаний\n"
        "• Контекстные подсказки\n\n"
        "📌 <b>Выберите действие:</b>",
        reply_markup=keyboards.category_memory_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "category_ai")
async def category_ai_callback(callback: CallbackQuery):
    """Категория: AI Помощник"""
    await callback.message.edit_text(
        "💬 <b>AI Помощник</b>\n\n"
        "🤖 <b>Возможности:</b>\n"
        "• Ответы на любые вопросы\n"
        "• Генерация текстов\n"
        "• Помощь с задачами\n"
        "• Голосовое общение\n\n"
        "🎨 <b>Режимы работы:</b>\n"
        "• 💬 Обычный чат\n"
        "• 🎤 Голосовой режим\n"
        "• 📝 Работа с текстами\n"
        "• 🧠 Аналитика\n\n"
        "📌 <b>Выберите действие:</b>",
        reply_markup=keyboards.ai_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "category_settings")
async def category_settings_callback(callback: CallbackQuery):
    """Категория: Настройки"""
    await callback.message.edit_text(
        "⚙️ <b>Настройки</b>\n\n"
        "🔧 <b>Доступные настройки:</b>\n"
        "• Профиль и персонализация\n"
        "• Уведомления и звуки\n"
        "• Язык и регион\n"
        "• Приватность и безопасность\n\n"
        "📌 <b>Выберите раздел:</b>",
        reply_markup=keyboards.category_settings_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "help_menu")
async def help_menu_callback(callback: CallbackQuery):
    """Справка из меню"""
    help_text = """
❓ <b>Справка по боту</b>

🤖 <b>Основные функции:</b>
• Пишите сообщения для общения с AI
• Отправляйте голосовые сообщения
• Используйте меню для дополнительных функций

📧 <b>Почта и календарь:</b>
• Подключите Яндекс сервисы
• Управляйте письмами и событиями
• Создавайте черновики

🧠 <b>Память:</b>
• Бот запоминает ваши разговоры
• Ищите информацию из прошлого
• Сохраняйте важные знания

💡 <b>Совет:</b> Закройте меню и просто начните писать!
    """
    
    await callback.message.edit_text(
        help_text,
        reply_markup=keyboards.back_button("menu_back"),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "memory_stats")
async def memory_stats_callback(callback: CallbackQuery):
    """Статистика памяти"""
    if not vector_memory:
        await callback.answer("❌ Векторная память не настроена", show_alert=True)
        return
    
    try:
        user_id = callback.from_user.id
        stats = await vector_memory.get_user_stats(user_id)
        
        stats_text = f"""
📊 <b>Статистика памяти</b>

💬 Всего разговоров: <code>{stats.get('total_conversations', 0)}</code>
🧠 Записей в базе знаний: <code>{stats.get('knowledge_entries', 0)}</code>
📏 Средняя длина сообщения: <code>{stats.get('avg_conversation_length', 0):.0f}</code> символов

📅 Первое взаимодействие: <code>{stats.get('first_interaction', 'Нет данных')}</code>
🕒 Последнее взаимодействие: <code>{stats.get('last_interaction', 'Нет данных')}</code>

💡 <i>Память улучшается с каждым разговором!</i>
        """
        
        await callback.message.edit_text(
            stats_text,
            reply_markup=keyboards.back_button("memory_menu"),
            parse_mode="HTML"
        )
        
    except Exception as e:
        await callback.answer("❌ Ошибка получения статистики", show_alert=True)
    
    await callback.answer()

@router.callback_query(F.data.startswith("yandex_"))
async def yandex_handlers(callback: CallbackQuery):
    """Обработчики Яндекс интеграций"""
    action = callback.data.replace("yandex_", "")
    
    if action == "benefits":
        await callback.message.edit_text(
            "🌟 <b>Преимущества интеграции с Яндекс</b>\n\n"
            "📧 <b>Яндекс.Почта:</b>\n"
            "• Чтение писем через AI\n"
            "• Умное составление ответов\n"
            "• Автоматическая сортировка\n"
            "• Поиск по содержимому\n\n"
            "📅 <b>Яндекс.Календарь:</b>\n"
            "• Создание событий голосом\n"
            "• Умные напоминания\n"
            "• Анализ занятости\n"
            "• Предложения времени встреч\n\n"
            "🔒 <i>Все данные обрабатываются безопасно!</i>",
            reply_markup=keyboards.yandex_connect_menu(),
            parse_mode="HTML"
        )
    
    await callback.answer()


# Новые обработчики для недостающих функций
@router.callback_query(F.data == "settings_menu")
async def settings_menu_callback(callback: CallbackQuery):
    """Показать меню настроек"""
    await callback.message.edit_text(
        "⚙️ <b>Настройки</b>\n\n"
        "Выберите что хотите настроить:",
        reply_markup=keyboards.settings_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "memory_menu")
async def memory_menu_callback(callback: CallbackQuery):
    """Показать меню памяти"""
    await callback.message.edit_text(
        "🧠 <b>Управление памятью</b>\n\n"
        "Выберите действие:",
        reply_markup=keyboards.memory_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "mail_inbox")
async def mail_inbox_callback(callback: CallbackQuery):
    """Показать входящие письма"""
    user_id = callback.from_user.id
    
    # Проверяем подключение почты
    from utils.email_sender import email_sender
    if not await email_sender.can_send_email(user_id):
        await callback.message.edit_text(
            "📧 <b>Почта не подключена</b>\n\n"
            "🔧 <b>Для просмотра входящих писем:</b>\n"
            "1. Нажмите «📧 Подключить Почту»\n"
            "2. Пройдите настройку\n"
            "3. Получите доступ к письмам\n\n"
            "💡 После подключения сможете:\n"
            "• Читать входящие письма\n"
            "• Искать по содержимому\n"
            "• Анализировать с помощью AI",
            reply_markup=keyboards.back_button("menu_back"),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    try:
        # Показываем статус загрузки
        await callback.message.edit_text(
            "📧 <b>Загружаю входящие письма...</b>\n\n"
            "⏳ Подключаюсь к серверу...",
            parse_mode="HTML"
        )
        
        # Получаем письма
        from utils.email_sender_real import real_email_sender
        emails = await real_email_sender.get_inbox_emails(user_id, limit=10)
        
        if not emails:
            await callback.message.edit_text(
                "📧 <b>Входящие письма</b>\n\n"
                "📭 В папке «Входящие» нет писем\n\n"
                "💡 <b>Возможные причины:</b>\n"
                "• Все письма прочитаны\n"
                "• Письма в других папках\n"
                "• Настройки фильтрации",
                reply_markup=keyboards.back_button("menu_back"),
                parse_mode="HTML"
            )
            await callback.answer()
            return
        
        # Формируем список писем
        emails_text = "📧 <b>Входящие письма</b>\n\n"
        
        for i, email_data in enumerate(emails, 1):
            sender = email_data.get('sender', 'Неизвестный отправитель')
            subject = email_data.get('subject', 'Без темы')
            date = email_data.get('date', '')
            
            # Экранируем и обрезаем значения
            sender = truncate_and_escape(sender, 30)
            subject = truncate_and_escape(subject, 40)
            
            emails_text += f"<b>{i}.</b> 👤 {sender}\n"
            emails_text += f"📝 {subject}\n"
            if date:
                emails_text += f"🕐 {escape_html(date[:16])}\n"
            emails_text += "\n"
        
        emails_text += "💡 <i>Для поиска по письмам используйте команду: \"найди письма от [имя]\"</i>"
        
        await callback.message.edit_text(
            emails_text,
            reply_markup=keyboards.inbox_menu(),
            parse_mode="HTML"
        )
        
    except Exception as e:
        await callback.message.edit_text(
            "❌ <b>Ошибка загрузки писем</b>\n\n"
            f"💥 <b>Проблема:</b> {str(e)[:100]}...\n\n"
            "🔧 <b>Попробуйте:</b>\n"
            "• Проверить подключение к интернету\n"
            "• Переподключить почту\n"
            "• Обратиться в поддержку",
            reply_markup=keyboards.back_button("menu_back"),
            parse_mode="HTML"
        )
    
    await callback.answer()

@router.callback_query(F.data == "mail_search")
async def mail_search_callback(callback: CallbackQuery):
    """Поиск писем"""
    user_id = callback.from_user.id
    
    # Проверяем подключение почты
    from utils.email_sender import email_sender
    if not await email_sender.can_send_email(user_id):
        await callback.message.edit_text(
            "🔍 <b>Поиск писем</b>\n\n"
            "🔐 Для поиска писем необходимо:\n"
            "1. Подключить Яндекс.Почту\n"
            "2. Предоставить разрешения\n\n"
            "🎯 После подключения здесь будет:\n"
            "• Поиск по теме письма\n"
            "• Поиск по отправителю\n"
            "• Поиск по содержимому\n"
            "• AI-анализ писем",
            reply_markup=keyboards.back_button("menu_back"),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        "🔍 <b>Поиск писем</b>\n\n"
        "💡 <b>Как искать письма:</b>\n"
        "Закройте меню и напишите команду поиска\n\n"
        "🎯 <b>Примеры поисковых запросов:</b>\n"
        "• \"найди письма от Иван\"\n"
        "• \"найди письма об работе\"\n"
        "• \"найди письма за вчера\"\n"
        "• \"покажи письма с важными\"\n\n"
        "🤖 <b>AI найдет:</b>\n"
        "• По имени отправителя\n"
        "• По теме письма\n"
        "• По содержимому\n"
        "• По ключевым словам",
        reply_markup=keyboards.back_button("menu_back"),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("settings_"))
async def settings_handlers(callback: CallbackQuery):
    """Обработчики настроек"""
    setting = callback.data.replace("settings_", "")
    
    if setting == "voice":
        await callback.message.edit_text(
            "🎤 <b>Настройки голоса</b>\n\n"
            "📊 <b>Текущие настройки:</b>\n"
            "• Распознавание: ✅ Включено\n"
            "• Синтез речи: ✅ Включен\n"
            "• Язык: 🇷🇺 Русский\n"
            "• Голос: Женский\n\n"
            "🚧 <i>Настройка в разработке</i>",
            reply_markup=keyboards.back_button("category_settings"),
            parse_mode="HTML"
        )
    elif setting == "vector":
        await callback.message.edit_text(
            "🧠 <b>Векторная память</b>\n\n"
            f"📊 <b>Статус:</b> {'✅ Включена' if vector_memory else '❌ Отключена'}\n"
            "🔧 <b>Настройки:</b>\n"
            "• База данных: Supabase\n"
            "• Модель эмбеддингов: OpenAI\n"
            "• Максимум записей: 10,000\n\n"
            "💡 <i>Векторная память улучшает понимание контекста</i>",
            reply_markup=keyboards.back_button("category_settings"),
            parse_mode="HTML"
        )
    elif setting == "notifications":
        await callback.message.edit_text(
            "🔔 <b>Настройки уведомлений</b>\n\n"
            "📱 <b>Текущие настройки:</b>\n"
            "• Уведомления: ✅ Включены\n"
            "• Звук: ✅ Включен\n"
            "• Напоминания: ✅ Включены\n\n"
            "🚧 <i>Настройка в разработке</i>",
            reply_markup=keyboards.back_button("category_settings"),
            parse_mode="HTML"
        )
    elif setting == "language":
        await callback.message.edit_text(
            "🌐 <b>Настройки языка</b>\n\n"
            "🗣️ <b>Текущий язык:</b> 🇷🇺 Русский\n\n"
            "📝 <b>Доступные языки:</b>\n"
            "• 🇷🇺 Русский (текущий)\n"
            "• 🇺🇸 English\n"
            "• 🇩🇪 Deutsch\n\n"
            "🚧 <i>Смена языка в разработке</i>",
            reply_markup=keyboards.back_button("category_settings"),
            parse_mode="HTML"
        )
    elif setting == "theme":
        # Этот пункт больше не должен быть доступен, но обрабатываем для совместимости
        await callback.message.edit_text(
            "🎨 <b>Внешний вид</b>\n\n"
            "⚠️ <i>Данный раздел больше недоступен</i>\n\n"
            "Вернитесь к настройкам для выбора других опций.",
            reply_markup=keyboards.back_button("category_settings"),
            parse_mode="HTML"
        )
    elif setting == "privacy":
        # Этот пункт больше не должен быть доступен, но обрабатываем для совместимости
        await callback.message.edit_text(
            "🔐 <b>Приватность</b>\n\n"
            "⚠️ <i>Данный раздел больше недоступен</i>\n\n"
            "Вернитесь к настройкам для выбора других опций.",
            reply_markup=keyboards.back_button("category_settings"),
            parse_mode="HTML"
        )
    
    await callback.answer()

@router.callback_query(F.data.startswith("memory_"))
async def memory_handlers(callback: CallbackQuery):
    """Обработчики памяти"""
    action = callback.data.replace("memory_", "")
    
    if action == "search":
        await callback.message.edit_text(
            "🔍 <b>Поиск в памяти</b>\n\n"
            "💡 <b>Как искать:</b>\n"
            "Просто напишите запрос после закрытия меню\n\n"
            "🎯 <b>Примеры поисков:</b>\n"
            "• \"Что мы обсуждали про Python?\"\n"
            "• \"Найди информацию о проектах\"\n"
            "• \"Покажи последние важные темы\"\n\n"
            "🧠 <i>AI найдет релевантную информацию из истории</i>",
            reply_markup=keyboards.back_button("memory_menu"),
            parse_mode="HTML"
        )
    elif action == "save":
        await callback.message.edit_text(
            "💾 <b>Сохранить знания</b>\n\n"
            "📝 <b>Как сохранить:</b>\n"
            "Напишите важную информацию после закрытия меню\n\n"
            "💡 <b>Примеры:</b>\n"
            "• \"Запомни: мой любимый цвет синий\"\n"
            "• \"Сохрани: встреча каждый понедельник в 10:00\"\n"
            "• \"Запиши: проект называется SuperBot\"\n\n"
            "🧠 <i>Бот запомнит эту информацию навсегда</i>",
            reply_markup=keyboards.back_button("memory_menu"),
            parse_mode="HTML"
        )
    elif action == "clear":
        await callback.message.edit_text(
            "🗑️ <b>Очистка памяти</b>\n\n"
            "⚠️ <b>Внимание!</b>\n"
            "Это действие удалит:\n"
            "• Всю историю разговоров\n"
            "• Сохраненные знания\n"
            "• Векторные эмбеддинги\n\n"
            "🚧 <i>Функция в разработке</i>\n"
            "Используйте команду /clear для очистки текущего диалога",
            reply_markup=keyboards.back_button("memory_menu"),
            parse_mode="HTML"
        )
    elif action == "help":
        await callback.message.edit_text(
            "❓ <b>Справка по памяти</b>\n\n"
            "🧠 <b>Как работает память:</b>\n"
            "• Бот запоминает все разговоры\n"
            "• Использует векторный поиск\n"
            "• Находит похожие темы\n"
            "• Улучшает ответы со временем\n\n"
            "🔧 <b>Команды памяти:</b>\n"
            "• /memory_stats - статистика\n"
            "• /search_memory - поиск\n"
            "• /save_knowledge - сохранить\n"
            "• /clear_memory - очистить\n\n"
            "💡 <i>Память становится умнее с каждым использованием!</i>",
            reply_markup=keyboards.back_button("memory_menu"),
            parse_mode="HTML"
        )
    
    await callback.answer()

@router.callback_query(F.data == "mail_analyze_inbox")
async def mail_analyze_inbox_callback(callback: CallbackQuery):
    """Анализ входящих писем с помощью AI"""
    user_id = callback.from_user.id
    user_name = callback.from_user.first_name or "Пользователь"
    if callback.from_user.last_name:
        user_name += f" {callback.from_user.last_name}"
    
    # Проверяем подключение почты
    from utils.email_sender import email_sender
    if not await email_sender.can_send_email(user_id):
        await callback.message.edit_text(
            "🔍 <b>Анализ писем</b>\n\n"
            "🔐 Для анализа писем необходимо:\n"
            "1. Подключить Яндекс.Почту\n"
            "2. Предоставить разрешения\n\n"
            "💡 После подключения AI сможет:\n"
            "• Анализировать входящие письма\n"
            "• Выделять важные темы\n"
            "• Давать рекомендации\n"
            "• Определять срочные письма",
            reply_markup=keyboards.back_button("menu_back"),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    try:
        # Показываем статус анализа
        await callback.message.edit_text(
            "🔍 <b>Анализирую входящие письма...</b>\n\n"
            "⏳ Загружаю последние письма...",
            parse_mode="HTML"
        )
        
        # Получаем последние 5 писем для анализа
        from utils.email_sender_real import real_email_sender
        emails = await real_email_sender.get_inbox_emails(user_id, limit=5)
        
        if not emails:
            await callback.message.edit_text(
                "🔍 <b>Анализ писем</b>\n\n"
                "📭 В папке «Входящие» нет писем для анализа\n\n"
                "💡 <b>Что можно сделать:</b>\n"
                "• Проверить другие папки\n"
                "• Подождать новых писем\n"
                "• Проверить настройки фильтров",
                reply_markup=keyboards.back_button("menu_back"),
                parse_mode="HTML"
            )
            await callback.answer()
            return
        
        # Обновляем статус
        await callback.message.edit_text(
            f"🔍 <b>Анализирую входящие письма...</b>\n\n"
            f"📧 Найдено писем: {len(emails)}\n"
            f"🤖 AI анализирует содержимое...",
            parse_mode="HTML"
        )
        
        # Запускаем анализ
        analysis = await email_analyzer.analyze_emails_summary(emails, user_name)
        insights = await email_analyzer.get_email_insights(emails)
        
        # Формируем финальный ответ
        result_text = f"🔍 <b>AI Анализ входящих писем</b>\n\n"
        result_text += analysis
        
        # Добавляем дополнительную статистику
        result_text += f"\n\n📊 <b>Дополнительная статистика:</b>\n"
        result_text += f"• Всего писем: {insights['total_emails']}\n"
        result_text += f"• Уникальных отправителей: {insights['unique_senders']}\n"
        
        if insights['urgent_count'] > 0:
            result_text += f"• ⚡ Срочных писем: {insights['urgent_count']}\n"
        
        spam_levels = {
            'low': '🟢 Низкий',
            'medium': '🟡 Средний', 
            'high': '🔴 Высокий'
        }
        result_text += f"• 🛡️ Уровень спама: {spam_levels.get(insights['spam_likelihood'], 'Неизвестно')}\n"
        
        result_text += "\n💡 <i>Анализ выполнен на основе последних писем</i>"
        
        await callback.message.edit_text(
            result_text,
            reply_markup=keyboards.inbox_menu(),
            parse_mode="HTML"
        )
        
    except Exception as e:
        await callback.message.edit_text(
            "❌ <b>Ошибка анализа писем</b>\n\n"
            f"💥 <b>Проблема:</b> {str(e)[:100]}...\n\n"
            "🔧 <b>Попробуйте:</b>\n"
            "• Перезагрузить страницу\n"
            "• Проверить подключение к интернету\n"
            "• Попробовать позже",
            reply_markup=keyboards.back_button("menu_back"),
            parse_mode="HTML"
        )
    
    await callback.answer()

@router.callback_query(F.data == "mail_folders")
async def mail_folders_callback(callback: CallbackQuery):
    """Папки почты (заглушка)"""
    await callback.answer("📂 Управление папками в разработке", show_alert=True)

@router.callback_query(F.data == "mail_labels")
async def mail_labels_callback(callback: CallbackQuery):
    """Метки почты (заглушка)"""
    await callback.answer("🏷️ Управление метками в разработке", show_alert=True)

# Дублирующий обработчик удален - используется обработчик в начале файла

# Правильный обработчик search_toggle_ находится ниже

@router.callback_query(F.data.startswith("search_toggle_"))
async def search_toggle_callback(callback: CallbackQuery):
    """Переключение настроек поиска"""
    user_id = callback.from_user.id
    setting = callback.data.replace("search_toggle_", "")
    
    # Загружаем настройки
    import json
    import os
    
    settings_dir = "data/search_settings"
    settings_file = os.path.join(settings_dir, f"user_{user_id}_search.json")
    
    default_settings = {
        'search_limit': 10,
        'content_analysis': False,
        'search_in_body': True,
        'search_in_attachments': False,
        'date_range_days': 365,
        'priority_search': False
    }
    
    current_settings = default_settings.copy()
    if os.path.exists(settings_file):
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                user_settings = json.load(f)
                current_settings.update(user_settings)
        except:
            pass
    
    # Переключаем настройку
    setting_map = {
        'body': 'search_in_body',
        'ai': 'content_analysis', 
        'attachments': 'search_in_attachments',
        'speed': 'priority_search'
    }
    
    if setting in setting_map:
        key = setting_map[setting]
        current_settings[key] = not current_settings[key]
        
        # Сохраняем
        try:
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(current_settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            await callback.answer(f"❌ Ошибка сохранения: {str(e)[:30]}...", show_alert=True)
            return
    
    # Обновляем интерфейс
    await settings_email_search_callback(callback)

@router.callback_query(F.data.startswith("search_setting_"))
async def search_setting_callback(callback: CallbackQuery):
    """Изменение числовых настроек поиска"""
    user_id = callback.from_user.id 
    setting = callback.data.replace("search_setting_", "")
    
    if setting == "limit":
        # Циклически изменяем лимит: 5 → 10 → 20 → 50 → 5
        limits = [5, 10, 20, 50]
        
        # Загружаем текущие настройки
        import json
        import os
        
        settings_dir = "data/search_settings"
        settings_file = os.path.join(settings_dir, f"user_{user_id}_search.json")
        
        current_limit = 10  # по умолчанию
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    user_settings = json.load(f)
                    current_limit = user_settings.get('search_limit', 10)
            except:
                pass
        
        # Находим следующий лимит
        try:
            current_index = limits.index(current_limit)
            new_limit = limits[(current_index + 1) % len(limits)]
        except ValueError:
            new_limit = limits[0]
        
        # Сохраняем новые настройки
        default_settings = {
            'search_limit': 10,
            'content_analysis': False,
            'search_in_body': True,
            'search_in_attachments': False,
            'date_range_days': 365,
            'priority_search': False
        }
        
        current_settings = default_settings.copy()
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    user_settings = json.load(f)
                    current_settings.update(user_settings)
            except:
                pass
        
        current_settings['search_limit'] = new_limit
        
        try:
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(current_settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            await callback.answer(f"❌ Ошибка сохранения: {str(e)[:30]}...", show_alert=True)
            return
    
    elif setting == "days":
        # Циклически изменяем диапазон: 30 → 90 → 180 → 365 → 30
        ranges = [30, 90, 180, 365]
        
        # Аналогично для диапазона дней
        import json
        import os
        
        settings_dir = "data/search_settings"
        settings_file = os.path.join(settings_dir, f"user_{user_id}_search.json")
        
        current_days = 365
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    user_settings = json.load(f)
                    current_days = user_settings.get('date_range_days', 365)
            except:
                pass
        
        try:
            current_index = ranges.index(current_days)
            new_days = ranges[(current_index + 1) % len(ranges)]
        except ValueError:
            new_days = ranges[0]
        
        # Загружаем и сохраняем
        default_settings = {
            'search_limit': 10,
            'content_analysis': False,
            'search_in_body': True,
            'search_in_attachments': False,
            'date_range_days': 365,
            'priority_search': False
        }
        
        current_settings = default_settings.copy()
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    user_settings = json.load(f)
                    current_settings.update(user_settings)
            except:
                pass
        
        current_settings['date_range_days'] = new_days
        
        try:
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(current_settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            await callback.answer(f"❌ Ошибка сохранения: {str(e)[:30]}...", show_alert=True)
            return
    
    # Обновляем интерфейс
    await settings_email_search_callback(callback)

@router.callback_query(F.data == "search_save_settings")
async def search_save_settings_callback(callback: CallbackQuery):
    """Сохранение настроек поиска"""
    await callback.answer("✅ Настройки поиска сохранены", show_alert=True)

@router.callback_query(F.data == "search_reset_settings")
async def search_reset_settings_callback(callback: CallbackQuery): 
    """Сброс настроек поиска к значениям по умолчанию"""
    user_id = callback.from_user.id
    
    import os
    
    settings_dir = "data/search_settings"
    settings_file = os.path.join(settings_dir, f"user_{user_id}_search.json")
    
    # Удаляем файл настроек (вернется к умолчанию)
    try:
        if os.path.exists(settings_file):
            os.remove(settings_file)
        await callback.answer("🔄 Настройки сброшены к значениям по умолчанию", show_alert=True)
    except Exception as e:
        await callback.answer(f"❌ Ошибка сброса: {str(e)[:30]}...", show_alert=True)
        return
    
    # Обновляем интерфейс
    await settings_email_search_callback(callback)

# Обработчики календаря
@router.callback_query(F.data == "calendar_connect")
async def calendar_connect_callback(callback: CallbackQuery, state: FSMContext):
    """Подключение календаря - перенаправление на полную реализацию"""
    # Импортируем handler из yandex_integration
    from handlers.yandex_integration import connect_calendar_handler
    
    # Вызываем полную реализацию подключения календаря
    await connect_calendar_handler(callback, state)

@router.callback_query(F.data == "calendar_today")
async def calendar_today_callback(callback: CallbackQuery):
    """Показать события на сегодня - перенаправление на полную реализацию"""
    # Импортируем handler из yandex_integration
    from handlers.yandex_integration import calendar_today_handler
    
    # Вызываем полную реализацию
    await calendar_today_handler(callback)

@router.callback_query(F.data == "calendar_week")
async def calendar_week_callback(callback: CallbackQuery):
    """Показать события на неделю - перенаправление на полную реализацию"""
    # Импортируем handler из yandex_integration
    from handlers.yandex_integration import calendar_week_handler
    
    # Вызываем полную реализацию
    await calendar_week_handler(callback)

@router.callback_query(F.data == "calendar_create")
async def calendar_create_callback(callback: CallbackQuery, state: FSMContext):
    """Создание события - перенаправление на полную реализацию"""
    # Импортируем handler из yandex_integration
    from handlers.yandex_integration import calendar_create_handler
    
    # Вызываем полную реализацию
    await calendar_create_handler(callback, state)

@router.callback_query(F.data == "calendar_sync_reminders")
async def calendar_sync_reminders_callback(callback: CallbackQuery):
    """Синхронизация с напоминаниями"""
    await callback.message.edit_text(
        "🔄 <b>Синхронизация с напоминаниями</b>\n\n"
        "🎯 <b>Возможности синхронизации:</b>\n"
        "• 📅 События календаря → ⏰ Напоминания\n"
        "• ⏰ Напоминания → 📅 События календаря\n"
        "• 🔄 Автоматическая двухсторонняя синхронизация\n"
        "• 📱 Уведомления на всех устройствах\n\n"
        "⚙️ <b>Настройки синхронизации:</b>\n"
        "• Время предупреждения: 15 минут\n"
        "• Повторяющиеся события: включено\n"
        "• Конфликты расписания: предупреждать\n\n"
        "🚧 <i>Функция в разработке</i>\n"
        "Скоро будет доступна полная синхронизация",
        reply_markup=keyboards.back_button("category_calendar"),
        parse_mode="HTML"
    )
    await callback.answer()

