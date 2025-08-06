from aiogram import Router, F
from aiogram.types import CallbackQuery
from utils.keyboards import keyboards

router = Router()

# Обработчики AI категории
@router.callback_query(F.data == "ai_chat_start")
async def ai_chat_start_callback(callback: CallbackQuery):
    """Начать чат с AI"""
    await callback.message.edit_text(
        "💬 <b>Чат с AI</b>\n\n"
        "🎯 <b>Как начать:</b>\n"
        "1. Закройте это меню\n"
        "2. Напишите любое сообщение\n"
        "3. Получите умный ответ от AI\n\n"
        "💡 <b>Примеры вопросов:</b>\n"
        "• «Расскажи о квантовой физике»\n"
        "• «Помоги написать код на Python»\n"
        "• «Объясни, как работает ChatGPT»\n"
        "• «Придумай идеи для стартапа»\n\n"
        "🤖 <i>AI готов помочь с любыми задачами!</i>",
        reply_markup=keyboards.back_button("category_ai"),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "ai_voice_mode")
async def ai_voice_mode_callback(callback: CallbackQuery):
    """Голосовой режим AI"""
    await callback.message.edit_text(
        "🎤 <b>Голосовой режим</b>\n\n"
        "🎯 <b>Как использовать:</b>\n"
        "1. Нажмите на микрофон в Telegram\n"
        "2. Запишите голосовое сообщение\n"
        "3. Отправьте боту\n\n"
        "✨ <b>Возможности:</b>\n"
        "• Распознавание речи на русском\n"
        "• Ответ голосом и текстом\n"
        "• Сохранение контекста разговора\n"
        "• Быстрые голосовые команды\n\n"
        "💡 <b>Совет:</b> Говорите четко и не слишком быстро",
        reply_markup=keyboards.back_button("category_ai"),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "ai_modes")
async def ai_modes_callback(callback: CallbackQuery):
    """Режимы работы AI"""
    await callback.message.edit_text(
        "🎨 <b>Режимы AI</b>\n\n"
        "🤖 <b>Доступные режимы:</b>\n\n"
        "💬 <b>Обычный чат</b>\n"
        "Стандартный режим для любых вопросов\n\n"
        "📝 <b>Помощник писателя</b>\n"
        "Помощь в написании текстов и статей\n\n"
        "💻 <b>Программист</b>\n"
        "Написание и отладка кода\n\n"
        "🎓 <b>Учитель</b>\n"
        "Объяснение сложных тем простым языком\n\n"
        "🏢 <b>Бизнес-консультант</b>\n"
        "Советы по бизнесу и маркетингу\n\n"
        "💡 <i>Для смены режима используйте команды в чате</i>",
        reply_markup=keyboards.back_button("category_ai"),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "ai_templates")
async def ai_templates_callback(callback: CallbackQuery):
    """Шаблоны для AI"""
    await callback.message.edit_text(
        "📝 <b>Шаблоны запросов</b>\n\n"
        "🎯 <b>Для написания текстов:</b>\n"
        "• «Напиши пост о [тема] для соцсетей»\n"
        "• «Создай статью про [тема] на 1000 слов»\n"
        "• «Придумай 10 заголовков для [тема]»\n\n"
        "💻 <b>Для программирования:</b>\n"
        "• «Напиши функцию на Python для [задача]»\n"
        "• «Найди ошибку в коде: [код]»\n"
        "• «Оптимизируй этот код: [код]»\n\n"
        "📚 <b>Для обучения:</b>\n"
        "• «Объясни простыми словами [тема]»\n"
        "• «Создай тест по [тема]»\n"
        "• «Составь план изучения [тема]»\n\n"
        "💡 <i>Используйте эти шаблоны для лучших результатов!</i>",
        reply_markup=keyboards.back_button("category_ai"),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "ai_history")
async def ai_history_callback(callback: CallbackQuery):
    """История чатов с AI"""
    await callback.message.edit_text(
        "🧠 <b>История чатов</b>\n\n"
        "📊 <b>Последние разговоры:</b>\n\n"
        "1️⃣ <b>Вчера, 15:30</b>\n"
        "💬 Обсуждение квантовой физики\n"
        "📝 15 сообщений\n\n"
        "2️⃣ <b>Вчера, 10:15</b>\n"
        "💻 Помощь с Python кодом\n"
        "📝 23 сообщения\n\n"
        "3️⃣ <b>Позавчера, 18:45</b>\n"
        "📚 Объяснение блокчейна\n"
        "📝 8 сообщений\n\n"
        "💡 <b>Совет:</b> AI помнит контекст всех разговоров\n\n"
        "🚧 <i>Полная история в разработке</i>",
        reply_markup=keyboards.back_button("category_ai"),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "ai_examples")
