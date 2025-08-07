from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from datetime import datetime

class BotKeyboards:
    """Клавиатуры для бота"""
    
    @staticmethod
    def main_menu() -> ReplyKeyboardMarkup:
        """Главное меню с кнопкой"""
        builder = ReplyKeyboardBuilder()
        
        # Одна кнопка для открытия меню
        builder.add(KeyboardButton(text="📱 Меню"))
        
        return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)
    
    @staticmethod
    def full_menu() -> InlineKeyboardMarkup:
        """Главное меню с категориями"""
        builder = InlineKeyboardBuilder()
        
        # Основные категории - крупные кнопки
        builder.add(
            InlineKeyboardButton(text="📧 Почта", callback_data="category_mail"),
            InlineKeyboardButton(text="📅 Календарь", callback_data="category_calendar")
        )
        
        builder.add(
            InlineKeyboardButton(text="⏰ Напоминания", callback_data="reminders_menu"),
            InlineKeyboardButton(text="👥 Контакты", callback_data="contacts_menu")
        )
        
        builder.add(
            InlineKeyboardButton(text="🧠 Память", callback_data="category_memory"),
            InlineKeyboardButton(text="💬 AI Помощник", callback_data="category_ai")
        )
        
        builder.add(
            InlineKeyboardButton(text="🌐 Веб-поиск", callback_data="web_search"),
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="category_settings")
        )
        
        builder.add(
            InlineKeyboardButton(text="❓ Помощь", callback_data="help_menu")
        )
        
        # Закрыть меню
        builder.add(InlineKeyboardButton(text="❌ Закрыть меню", callback_data="close_menu"))
        
        builder.adjust(2, 2, 2, 2, 1, 1)
        return builder.as_markup()
    
    @staticmethod
    def memory_menu() -> InlineKeyboardMarkup:
        """Меню управления памятью"""
        builder = InlineKeyboardBuilder()
        
        builder.add(
            InlineKeyboardButton(text="📊 Статистика", callback_data="memory_stats"),
            InlineKeyboardButton(text="🔍 Поиск", callback_data="memory_search"),
            InlineKeyboardButton(text="💾 Сохранить знания", callback_data="memory_save"),
            InlineKeyboardButton(text="🗑️ Очистить память", callback_data="memory_clear"),
            InlineKeyboardButton(text="❓ Справка", callback_data="memory_help"),
            InlineKeyboardButton(text="◀️ Назад в меню", callback_data="menu_back")
        )
        
        builder.adjust(2, 2, 1, 1)
        return builder.as_markup()
    
    @staticmethod
    def mail_menu() -> InlineKeyboardMarkup:
        """Категория: Почта"""
        builder = InlineKeyboardBuilder()
        
        # Главные функции почты
        builder.add(
            InlineKeyboardButton(text="📨 Входящие письма", callback_data="mail_inbox"),
            InlineKeyboardButton(text="✍️ Написать письмо", callback_data="mail_compose")
        )
        
        builder.add(
            InlineKeyboardButton(text="📋 Черновики", callback_data="mail_drafts"),
            InlineKeyboardButton(text="🔍 Поиск писем", callback_data="mail_search")
        )
        
        builder.add(
            InlineKeyboardButton(text="📂 Папки", callback_data="mail_folders"),
            InlineKeyboardButton(text="🏷️ Метки", callback_data="mail_labels")
        )
        
        # Настройка почты
        builder.add(
            InlineKeyboardButton(text="🔗 Подключить почту", callback_data="connect_yandex_mail")
        )
        
        # Назад
        builder.add(
            InlineKeyboardButton(text="◀️ Главное меню", callback_data="menu_back")
        )
        
        builder.adjust(2, 2, 2, 1, 1)
        return builder.as_markup()
    
    @staticmethod
    def calendar_menu(user_id: int = None, auto_sync_enabled: bool = False) -> InlineKeyboardMarkup:
        """Меню календаря"""
        builder = InlineKeyboardBuilder()
        
        builder.add(
            InlineKeyboardButton(text="📅 Сегодня", callback_data="calendar_today"),
            InlineKeyboardButton(text="📆 Неделя", callback_data="calendar_week")
        )
        
        builder.add(
            InlineKeyboardButton(text="➕ Создать событие", callback_data="calendar_create"),
            InlineKeyboardButton(text="🔗 Подключить календарь", callback_data="calendar_connect")
        )
        
        # Кнопка автосинхронизации с индикатором состояния
        sync_icon = "✅" if auto_sync_enabled else "❌"
        sync_text = f"🔄 Автосинхронизация: {sync_icon}"
        builder.add(
            InlineKeyboardButton(text=sync_text, callback_data="calendar_toggle_sync")
        )
        
        builder.add(
            InlineKeyboardButton(text="◀️ Назад в меню", callback_data="menu_back")
        )
        
        builder.adjust(2, 2, 1, 1)
        return builder.as_markup()
    
    @staticmethod
    def settings_menu() -> InlineKeyboardMarkup:
        """Меню настроек"""
        builder = InlineKeyboardBuilder()
        
        builder.add(
            InlineKeyboardButton(text="🎤 Голосовые сообщения", callback_data="settings_voice"),
            InlineKeyboardButton(text="🧠 Векторная память", callback_data="settings_vector"),
            InlineKeyboardButton(text="🔔 Уведомления", callback_data="settings_notifications"),
            InlineKeyboardButton(text="🌐 Язык", callback_data="settings_language"),
            InlineKeyboardButton(text="◀️ Назад в меню", callback_data="menu_back")
        )
        
        builder.adjust(2, 2, 1, 1)
        return builder.as_markup()
    
    @staticmethod
    def voice_mode_menu() -> InlineKeyboardMarkup:
        """Меню голосового режима"""
        builder = InlineKeyboardBuilder()
        
        builder.add(
            InlineKeyboardButton(text="🎙️ Записать сообщение", callback_data="voice_record"),
            InlineKeyboardButton(text="🔊 Последний ответ", callback_data="voice_last_response"),
            InlineKeyboardButton(text="⚙️ Настройки голоса", callback_data="voice_settings"),
            InlineKeyboardButton(text="◀️ Назад в меню", callback_data="menu_back")
        )
        
        builder.adjust(2, 1, 1)
        return builder.as_markup()
    
    @staticmethod
    def confirm_action(action: str, action_data: str) -> InlineKeyboardMarkup:
        """Подтверждение действия"""
        builder = InlineKeyboardBuilder()
        
        builder.add(
            InlineKeyboardButton(text="✅ Да", callback_data=f"confirm_{action_data}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def yandex_connect_menu() -> InlineKeyboardMarkup:
        """Меню подключения Яндекс сервисов"""
        builder = InlineKeyboardBuilder()
        
        builder.add(
            InlineKeyboardButton(text="📧 Подключить Почту", callback_data="connect_yandex_mail"),
            InlineKeyboardButton(text="📅 Подключить Календарь", callback_data="connect_yandex_calendar"),
            InlineKeyboardButton(text="❓ Что это даст?", callback_data="yandex_benefits"),
            InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")
        )
        
        builder.adjust(2, 1, 1)
        return builder.as_markup()
    
    @staticmethod
    def back_button(callback_data: str = "main_menu") -> InlineKeyboardMarkup:
        """Простая кнопка назад"""
        builder = InlineKeyboardBuilder()
        
        if callback_data == "menu_back":
            builder.add(InlineKeyboardButton(text="◀️ Назад в меню", callback_data="menu_back"))
        else:
            builder.add(InlineKeyboardButton(text="◀️ Назад", callback_data=callback_data))
        
        return builder.as_markup()
    
    @staticmethod
    def inbox_menu() -> InlineKeyboardMarkup:
        """Меню для входящих писем с кнопкой анализа"""
        builder = InlineKeyboardBuilder()
        
        builder.add(
            InlineKeyboardButton(text="🔍 Проанализировать", callback_data="mail_analyze_inbox")
        )
        builder.add(
            InlineKeyboardButton(text="◀️ Назад в меню", callback_data="menu_back")
        )
        
        builder.adjust(1, 1)
        return builder.as_markup()
    
    @staticmethod
    def create_cancel_button(callback_data: str = "cancel_operation") -> InlineKeyboardMarkup:
        """Кнопка отмены операции"""
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="❌ Отменить", callback_data=callback_data))
        return builder.as_markup()
    
    @staticmethod
    def quick_actions() -> InlineKeyboardMarkup:
        """Быстрые действия для AI ответов"""
        print(f"DEBUG: Creating quick_actions keyboard")
        builder = InlineKeyboardBuilder()
        
        builder.add(
            InlineKeyboardButton(text="🎤 Озвучить", callback_data="quick_voice"),
            InlineKeyboardButton(text="💾 Сохранить", callback_data="quick_save"),
            InlineKeyboardButton(text="🔄 Переспросить", callback_data="quick_retry"),
            InlineKeyboardButton(text="➕ Подробнее", callback_data="quick_more")
        )
        
        builder.adjust(2, 2)
        markup = builder.as_markup()
        print(f"DEBUG: Quick actions keyboard created with {len(markup.inline_keyboard)} rows")
        return markup
    
    @staticmethod
    def mail_compose_menu() -> InlineKeyboardMarkup:
        """Меню создания письма"""
        builder = InlineKeyboardBuilder()
        
        builder.add(
            InlineKeyboardButton(text="✅ Отправить", callback_data="mail_send"),
            InlineKeyboardButton(text="💾 Сохранить в черновики", callback_data="mail_save_draft"),
            InlineKeyboardButton(text="🗑️ Удалить", callback_data="mail_delete"),
            InlineKeyboardButton(text="◀️ К почте", callback_data="mail_menu")
        )
        
        builder.adjust(2, 1, 1)
        return builder.as_markup()
    
    @staticmethod
    def email_confirm_menu(email_id: str) -> InlineKeyboardMarkup:
        """Меню подтверждения отправки письма"""
        builder = InlineKeyboardBuilder()
        
        builder.add(
            InlineKeyboardButton(text="✅ Отправить", callback_data=f"email_send_{email_id}"),
            InlineKeyboardButton(text="🤖 Улучшить письмо", callback_data=f"email_improve_{email_id}")
        )
        
        builder.add(
            InlineKeyboardButton(text="🧠 Дополнить AI", callback_data=f"email_expand_{email_id}"),
            InlineKeyboardButton(text="✏️ Редактировать тему", callback_data=f"email_edit_subject_{email_id}")
        )
        
        builder.add(
            InlineKeyboardButton(text="📝 Редактировать текст", callback_data=f"email_edit_body_{email_id}")
        )
        
        builder.add(
            InlineKeyboardButton(text="💾 Сохранить в черновики", callback_data=f"email_save_draft_{email_id}"),
            InlineKeyboardButton(text="❌ Отменить", callback_data=f"email_cancel_{email_id}")
        )
        
        builder.adjust(2, 2, 2)
        return builder.as_markup()
    
    @staticmethod
    def calendar_event_menu() -> InlineKeyboardMarkup:
        """Меню создания события"""
        builder = InlineKeyboardBuilder()
        
        builder.add(
            InlineKeyboardButton(text="✅ Создать", callback_data="calendar_event_create"),
            InlineKeyboardButton(text="🔔 Добавить напоминание", callback_data="calendar_event_reminder"),
            InlineKeyboardButton(text="👥 Пригласить участников", callback_data="calendar_event_invite"),
            InlineKeyboardButton(text="◀️ К календарю", callback_data="calendar_menu")
        )
        
        builder.adjust(2, 1, 1)
        return builder.as_markup()

    @staticmethod
    def ai_menu() -> InlineKeyboardMarkup:
        """Категория: AI Помощник"""
        builder = InlineKeyboardBuilder()
        
        builder.add(
            InlineKeyboardButton(text="💬 Начать чат", callback_data="ai_chat_start"),
            InlineKeyboardButton(text="🎤 Голосовой режим", callback_data="ai_voice_mode")
        )
        
        builder.add(
            InlineKeyboardButton(text="🎨 Режимы AI", callback_data="ai_modes"),
            InlineKeyboardButton(text="📝 Шаблоны", callback_data="ai_templates")
        )
        
        builder.add(
            InlineKeyboardButton(text="🧠 История чатов", callback_data="ai_history"),
            InlineKeyboardButton(text="💡 Примеры использования", callback_data="ai_examples")
        )
        
        builder.add(
            InlineKeyboardButton(text="◀️ Главное меню", callback_data="menu_back")
        )
        
        builder.adjust(2, 2, 2, 1)
        return builder.as_markup()
    
    @staticmethod
    def category_memory_menu() -> InlineKeyboardMarkup:
        """Категория: Память"""
        builder = InlineKeyboardBuilder()
        
        builder.add(
            InlineKeyboardButton(text="📊 Статистика памяти", callback_data="memory_stats"),
            InlineKeyboardButton(text="🔍 Поиск в памяти", callback_data="memory_search")
        )
        
        builder.add(
            InlineKeyboardButton(text="💾 Сохранить знания", callback_data="memory_save"),
            InlineKeyboardButton(text="📚 База знаний", callback_data="memory_knowledge")
        )
        
        builder.add(
            InlineKeyboardButton(text="🗂️ Управление памятью", callback_data="memory_manage"),
            InlineKeyboardButton(text="❓ Как это работает", callback_data="memory_help")
        )
        
        builder.add(
            InlineKeyboardButton(text="◀️ Главное меню", callback_data="menu_back")
        )
        
        builder.adjust(2, 2, 2, 1)
        return builder.as_markup()
    
    @staticmethod
    def category_settings_menu() -> InlineKeyboardMarkup:
        """Категория: Настройки"""
        builder = InlineKeyboardBuilder()
        
        builder.add(
            InlineKeyboardButton(text="👤 Профиль", callback_data="settings_profile"),
            InlineKeyboardButton(text="🔔 Уведомления", callback_data="settings_notifications")
        )
        
        builder.add(
            InlineKeyboardButton(text="🎤 Голос и звук", callback_data="settings_voice"),
            InlineKeyboardButton(text="🌐 Язык", callback_data="settings_language")
        )
        
        
        builder.add(
            InlineKeyboardButton(text="🧠 Векторная память", callback_data="settings_vector"),
            InlineKeyboardButton(text="🔍 Поиск писем", callback_data="settings_email_search")
        )
        
        builder.add(
            InlineKeyboardButton(text="📱 О боте", callback_data="settings_about")
        )
        
        builder.add(
            InlineKeyboardButton(text="◀️ Главное меню", callback_data="menu_back")
        )
        
        builder.adjust(2, 2, 2, 1, 1)
        return builder.as_markup()
    
    @staticmethod
    def error_menu() -> InlineKeyboardMarkup:
        """Меню для ошибок"""
        builder = InlineKeyboardBuilder()
        
        builder.add(
            InlineKeyboardButton(text="🔄 Попробовать снова", callback_data="retry_action"),
            InlineKeyboardButton(text="❓ Помощь", callback_data="help_menu"),
            InlineKeyboardButton(text="◀️ Главное меню", callback_data="menu_back")
        )
        
        builder.adjust(1, 1, 1)
        return builder.as_markup()
    
    @staticmethod
    def web_search_menu() -> InlineKeyboardMarkup:
        """Меню веб-поиска"""
        builder = InlineKeyboardBuilder()
        
        builder.add(
            InlineKeyboardButton(text="🔍 Обычный поиск", callback_data="web_search_general"),
            InlineKeyboardButton(text="📰 Поиск новостей", callback_data="web_search_news")
        )
        
        builder.add(
            InlineKeyboardButton(text="💡 Умный поиск", callback_data="web_search_smart")
        )
        
        builder.add(
            InlineKeyboardButton(text="◀️ Главное меню", callback_data="menu_back")
        )
        
        builder.adjust(2, 1, 1)
        return builder.as_markup()
    
    @staticmethod
    def search_results_menu() -> InlineKeyboardMarkup:
        """Меню для результатов поиска"""
        builder = InlineKeyboardBuilder()
        
        builder.add(
            InlineKeyboardButton(text="🧠 Проанализировать", callback_data="analyze_news"),
            InlineKeyboardButton(text="🔍 Новый поиск", callback_data="search_new_query")
        )
        
        builder.add(
            InlineKeyboardButton(text="🏠 В меню", callback_data="search_to_menu")
        )
        
        builder.adjust(2, 1)
        return builder.as_markup()
    
    @staticmethod
    def create_cancel_button(back_callback: str = "menu_back") -> InlineKeyboardMarkup:
        """Кнопка отмены для веб-поиска"""
        builder = InlineKeyboardBuilder()
        
        builder.add(
            InlineKeyboardButton(text="❌ Отмена", callback_data=back_callback)
        )
        
        return builder.as_markup()

