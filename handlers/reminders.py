"""
Обработчик напоминаний для Telegram бота
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta
import re
import logging
from typing import Optional
from database.reminders import ReminderDB
from utils.keyboards import ReminderKeyboards

logger = logging.getLogger(__name__)

router = Router()

# Состояния для создания напоминания
class ReminderStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_time = State()
    waiting_for_repeat = State()
    editing_reminder = State()
    waiting_for_default_time = State()  # Для настройки времени по умолчанию

# Инициализация компонентов
reminder_db = ReminderDB()
keyboards = ReminderKeyboards()

@router.message(Command("reminder", "напоминание"))
async def reminder_command(message: Message):
    """Команда для управления напоминаниями"""
    user_id = message.from_user.id
    
    # Получаем статистику напоминаний
    stats = await reminder_db.get_user_stats(user_id)
    
    text = "⏰ <b>Управление напоминаниями</b>\n\n"
    text += f"📊 <b>Ваша статистика:</b>\n"
    text += f"• Активных напоминаний: {stats.get('active_reminders', 0)}\n"
    text += f"• Выполнено: {stats.get('completed_reminders', 0)}\n"
    text += f"• Сегодня: {stats.get('upcoming_today', 0)}\n"
    text += f"• На этой неделе: {stats.get('upcoming_week', 0)}\n\n"
    text += "Выберите действие:"
    
    await message.answer(
        text,
        reply_markup=keyboards.reminder_menu(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "reminders_menu")
async def reminders_menu_callback(callback: CallbackQuery):
    """Показать меню напоминаний"""
    user_id = callback.from_user.id
    
    stats = await reminder_db.get_user_stats(user_id)
    
    text = "⏰ <b>Напоминания</b>\n\n"
    text += f"📊 <b>Статистика:</b>\n"
    text += f"• Активных: {stats.get('active_reminders', 0)}\n"
    text += f"• Сегодня: {stats.get('upcoming_today', 0)}\n\n"
    text += "Выберите действие:"
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboards.reminder_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "reminder_create")
async def create_reminder_start(callback: CallbackQuery, state: FSMContext):
    """Начало создания напоминания"""
    await callback.message.edit_text(
        "📝 <b>Создание напоминания</b>\n\n"
        "Введите название напоминания:\n"
        "<i>Например: Встреча с клиентом</i>",
        parse_mode="HTML"
    )
    await state.set_state(ReminderStates.waiting_for_title)
    await callback.answer()

@router.message(ReminderStates.waiting_for_title)
async def process_reminder_title(message: Message, state: FSMContext):
    """Обработка названия напоминания"""
    await state.update_data(title=message.text)
    
    await message.answer(
        "📝 <b>Описание (необязательно)</b>\n\n"
        "Введите описание напоминания или нажмите /skip чтобы пропустить:",
        parse_mode="HTML"
    )
    await state.set_state(ReminderStates.waiting_for_description)

@router.message(ReminderStates.waiting_for_description)
async def process_reminder_description(message: Message, state: FSMContext):
    """Обработка описания напоминания"""
    if message.text != "/skip":
        await state.update_data(description=message.text)
    else:
        await state.update_data(description=None)
    
    await message.answer(
        "⏰ <b>Время напоминания</b>\n\n"
        "Когда напомнить? Введите время в одном из форматов:\n\n"
        "• <code>через 30 минут</code>\n"
        "• <code>завтра в 14:00</code>\n"
        "• <code>25.12 в 10:30</code>\n"
        "• <code>25.12.2024 15:00</code>\n"
        "• <code>каждый день в 9:00</code>",
        parse_mode="HTML",
        reply_markup=keyboards.quick_time_buttons()
    )
    await state.set_state(ReminderStates.waiting_for_time)

@router.callback_query(F.data.startswith("quick_time_"))
async def process_quick_time(callback: CallbackQuery, state: FSMContext):
    """Обработка быстрых кнопок времени"""
    time_option = callback.data.replace("quick_time_", "")
    
    now = datetime.now()
    reminder_time = None
    repeat_type = "none"
    
    if time_option == "15min":
        reminder_time = now + timedelta(minutes=15)
    elif time_option == "30min":
        reminder_time = now + timedelta(minutes=30)
    elif time_option == "1hour":
        reminder_time = now + timedelta(hours=1)
    elif time_option == "3hours":
        reminder_time = now + timedelta(hours=3)
    elif time_option == "tomorrow":
        reminder_time = now.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)
    elif time_option == "tomorrow_evening":
        reminder_time = now.replace(hour=18, minute=0, second=0, microsecond=0) + timedelta(days=1)
    
    if reminder_time:
        await state.update_data(
            remind_at=reminder_time,
            repeat_type=repeat_type
        )
        await save_reminder(callback.message, state, callback.from_user.id)
        await callback.answer()

@router.message(ReminderStates.waiting_for_time)
async def process_reminder_time(message: Message, state: FSMContext):
    """Обработка времени напоминания"""
    time_text = message.text.lower()
    reminder_time = None
    repeat_type = "none"
    
    try:
        # Парсинг различных форматов времени
        if "через" in time_text:
            # Формат: через X минут/часов
            match = re.search(r'через\s+(\d+)\s*(минут|час|день|дн)', time_text)
            if match:
                amount = int(match.group(1))
                unit = match.group(2)
                now = datetime.now()
                
                if "минут" in unit:
                    reminder_time = now + timedelta(minutes=amount)
                elif "час" in unit:
                    reminder_time = now + timedelta(hours=amount)
                elif "дн" in unit or "день" in unit:
                    reminder_time = now + timedelta(days=amount)
        
        elif "каждый день" in time_text:
            # Ежедневное напоминание
            match = re.search(r'(\d{1,2}):(\d{2})', time_text)
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2))
                reminder_time = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
                if reminder_time < datetime.now():
                    reminder_time += timedelta(days=1)
                repeat_type = "daily"
        
        elif "завтра" in time_text:
            # Завтра в определенное время
            match = re.search(r'(\d{1,2}):(\d{2})', time_text)
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2))
                reminder_time = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=1)
            else:
                # Завтра в 9:00 по умолчанию
                reminder_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)
        
        else:
            # Попытка распарсить дату и время
            # Формат: 25.12 в 10:30 или 25.12.2024 15:00
            patterns = [
                r'(\d{1,2})\.(\d{1,2})\s+в?\s*(\d{1,2}):(\d{2})',  # 25.12 в 10:30
                r'(\d{1,2})\.(\d{1,2})\.(\d{4})\s+(\d{1,2}):(\d{2})',  # 25.12.2024 15:00
            ]
            
            for pattern in patterns:
                match = re.search(pattern, time_text)
                if match:
                    if len(match.groups()) == 4:  # День.месяц время
                        day, month, hour, minute = match.groups()
                        year = datetime.now().year
                        reminder_time = datetime(year, int(month), int(day), int(hour), int(minute))
                        if reminder_time < datetime.now():
                            reminder_time = reminder_time.replace(year=year + 1)
                    elif len(match.groups()) == 5:  # День.месяц.год время
                        day, month, year, hour, minute = match.groups()
                        reminder_time = datetime(int(year), int(month), int(day), int(hour), int(minute))
                    break
        
        if reminder_time:
            await state.update_data(
                remind_at=reminder_time,
                repeat_type=repeat_type
            )
            
            # Спрашиваем о повторении, если еще не установлено
            if repeat_type == "none":
                await message.answer(
                    "🔁 <b>Повторение</b>\n\n"
                    "Нужно ли повторять это напоминание?",
                    reply_markup=keyboards.repeat_options(),
                    parse_mode="HTML"
                )
                await state.set_state(ReminderStates.waiting_for_repeat)
            else:
                await save_reminder(message, state, message.from_user.id)
        else:
            await message.answer(
                "❌ Не удалось распознать время.\n\n"
                "Попробуйте еще раз в одном из форматов:\n"
                "• <code>через 30 минут</code>\n"
                "• <code>завтра в 14:00</code>\n"
                "• <code>25.12 в 10:30</code>",
                parse_mode="HTML"
            )
    
    except Exception as e:
        logger.error(f"Ошибка парсинга времени: {e}")
        await message.answer(
            "❌ Произошла ошибка при обработке времени.\n"
            "Попробуйте другой формат.",
            parse_mode="HTML"
        )

@router.callback_query(F.data.startswith("repeat_"))
async def process_repeat_option(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора повторения"""
    repeat_option = callback.data.replace("repeat_", "")
    
    repeat_mapping = {
        "none": ("none", 0),
        "daily": ("daily", 1),
        "weekly": ("weekly", 1),
        "monthly": ("monthly", 1),
        "yearly": ("yearly", 1)
    }
    
    repeat_type, repeat_interval = repeat_mapping.get(repeat_option, ("none", 0))
    
    await state.update_data(
        repeat_type=repeat_type,
        repeat_interval=repeat_interval
    )
    
    await save_reminder(callback.message, state, callback.from_user.id)
    await callback.answer()