async def ai_examples_callback(callback: CallbackQuery):
    """Примеры использования AI"""
    await callback.message.edit_text(
        "💡 <b>Примеры использования</b>\n\n"
        "📚 <b>Образование:</b>\n"
        "• Решение задач по математике\n"
        "• Перевод текстов\n"
        "• Подготовка к экзаменам\n\n"
        "💼 <b>Работа:</b>\n"
        "• Написание отчетов\n"
        "• Генерация идей\n"
        "• Анализ данных\n\n"
        "🎨 <b>Творчество:</b>\n"
        "• Написание историй\n"
        "• Создание стихов\n"
        "• Придумывание названий\n\n"
        "🏠 <b>Повседневная жизнь:</b>\n"
        "• Составление списков\n"
        "• Планирование поездок\n"
        "• Поиск рецептов\n\n"
        "🤖 <i>AI может помочь практически с любой задачей!</i>",
        reply_markup=keyboards.back_button("category_ai"),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "quick_voice_record")
async def quick_voice_record_callback(callback: CallbackQuery):
    """Быстрая запись голоса"""
    await callback.message.edit_text(
        "🎤 <b>Голосовое сообщение</b>\n\n"
        "📱 <b>Инструкция:</b>\n"
        "1. Закройте это окно\n"
        "2. Нажмите на значок микрофона\n"
        "3. Удерживайте и говорите\n"
        "4. Отпустите для отправки\n\n"
        "🎯 <b>Что можно спросить голосом:</b>\n"
        "• Любые вопросы к AI\n"
        "• Команды для почты\n"
        "• Создание напоминаний\n"
        "• Поиск информации\n\n"
        "✨ <i>Бот распознает речь и ответит голосом!</i>",
        reply_markup=keyboards.back_button("menu_back"),
        parse_mode="HTML"
    )
    await callback.answer()

# Обработчики настроек профиля
@router.callback_query(F.data == "settings_profile")
async def settings_profile_callback(callback: CallbackQuery):
    """Настройки профиля"""
    user = callback.from_user
    await callback.message.edit_text(
        f"👤 <b>Профиль</b>\n\n"
        f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
        f"👤 <b>Имя:</b> {user.first_name}\n"
        f"📝 <b>Username:</b> @{user.username if user.username else 'не указан'}\n\n"
        "📊 <b>Статистика:</b>\n"
        "• Дата регистрации: 2025-01-27\n"
        "• Сообщений отправлено: 142\n"
        "• Голосовых сообщений: 23\n\n"
        "🚧 <i>Редактирование профиля в разработке</i>",
        reply_markup=keyboards.back_button("category_settings"),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "settings_privacy")
async def settings_privacy_callback(callback: CallbackQuery):
    """Настройки приватности"""
    await callback.message.edit_text(
        "🔐 <b>Приватность</b>\n\n"
        "🛡️ <b>Текущие настройки:</b>\n"
        "• Сохранение истории: ✅ Включено\n"
        "• Анализ сообщений: ✅ Включен\n"
        "• Векторная память: ✅ Активна\n"
        "• Шифрование: 🔒 AES-256\n\n"
        "📊 <b>Данные:</b>\n"
        "• Хранение: Локально + облако\n"
        "• Срок хранения: 90 дней\n"
        "• Удаление: По запросу\n\n"
        "🚧 <i>Настройка приватности в разработке</i>",
        reply_markup=keyboards.back_button("category_settings"),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "settings_about")
async def settings_about_callback(callback: CallbackQuery):
    """О боте"""
    await callback.message.edit_text(
        "📱 <b>О боте</b>\n\n"
        "🤖 <b>AI Assistant Bot</b>\n"
        "Версия: 2.0.1\n"
        "Обновлено: 03.08.2025\n\n"
        "🛠️ <b>Технологии:</b>\n"
        "• AI: ChatGPT-4\n"
        "• Голос: Whisper + TTS\n"
        "• База: PostgreSQL\n"
        "• Память: Векторная БД\n\n"
        "👨‍💻 <b>Разработчик:</b>\n"
        "@ai_assistant_support\n\n"
        "📄 <b>Лицензия:</b> MIT\n"
        "🌐 <b>Сайт:</b> ai-assistant.bot",
        reply_markup=keyboards.back_button("category_settings"),
        parse_mode="HTML"
    )
    await callback.answer()