class ReminderKeyboards:
    """Клавиатуры для напоминаний"""
    
    @staticmethod
    def reminder_menu() -> InlineKeyboardMarkup:
        """Главное меню напоминаний"""
        builder = InlineKeyboardBuilder()
        
        builder.add(
            InlineKeyboardButton(text="➕ Создать напоминание", callback_data="reminder_create"),
            InlineKeyboardButton(text="📋 Мои напоминания", callback_data="reminder_list")
        )
        
        builder.add(
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="reminder_settings"),
            InlineKeyboardButton(text="📊 Статистика", callback_data="reminder_stats")
        )
        
        builder.add(
            InlineKeyboardButton(text="◀️ Главное меню", callback_data="menu_back")
        )
        
        builder.adjust(2, 2, 1)
        return builder.as_markup()
    
    @staticmethod
    def quick_time_buttons() -> InlineKeyboardMarkup:
        """Быстрые кнопки выбора времени"""
        builder = InlineKeyboardBuilder()
        
        builder.add(
            InlineKeyboardButton(text="⏱️ Через 15 минут", callback_data="quick_time_15min"),
            InlineKeyboardButton(text="⏱️ Через 30 минут", callback_data="quick_time_30min")
        )
        
        builder.add(
            InlineKeyboardButton(text="⏱️ Через 1 час", callback_data="quick_time_1hour"),
            InlineKeyboardButton(text="⏱️ Через 3 часа", callback_data="quick_time_3hours")
        )
        
        builder.add(
            InlineKeyboardButton(text="📅 Завтра в 9:00", callback_data="quick_time_tomorrow"),
            InlineKeyboardButton(text="🌆 Завтра в 18:00", callback_data="quick_time_tomorrow_evening")
        )
        
        builder.adjust(2, 2, 2)
        return builder.as_markup()
    
    @staticmethod
    def repeat_options() -> InlineKeyboardMarkup:
        """Опции повторения напоминания"""
        builder = InlineKeyboardBuilder()
        
        builder.add(
            InlineKeyboardButton(text="❌ Без повторения", callback_data="repeat_none"),
            InlineKeyboardButton(text="📅 Ежедневно", callback_data="repeat_daily")
        )
        
        builder.add(
            InlineKeyboardButton(text="📆 Еженедельно", callback_data="repeat_weekly"),
            InlineKeyboardButton(text="🗓️ Ежемесячно", callback_data="repeat_monthly")
        )
        
        builder.add(
            InlineKeyboardButton(text="🎊 Ежегодно", callback_data="repeat_yearly")
        )
        
        builder.adjust(2, 2, 1)
        return builder.as_markup()
    
    @staticmethod
    def back_to_reminders() -> InlineKeyboardMarkup:
        """Кнопка возврата к меню напоминаний"""
        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(text="◀️ К напоминаниям", callback_data="reminders_menu")
        )
        return builder.as_markup()
    
    @staticmethod
    def empty_list_menu() -> InlineKeyboardMarkup:
        """Меню для пустого списка напоминаний"""
        builder = InlineKeyboardBuilder()
        
        builder.add(
            InlineKeyboardButton(text="➕ Создать первое напоминание", callback_data="reminder_create")
        )
        
        builder.add(
            InlineKeyboardButton(text="◀️ Назад", callback_data="reminders_menu")
        )
        
        builder.adjust(1, 1)
        return builder.as_markup()
    
    @staticmethod
    def reminders_list_menu(reminders: list) -> InlineKeyboardMarkup:
        """Меню списка напоминаний"""
        builder = InlineKeyboardBuilder()
        
        # Добавляем кнопки для каждого напоминания
        for reminder in reminders[:5]:
            builder.add(
                InlineKeyboardButton(
                    text=f"📌 {reminder['title'][:30]}...",
                    callback_data=f"reminder_view_{reminder['id']}"
                )
            )
        
        builder.add(
            InlineKeyboardButton(text="➕ Создать новое", callback_data="reminder_create"),
            InlineKeyboardButton(text="◀️ Назад", callback_data="reminders_menu")
        )
        
        builder.adjust(1, 1, 1, 1, 1, 2)
        return builder.as_markup()
    
    @staticmethod
    def reminder_actions(reminder_id: int) -> InlineKeyboardMarkup:
        """Действия с напоминанием"""
        builder = InlineKeyboardBuilder()
        
        builder.add(
            InlineKeyboardButton(text="✅ Выполнено", callback_data=f"reminder_complete_{reminder_id}"),
            InlineKeyboardButton(text="✏️ Изменить", callback_data=f"reminder_edit_{reminder_id}")
        )
        
        builder.add(
            InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"reminder_delete_{reminder_id}")
        )
        
        builder.add(
            InlineKeyboardButton(text="◀️ К списку", callback_data="reminder_list"),
            InlineKeyboardButton(text="🏠 В меню", callback_data="reminders_menu")
        )
        
        builder.adjust(2, 1, 2)
        return builder.as_markup()
    
    @staticmethod
    def settings_menu(settings: dict) -> InlineKeyboardMarkup:
        """Меню настроек напоминаний"""
        builder = InlineKeyboardBuilder()
        
        # Переключатели настроек
        enabled_icon = "✅" if settings.get('enabled', True) else "❌"
        sound_icon = "✅" if settings.get('sound_enabled', True) else "❌"
        notify_at_event_icon = "✅" if settings.get('notify_at_event', False) else "❌"
        
        builder.add(
            InlineKeyboardButton(
                text=f"🔔 Напоминания: {enabled_icon}",
                callback_data="setting_toggle_enabled"
            )
        )
        
        builder.add(
            InlineKeyboardButton(
                text=f"🔊 Звук: {sound_icon}",
                callback_data="setting_toggle_sound_enabled"
            )
        )
        
        builder.add(
            InlineKeyboardButton(
                text=f"📅 Уведомлять в момент события: {notify_at_event_icon}",
                callback_data="setting_toggle_notify_at_event"
            )
        )
        
        # Настройки времени
        advance_time = settings.get('advance_time', 15)
        timezone = settings.get('timezone', 'Europe/Moscow').replace('Europe/', '').replace('_', ' ')
        
        builder.add(
            InlineKeyboardButton(text=f"⏱️ За {advance_time} мин", callback_data="setting_advance_time"),
            InlineKeyboardButton(text=f"🕐 {timezone}", callback_data="setting_timezone")
        )
        
        builder.add(
            InlineKeyboardButton(text="◀️ Назад", callback_data="reminders_menu")
        )
        
        builder.adjust(1, 1, 1, 2, 1)
        return builder.as_markup()
    
    @staticmethod
    def advance_time_menu() -> InlineKeyboardMarkup:
        """Меню выбора времени предварительного напоминания"""
        builder = InlineKeyboardBuilder()
        
        builder.add(
            InlineKeyboardButton(text="5 минут", callback_data="advance_5"),
            InlineKeyboardButton(text="10 минут", callback_data="advance_10"),
            InlineKeyboardButton(text="15 минут", callback_data="advance_15")
        )
        
        builder.add(
            InlineKeyboardButton(text="30 минут", callback_data="advance_30"),
            InlineKeyboardButton(text="1 час", callback_data="advance_60"),
            InlineKeyboardButton(text="2 часа", callback_data="advance_120")
        )
        
        builder.add(
            InlineKeyboardButton(text="1 день", callback_data="advance_1440")
        )
        
        builder.add(
            InlineKeyboardButton(text="◀️ Назад", callback_data="reminder_settings")
        )
        
        builder.adjust(3, 3, 1, 1)
        return builder.as_markup()
    
    @staticmethod
    def timezone_menu() -> InlineKeyboardMarkup:
        """Меню выбора часового пояса"""
        builder = InlineKeyboardBuilder()
        
        # Основные часовые пояса
        timezones = [
            ("🇷🇺 Москва (UTC+3)", "Europe/Moscow"),
            ("🇷🇺 СПб (UTC+3)", "Europe/Moscow"),
            ("🇷🇺 Екатеринбург (UTC+5)", "Asia/Yekaterinburg"),
            ("🇷🇺 Новосибирск (UTC+7)", "Asia/Novosibirsk"),
            ("🇷🇺 Красноярск (UTC+7)", "Asia/Krasnoyarsk"),
            ("🇷🇺 Иркутск (UTC+8)", "Asia/Irkutsk"),
            ("🇷🇺 Владивосток (UTC+10)", "Asia/Vladivostok"),
            ("🇺🇦 Киев (UTC+2)", "Europe/Kiev"),
            ("🇰🇿 Алматы (UTC+6)", "Asia/Almaty"),
            ("🇧🇾 Минск (UTC+3)", "Europe/Minsk")
        ]
        
        for name, tz in timezones:
            builder.add(
                InlineKeyboardButton(text=name, callback_data=f"tz_{tz}")
            )
        
        builder.add(
            InlineKeyboardButton(text="◀️ Назад", callback_data="reminder_settings")
        )
        
        builder.adjust(1)
        return builder.as_markup()
    
    @staticmethod
    def calendar_events_menu(events: list, back_to_calendar: bool = True) -> InlineKeyboardMarkup:
        """Меню со списком событий календаря"""
        builder = InlineKeyboardBuilder()
        
        # Добавляем кликабельные события (максимум 8)
        for i, event in enumerate(events[:8]):
            # Безопасно получаем ID события
            event_id = str(event.get('id', event.get('uid', f'event_{i}')))
            title = str(event.get('summary', 'Без названия'))[:25]  # Ограничиваем длину
            
            # Добавляем время если есть
            start = event.get('start', {})
            start_time = start.get('dateTime', '') if isinstance(start, dict) else ''
            
            if start_time:
                try:
                    # Убираем временную зону и парсим
                    clean_time = start_time.replace("Z", "+00:00")
                    event_time = datetime.fromisoformat(clean_time)
                    time_str = event_time.strftime("%H:%M")
                    button_text = f"🗓️ {time_str} - {title}"
                except Exception as e:
                    print(f"Error parsing time {start_time}: {e}")
                    button_text = f"🗓️ {title}"
            else:
                button_text = f"🗓️ {title}"
                
            # Убеждаемся что callback_data не слишком длинный
            safe_event_id = event_id[:30]  # Ограничиваем длину ID
            
            builder.add(
                InlineKeyboardButton(text=button_text, callback_data=f"calendar_event_{safe_event_id}")
            )
        
        # Кнопка назад
        if back_to_calendar:
            builder.add(
                InlineKeyboardButton(text="◀️ К календарю", callback_data="category_calendar")
            )
        else:
            builder.add(
                InlineKeyboardButton(text="◀️ В меню", callback_data="menu_back")
            )
        
        # Настраиваем layout: по одному событию в ряду, кнопка назад отдельно
        builder.adjust(1)  # Все кнопки в один столбец
        return builder.as_markup()
    
    @staticmethod
    def calendar_event_actions(event_id: str) -> InlineKeyboardMarkup:
        """Меню действий с конкретным событием"""
        builder = InlineKeyboardBuilder()
        
        builder.add(
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"calendar_edit_{event_id}"),
            InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"calendar_delete_{event_id}")
        )
        
        builder.add(
            InlineKeyboardButton(text="🧠 Дополнить AI", callback_data=f"calendar_expand_{event_id}")
        )
        
        builder.add(
            InlineKeyboardButton(text="◀️ К событиям", callback_data="calendar_today"),
            InlineKeyboardButton(text="🏠 К календарю", callback_data="category_calendar")
        )
        
        builder.adjust(2, 1, 2)
        return builder.as_markup()

keyboards = BotKeyboards()