async def save_reminder(message: Message, state: FSMContext, user_id: int):
    """Сохранение напоминания в базу данных"""
    data = await state.get_data()
    
    try:
        reminder_id = await reminder_db.create_reminder(
            user_id=user_id,
            title=data['title'],
            description=data.get('description'),
            remind_at=data['remind_at'],
            repeat_type=data.get('repeat_type', 'none'),
            repeat_interval=data.get('repeat_interval', 0)
        )
        
        if reminder_id:
            time_str = data['remind_at'].strftime("%d.%m.%Y в %H:%M")
            repeat_str = ""
            if data.get('repeat_type') != 'none':
                repeat_types = {
                    'daily': 'Ежедневно',
                    'weekly': 'Еженедельно',
                    'monthly': 'Ежемесячно',
                    'yearly': 'Ежегодно'
                }
                repeat_str = f"\n🔁 Повторение: {repeat_types.get(data.get('repeat_type'), 'Нет')}"
            
            await message.edit_text(
                f"✅ <b>Напоминание создано!</b>\n\n"
                f"📌 {data['title']}\n"
                f"⏰ {time_str}{repeat_str}\n\n"
                f"Я напомню вам в указанное время.",
                reply_markup=keyboards.back_to_reminders(),
                parse_mode="HTML"
            )
        else:
            await message.edit_text(
                "❌ Не удалось создать напоминание.\n"
                "Попробуйте позже.",
                reply_markup=keyboards.back_to_reminders(),
                parse_mode="HTML"
            )
    
    except Exception as e:
        logger.error(f"Ошибка сохранения напоминания: {e}")
        await message.edit_text(
            "❌ Произошла ошибка при сохранении напоминания.",
            reply_markup=keyboards.back_to_reminders(),
            parse_mode="HTML"
        )
    
    await state.clear()

@router.callback_query(F.data == "reminder_list")
async def show_reminders_list(callback: CallbackQuery):
    """Показать список активных напоминаний"""
    user_id = callback.from_user.id
    
    reminders = await reminder_db.get_user_reminders(user_id, active_only=True)
    
    if not reminders:
        await callback.message.edit_text(
            "📭 <b>У вас нет активных напоминаний</b>\n\n"
            "Создайте первое напоминание, чтобы не забыть о важном!",
            reply_markup=keyboards.empty_list_menu(),
            parse_mode="HTML"
        )
    else:
        text = "📋 <b>Ваши активные напоминания:</b>\n\n"
        
        for i, reminder in enumerate(reminders[:10], 1):
            time_str = reminder['remind_at'].strftime("%d.%m %H:%M")
            repeat_icon = "🔁" if reminder.get('repeat_type') != 'none' else ""
            text += f"{i}. {repeat_icon} <b>{reminder['title']}</b>\n"
            text += f"   ⏰ {time_str}\n"
            if reminder.get('description'):
                text += f"   📝 {reminder['description'][:50]}...\n" if len(reminder['description']) > 50 else f"   📝 {reminder['description']}\n"
            text += "\n"
        
        if len(reminders) > 10:
            text += f"<i>... и еще {len(reminders) - 10} напоминаний</i>\n"
        
        await callback.message.edit_text(
            text,
            reply_markup=keyboards.reminders_list_menu(reminders[:10]),
            parse_mode="HTML"
        )
    
    await callback.answer()

@router.callback_query(F.data.startswith("reminder_view_"))
async def view_reminder(callback: CallbackQuery):
    """Просмотр деталей напоминания"""
    reminder_id = int(callback.data.replace("reminder_view_", ""))
    
    reminder = await reminder_db.get_reminder(reminder_id)
    
    if not reminder:
        await callback.answer("Напоминание не найдено", show_alert=True)
        return
    
    repeat_types = {
        'none': 'Нет',
        'daily': 'Ежедневно',
        'weekly': 'Еженедельно',
        'monthly': 'Ежемесячно',
        'yearly': 'Ежегодно'
    }
    
    text = f"📌 <b>{reminder['title']}</b>\n\n"
    
    if reminder.get('description'):
        text += f"📝 {reminder['description']}\n\n"
    
    text += f"⏰ <b>Время:</b> {reminder['remind_at'].strftime('%d.%m.%Y в %H:%M')}\n"
    text += f"🔁 <b>Повторение:</b> {repeat_types.get(reminder.get('repeat_type', 'none'), 'Нет')}\n"
    text += f"📊 <b>Статус:</b> {'✅ Активно' if reminder.get('is_active') else '❌ Неактивно'}\n"
    
    if reminder.get('created_at'):
        text += f"📅 <b>Создано:</b> {reminder['created_at'].strftime('%d.%m.%Y')}\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboards.reminder_actions(reminder_id),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("reminder_delete_"))
async def delete_reminder(callback: CallbackQuery):
    """Удаление напоминания"""
    reminder_id = int(callback.data.replace("reminder_delete_", ""))
    
    success = await reminder_db.delete_reminder(reminder_id)
    
    if success:
        await callback.message.edit_text(
            "✅ <b>Напоминание удалено</b>",
            reply_markup=keyboards.back_to_reminders(),
            parse_mode="HTML"
        )
        await callback.answer("Удалено")
    else:
        await callback.answer("Ошибка удаления", show_alert=True)

@router.callback_query(F.data.startswith("reminder_complete_"))
async def complete_reminder(callback: CallbackQuery):
    """Отметить напоминание как выполненное"""
    reminder_id = int(callback.data.replace("reminder_complete_", ""))
    
    success = await reminder_db.complete_reminder(reminder_id)
    
    if success:
        await callback.message.edit_text(
            "✅ <b>Напоминание выполнено!</b>",
            reply_markup=keyboards.back_to_reminders(),
            parse_mode="HTML"
        )
        await callback.answer("Выполнено")
    else:
        await callback.answer("Ошибка", show_alert=True)

@router.callback_query(F.data.startswith("reminder_snooze_"))
async def snooze_reminder(callback: CallbackQuery):
    """Отложить напоминание"""
    parts = callback.data.split("_")
    reminder_id = int(parts[2])
    minutes = int(parts[3])
    
    # Получаем напоминание
    reminder = await reminder_db.get_reminder(reminder_id)
    
    if reminder:
        # Обновляем время напоминания
        new_time = datetime.now() + timedelta(minutes=minutes)
        success = await reminder_db.update_reminder(
            reminder_id,
            remind_at=new_time,
            notification_sent=False
        )
        
        if success:
            await callback.message.edit_text(
                f"⏱️ <b>Напоминание отложено на {minutes} минут</b>\n\n"
                f"Я напомню вам в {new_time.strftime('%H:%M')}",
                parse_mode="HTML"
            )
            await callback.answer(f"Отложено на {minutes} минут")
        else:
            await callback.answer("Ошибка при откладывании", show_alert=True)
    else:
        await callback.answer("Напоминание не найдено", show_alert=True)

@router.callback_query(F.data == "reminder_stats")
async def show_reminder_stats(callback: CallbackQuery):
    """Показать статистику напоминаний"""
    user_id = callback.from_user.id
    
    stats = await reminder_db.get_user_stats(user_id)
    
    text = "📊 <b>Статистика напоминаний</b>\n\n"
    text += f"📝 <b>Всего создано:</b> {stats.get('total_reminders', 0)}\n"
    text += f"✅ <b>Выполнено:</b> {stats.get('completed_reminders', 0)}\n"
    text += f"⏰ <b>Активных:</b> {stats.get('active_reminders', 0)}\n\n"
    
    text += "📅 <b>Предстоящие:</b>\n"
    text += f"• Сегодня: {stats.get('upcoming_today', 0)}\n"
    text += f"• На этой неделе: {stats.get('upcoming_week', 0)}\n\n"
    
    if stats.get('completed_reminders', 0) > 0 and stats.get('total_reminders', 0) > 0:
        completion_rate = (stats['completed_reminders'] / stats['total_reminders']) * 100
        text += f"🎯 <b>Процент выполнения:</b> {completion_rate:.1f}%"
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboards.back_to_reminders(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "reminder_settings")
async def show_reminder_settings(callback: CallbackQuery):
    """Показать настройки напоминаний"""
    user_id = callback.from_user.id
    
    settings = await reminder_db.get_user_settings(user_id)
    
    text = "⚙️ <b>Настройки напоминаний</b>\n\n"
    text += f"🔔 Напоминания: {'✅ Включены' if settings.get('enabled', True) else '❌ Выключены'}\n"
    text += f"🔊 Звук: {'✅ Включен' if settings.get('sound_enabled', True) else '❌ Выключен'}\n"
    text += f"⏰ Время по умолчанию: {settings.get('default_notification_time', '09:00')}\n"
    text += f"🌍 Часовой пояс: {settings.get('timezone', 'Europe/Moscow')}\n"
    text += f"⏱️ Предупреждать за: {settings.get('advance_notification', 10)} минут\n"
    text += f"📋 Ежедневная сводка: {'✅ Включена' if settings.get('daily_summary', False) else '❌ Выключена'}\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboards.settings_menu(settings),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("setting_toggle_"))
async def toggle_setting(callback: CallbackQuery):
    """Переключение настроек"""
    setting = callback.data.replace("setting_toggle_", "")
    user_id = callback.from_user.id
    
    success = await reminder_db.toggle_setting(user_id, setting)
    
    if success:
        # Обновляем отображение настроек
        await show_reminder_settings(callback)
    else:
        await callback.answer("Ошибка изменения настройки", show_alert=True)

@router.callback_query(F.data == "setting_notification_time")
async def set_notification_time(callback: CallbackQuery, state: FSMContext):
    """Настройка времени уведомлений по умолчанию"""
    await callback.message.edit_text(
        "⏰ <b>Настройка времени уведомлений</b>\n\n"
        "Введите время по умолчанию для новых напоминаний в формате ЧЧ:ММ\n"
        "Например: <code>09:00</code> или <code>18:30</code>\n\n"
        "Текущее время можно узнать командой /skip",
        parse_mode="HTML"
    )
    await state.set_state(ReminderStates.waiting_for_default_time)
    await callback.answer()

@router.message(ReminderStates.waiting_for_default_time)
async def process_default_time(message: Message, state: FSMContext):
    """Обработка времени по умолчанию"""
    user_id = message.from_user.id
    
    if message.text == "/skip":
        settings = await reminder_db.get_user_settings(user_id)
        current_time = settings.get('default_notification_time', '09:00')
        await message.answer(
            f"⏰ Текущее время по умолчанию: <b>{current_time}</b>",
            reply_markup=keyboards.back_to_reminders(),
            parse_mode="HTML"
        )
        await state.clear()
        return
    
    # Парсим время
    import re
    match = re.match(r'^(\d{1,2}):(\d{2})$', message.text)
    
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            time_str = f"{hour:02d}:{minute:02d}:00"
            
            success = await reminder_db.update_user_settings(
                user_id,
                default_notification_time=time_str
            )
            
            if success:
                await message.answer(
                    f"✅ <b>Время по умолчанию установлено:</b> {hour:02d}:{minute:02d}\n\n"
                    "Теперь новые напоминания без указания времени будут создаваться на это время.",
                    reply_markup=keyboards.back_to_reminders(),
                    parse_mode="HTML"
                )
            else:
                await message.answer(
                    "❌ Ошибка сохранения настройки",
                    reply_markup=keyboards.back_to_reminders(),
                    parse_mode="HTML"
                )
        else:
            await message.answer(
                "❌ Неверное время. Часы должны быть от 0 до 23, минуты от 0 до 59.\n"
                "Попробуйте еще раз или отправьте /skip для отмены.",
                parse_mode="HTML"
            )
            return
    else:
        await message.answer(
            "❌ Неверный формат. Используйте формат ЧЧ:ММ\n"
            "Например: <code>09:00</code> или <code>18:30</code>",
            parse_mode="HTML"
        )
        return
    
    await state.clear()

@router.callback_query(F.data == "setting_advance_time")
async def set_advance_time(callback: CallbackQuery):
    """Настройка времени предварительного напоминания"""
    user_id = callback.from_user.id
    settings = await reminder_db.get_user_settings(user_id)
    current_advance = settings.get('advance_notification', 10)
    
    await callback.message.edit_text(
        f"⏱️ <b>Время предварительного напоминания</b>\n\n"
        f"Текущее значение: <b>{current_advance} минут</b>\n\n"
        "За сколько минут до события отправлять напоминание?\n"
        "Выберите или введите свое значение:",
        reply_markup=keyboards.advance_time_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("advance_"))
async def process_advance_time(callback: CallbackQuery):
    """Обработка выбора времени предупреждения"""
    minutes = int(callback.data.replace("advance_", ""))
    user_id = callback.from_user.id
    
    success = await reminder_db.update_user_settings(
        user_id,
        advance_notification=minutes
    )
    
    if success:
        await callback.message.edit_text(
            f"✅ <b>Настройка сохранена</b>\n\n"
            f"Напоминания будут приходить за <b>{minutes} минут</b> до события.",
            reply_markup=keyboards.back_to_reminders(),
            parse_mode="HTML"
        )
        await callback.answer("Сохранено")
    else:
        await callback.answer("Ошибка сохранения", show_alert=True)