from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.contacts import contacts_manager, Contact
from utils.html_utils import escape_html, escape_email
import re

router = Router()

class ContactStates(StatesGroup):
    """Состояния для работы с контактами"""
    adding_name = State()
    adding_email = State()
    adding_phone = State()
    adding_telegram = State()
    adding_company = State()
    adding_position = State()
    adding_notes = State()
    adding_tags = State()
    editing_contact = State()
    searching = State()

def create_contacts_menu():
    """Главное меню контактов"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="👥 Все контакты", callback_data="contacts_list"),
        InlineKeyboardButton(text="➕ Добавить контакт", callback_data="contacts_add"),
        InlineKeyboardButton(text="🔍 Поиск контактов", callback_data="contacts_search"),
        InlineKeyboardButton(text="📊 Статистика", callback_data="contacts_stats"),
        InlineKeyboardButton(text="🏷️ По тегам", callback_data="contacts_tags"),
        InlineKeyboardButton(text="◀️ Назад в меню", callback_data="menu_back")
    )
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup()

def create_contact_actions_menu(contact_id: str):
    """Меню действий с контактом"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"contact_edit_{contact_id}"),
        InlineKeyboardButton(text="📧 Написать письмо", callback_data=f"contact_email_{contact_id}"),
        InlineKeyboardButton(text="📱 Позвонить", callback_data=f"contact_call_{contact_id}"),
        InlineKeyboardButton(text="📲 Telegram", callback_data=f"contact_telegram_{contact_id}"),
        InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"contact_delete_{contact_id}"),
        InlineKeyboardButton(text="◀️ К списку", callback_data="contacts_list")
    )
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup()

def create_cancel_button():
    """Кнопка отмены"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="❌ Отменить", callback_data="contacts_cancel"))
    return builder.as_markup()

@router.callback_query(F.data == "contacts_menu")
async def contacts_main_menu(callback: CallbackQuery):
    """Главное меню контактов"""
    await callback.message.edit_text(
        "👥 <b>Управление контактами</b>\n\n"
        "📱 Сохраняйте и управляйте контактами:\n"
        "• Email адреса\n"
        "• Телефонные номера\n"
        "• Telegram никнеймы\n"
        "• Информация о компаниях\n"
        "• Теги для группировки\n\n"
        "💡 <b>Выберите действие:</b>",
        reply_markup=create_contacts_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "contacts_list")
async def contacts_list(callback: CallbackQuery):
    """Показать список всех контактов"""
    user_id = callback.from_user.id
    contacts = await contacts_manager.get_all_contacts(user_id)
    
    if not contacts:
        await callback.message.edit_text(
            "📭 <b>У вас пока нет контактов</b>\n\n"
            "➕ Нажмите \"Добавить контакт\" чтобы создать первый контакт",
            reply_markup=create_contacts_menu(),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    # Показываем первые 10 контактов
    contacts_text = f"👥 <b>Ваши контакты ({len(contacts)})</b>\n\n"
    
    builder = InlineKeyboardBuilder()
    
    for i, contact in enumerate(contacts[:10]):
        # Краткая информация о контакте
        info_parts = []
        if contact.email:
            info_parts.append("📧")
        if contact.phone:
            info_parts.append("📱")
        if contact.telegram:
            info_parts.append("📲")
        
        info_str = " ".join(info_parts)
        button_text = f"{contact.name} {info_str}".strip()
        
        builder.add(InlineKeyboardButton(
            text=button_text,
            callback_data=f"contact_view_{contact.id}"
        ))
    
    # Если контактов больше 10, добавляем кнопку "Показать еще"
    if len(contacts) > 10:
        builder.add(InlineKeyboardButton(
            text=f"📄 Показать все ({len(contacts) - 10} еще)",
            callback_data="contacts_list_all"
        ))
    
    builder.add(InlineKeyboardButton(text="◀️ Назад", callback_data="contacts_menu"))
    builder.adjust(1)
    
    await callback.message.edit_text(
        contacts_text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("contact_view_"))
async def contact_view(callback: CallbackQuery):
    """Показать детали контакта"""
    contact_id = callback.data.split("_")[-1]
    user_id = callback.from_user.id
    
    contact = await contacts_manager.find_contact(user_id, contact_id)
    if not contact:
        await callback.answer("❌ Контакт не найден", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"📋 <b>Информация о контакте</b>\n\n{contact.format_display()}",
        reply_markup=create_contact_actions_menu(contact_id),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "contacts_add")
async def contacts_add_start(callback: CallbackQuery, state: FSMContext):
    """Начать добавление контакта"""
    await callback.message.edit_text(
        "➕ <b>Добавление нового контакта</b>\n\n"
        "👤 <b>Шаг 1 из 8: Имя контакта</b>\n\n"
        "📝 Введите имя контакта:\n"
        "(например: Иван Петров, Мария Сидорова)\n\n"
        "✏️ <i>Напишите имя в следующем сообщении</i>",
        reply_markup=create_cancel_button(),
        parse_mode="HTML"
    )
    
    await state.set_state(ContactStates.adding_name)
    await callback.answer()

@router.message(ContactStates.adding_name)
async def contacts_add_name(message: Message, state: FSMContext):
    """Обработать ввод имени контакта"""
    name = message.text.strip()
    
    if len(name) < 2:
        await message.answer(
            "❌ <b>Имя слишком короткое</b>\n\n"
            "📝 Введите корректное имя (минимум 2 символа):",
            reply_markup=create_cancel_button(),
            parse_mode="HTML"
        )
        return
    
    # Проверяем, нет ли уже контакта с таким именем
    user_id = message.from_user.id
    existing_contacts = await contacts_manager.get_all_contacts(user_id)
    if any(c.name.lower() == name.lower() for c in existing_contacts):
        await message.answer(
            f"⚠️ <b>Контакт с именем \"{name}\" уже существует</b>\n\n"
            "📝 Введите другое имя или измените существующий:",
            reply_markup=create_cancel_button(),
            parse_mode="HTML"
        )
        return
    
    await state.update_data(name=name)
    
    await message.answer(
        f"✅ <b>Имя принято:</b> {name}\n\n"
        "📧 <b>Шаг 2 из 8: Email адрес</b>\n\n"
        "📝 Введите email адрес:\n"
        "(например: ivan@example.com)\n\n"
        "⏭️ Или отправьте \"-\" чтобы пропустить\n\n"
        "✏️ <i>Напишите email в следующем сообщении</i>",
        reply_markup=create_cancel_button(),
        parse_mode="HTML"
    )
    
    await state.set_state(ContactStates.adding_email)

@router.message(ContactStates.adding_email)
async def contacts_add_email(message: Message, state: FSMContext):
    """Обработать ввод email"""
    email = message.text.strip()
    
    if email != "-":
        # Проверяем формат email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            await message.answer(
                "❌ <b>Некорректный email адрес</b>\n\n"
                "📝 Введите правильный email:\n"
                "(например: ivan@example.com)\n\n"
                "⏭️ Или отправьте \"-\" чтобы пропустить:",
                reply_markup=create_cancel_button(),
                parse_mode="HTML"
            )
            return
    else:
        email = ""
    
    await state.update_data(email=email)
    
    data = await state.get_data()
    name = data.get('name', '')
    
    await message.answer(
        f"✅ <b>Email принят:</b> {email if email else 'пропущен'}\n\n"
        f"👤 <b>Контакт:</b> {name}\n\n"
        "📱 <b>Шаг 3 из 8: Номер телефона</b>\n\n"
        "📝 Введите номер телефона:\n"
        "(например: +7 999 123-45-67)\n\n"
        "⏭️ Или отправьте \"-\" чтобы пропустить\n\n"
        "✏️ <i>Напишите номер в следующем сообщении</i>",
        reply_markup=create_cancel_button(),
        parse_mode="HTML"
    )
    
    await state.set_state(ContactStates.adding_phone)

@router.message(ContactStates.adding_phone)
async def contacts_add_phone(message: Message, state: FSMContext):
    """Обработать ввод телефона"""
    phone = message.text.strip()
    
    if phone != "-":
        # Простая проверка телефона (содержит цифры)
        if not re.search(r'\d', phone):
            await message.answer(
                "❌ <b>Некорректный номер телефона</b>\n\n"
                "📝 Введите правильный номер:\n"
                "(например: +7 999 123-45-67)\n\n"
                "⏭️ Или отправьте \"-\" чтобы пропустить:",
                reply_markup=create_cancel_button(),
                parse_mode="HTML"
            )
            return
    else:
        phone = ""
    
    await state.update_data(phone=phone)
    
    data = await state.get_data()
    name = data.get('name', '')
    
    await message.answer(
        f"✅ <b>Телефон принят:</b> {phone if phone else 'пропущен'}\n\n"
        f"👤 <b>Контакт:</b> {name}\n\n"
        "📲 <b>Шаг 4 из 8: Telegram</b>\n\n"
        "📝 Введите Telegram никнейм:\n"
        "(например: @username или просто username)\n\n"
        "⏭️ Или отправьте \"-\" чтобы пропустить\n\n"
        "✏️ <i>Напишите никнейм в следующем сообщении</i>",
        reply_markup=create_cancel_button(),
        parse_mode="HTML"
    )
    
    await state.set_state(ContactStates.adding_telegram)

@router.message(ContactStates.adding_telegram)
async def contacts_add_telegram(message: Message, state: FSMContext):
    """Обработать ввод Telegram"""
    telegram = message.text.strip()
    
    if telegram != "-":
        # Убираем @ если есть и проверяем формат
        telegram = telegram.lstrip('@')
        if not re.match(r'^[a-zA-Z0-9_]{5,32}$', telegram):
            await message.answer(
                "❌ <b>Некорректный Telegram никнейм</b>\n\n"
                "📝 Введите правильный никнейм:\n"
                "(например: @username или username)\n\n"
                "⏭️ Или отправьте \"-\" чтобы пропустить:",
                reply_markup=create_cancel_button(),
                parse_mode="HTML"
            )
            return
    else:
        telegram = ""
    
    await state.update_data(telegram=telegram)
    
    data = await state.get_data()
    name = data.get('name', '')
    
    await message.answer(
        f"✅ <b>Telegram принят:</b> {('@' + telegram) if telegram else 'пропущен'}\n\n"
        f"👤 <b>Контакт:</b> {name}\n\n"
        "🏢 <b>Шаг 5 из 8: Компания</b>\n\n"
        "📝 Введите название компании:\n"
        "(например: ООО \"Рога и Копыта\")\n\n"
        "⏭️ Или отправьте \"-\" чтобы пропустить\n\n"
        "✏️ <i>Напишите компанию в следующем сообщении</i>",
        reply_markup=create_cancel_button(),
        parse_mode="HTML"
    )
    
    await state.set_state(ContactStates.adding_company)

@router.message(ContactStates.adding_company)
async def contacts_add_company(message: Message, state: FSMContext):
    """Обработать ввод компании"""
    company = message.text.strip() if message.text.strip() != "-" else ""
    
    await state.update_data(company=company)
    
    data = await state.get_data()
    name = data.get('name', '')
    
    await message.answer(
        f"✅ <b>Компания принята:</b> {company if company else 'пропущена'}\n\n"
        f"👤 <b>Контакт:</b> {name}\n\n"
        "💼 <b>Шаг 6 из 8: Должность</b>\n\n"
        "📝 Введите должность:\n"
        "(например: Менеджер по продажам)\n\n"
        "⏭️ Или отправьте \"-\" чтобы пропустить\n\n"
        "✏️ <i>Напишите должность в следующем сообщении</i>",
        reply_markup=create_cancel_button(),
        parse_mode="HTML"
    )
    
    await state.set_state(ContactStates.adding_position)

@router.message(ContactStates.adding_position)
async def contacts_add_position(message: Message, state: FSMContext):
    """Обработать ввод должности"""
    position = message.text.strip() if message.text.strip() != "-" else ""
    
    await state.update_data(position=position)
    
    data = await state.get_data()
    name = data.get('name', '')
    
    await message.answer(
        f"✅ <b>Должность принята:</b> {position if position else 'пропущена'}\n\n"
        f"👤 <b>Контакт:</b> {name}\n\n"
        "🏷️ <b>Шаг 7 из 8: Теги</b>\n\n"
        "📝 Введите теги через запятую:\n"
        "(например: работа, клиент, важный)\n\n"
        "⏭️ Или отправьте \"-\" чтобы пропустить\n\n"
        "✏️ <i>Напишите теги в следующем сообщении</i>",
        reply_markup=create_cancel_button(),
        parse_mode="HTML"
    )
    
    await state.set_state(ContactStates.adding_tags)

@router.message(ContactStates.adding_tags)
async def contacts_add_tags(message: Message, state: FSMContext):
    """Обработать ввод тегов"""
    tags_input = message.text.strip()
    tags = []
    
    if tags_input != "-":
        # Разбиваем по запятым и очищаем
        tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
    
    await state.update_data(tags=tags)
    
    data = await state.get_data()
    name = data.get('name', '')
    
    await message.answer(
        f"✅ <b>Теги приняты:</b> {', '.join(tags) if tags else 'пропущены'}\n\n"
        f"👤 <b>Контакт:</b> {name}\n\n"
        "📝 <b>Шаг 8 из 8: Заметки</b>\n\n"
        "📝 Введите дополнительные заметки:\n"
        "(например: встретились на конференции)\n\n"
        "⏭️ Или отправьте \"-\" чтобы пропустить\n\n"
        "✏️ <i>Напишите заметки в следующем сообщении</i>",
        reply_markup=create_cancel_button(),
        parse_mode="HTML"
    )
    
    await state.set_state(ContactStates.adding_notes)

@router.message(ContactStates.adding_notes)
async def contacts_add_notes(message: Message, state: FSMContext):
    """Обработать ввод заметок и завершить создание контакта"""
    notes = message.text.strip() if message.text.strip() != "-" else ""
    
    data = await state.get_data()
    user_id = message.from_user.id
    
    # Создаем контакт
    contact = Contact(
        name=data['name'],
        email=data.get('email', ''),
        phone=data.get('phone', ''),
        telegram=data.get('telegram', ''),
        company=data.get('company', ''),
        position=data.get('position', ''),
        notes=notes,
        tags=data.get('tags', [])
    )
    
    # Сохраняем контакт
    success = await contacts_manager.add_contact(user_id, contact)
    
    if success:
        await message.answer(
            f"🎉 <b>Контакт успешно создан!</b>\n\n{contact.format_display()}\n\n"
            "💡 <b>Теперь вы можете:</b>\n"
            "• Найти контакт через поиск\n"
            "• Отправить письмо одним кликом\n"
            "• Использовать теги для группировки",
            reply_markup=create_contacts_menu(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "❌ <b>Ошибка при создании контакта</b>\n\n"
            "Попробуйте еще раз или обратитесь за помощью.",
            reply_markup=create_contacts_menu(),
            parse_mode="HTML"
        )
    
    await state.clear()

@router.callback_query(F.data == "contacts_cancel")
async def contacts_cancel(callback: CallbackQuery, state: FSMContext):
    """Отменить операцию с контактами"""
    await state.clear()
    await callback.message.edit_text(
        "❌ <b>Операция отменена</b>\n\n"
        "🔙 Возвращаемся в меню контактов",
        reply_markup=create_contacts_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "contacts_stats")
async def contacts_stats(callback: CallbackQuery):
    """Показать статистику контактов"""
    user_id = callback.from_user.id
    stats = await contacts_manager.get_stats(user_id)
    
    stats_text = f"📊 <b>Статистика контактов</b>\n\n"
    stats_text += f"👥 <b>Всего контактов:</b> {stats['total']}\n"
    stats_text += f"📧 <b>С email:</b> {stats['with_email']}\n"
    stats_text += f"📱 <b>С телефоном:</b> {stats['with_phone']}\n"
    stats_text += f"📲 <b>С Telegram:</b> {stats['with_telegram']}\n\n"
    
    if stats['tags']:
        stats_text += "🏷️ <b>Популярные теги:</b>\n"
        sorted_tags = sorted(stats['tags'].items(), key=lambda x: x[1], reverse=True)
        for tag, count in sorted_tags[:5]:
            stats_text += f"• {tag}: {count}\n"
    
    await callback.message.edit_text(
        stats_text,
        reply_markup=create_contacts_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "contacts_search")
async def contacts_search_start(callback: CallbackQuery, state: FSMContext):
    """Начать поиск контактов"""
    await callback.message.edit_text(
        "🔍 <b>Поиск контактов</b>\n\n"
        "📝 Введите поисковый запрос:\n"
        "• Имя контакта\n"
        "• Email адрес\n"
        "• Номер телефона\n"
        "• Название компании\n"
        "• Тег\n\n"
        "✏️ <i>Напишите запрос в следующем сообщении</i>",
        reply_markup=create_cancel_button(),
        parse_mode="HTML"
    )
    
    await state.set_state(ContactStates.searching)
    await callback.answer()

@router.message(ContactStates.searching)
async def contacts_search_process(message: Message, state: FSMContext):
    """Обработать поисковый запрос"""
    query = message.text.strip()
    
    if len(query) < 2:
        await message.answer(
            "❌ <b>Запрос слишком короткий</b>\n\n"
            "📝 Введите минимум 2 символа для поиска:",
            reply_markup=create_cancel_button(),
            parse_mode="HTML"
        )
        return
    
    user_id = message.from_user.id
    results = await contacts_manager.search_contacts(user_id, query)
    
    if not results:
        await message.answer(
            f"🔍 <b>Поиск: \"{query}\"</b>\n\n"
            "❌ <b>Контакты не найдены</b>\n\n"
            "💡 <b>Попробуйте:</b>\n"
            "• Изменить запрос\n"
            "• Поискать по части имени\n"
            "• Поискать по тегу или компании",
            reply_markup=create_contacts_menu(),
            parse_mode="HTML"
        )
        await state.clear()
        return
    
    # Показываем результаты поиска
    search_text = f"🔍 <b>Результаты поиска: \"{query}\"</b>\n\n"
    search_text += f"📊 <b>Найдено контактов:</b> {len(results)}\n\n"
    
    builder = InlineKeyboardBuilder()
    
    for contact in results[:10]:  # Показываем первые 10
        info_parts = []
        if contact.email:
            info_parts.append("📧")
        if contact.phone:
            info_parts.append("📱")
        if contact.telegram:
            info_parts.append("📲")
        
        info_str = " ".join(info_parts)
        button_text = f"{contact.name} {info_str}".strip()
        
        builder.add(InlineKeyboardButton(
            text=button_text,
            callback_data=f"contact_view_{contact.id}"
        ))
    
    # Если результатов больше 10
    if len(results) > 10:
        builder.add(InlineKeyboardButton(
            text=f"📄 Показать все ({len(results) - 10} еще)",
            callback_data=f"contacts_search_all_{query}"
        ))
    
    builder.add(
        InlineKeyboardButton(text="🔍 Новый поиск", callback_data="contacts_search"),
        InlineKeyboardButton(text="◀️ Назад", callback_data="contacts_menu")
    )
    builder.adjust(1)
    
    await message.answer(
        search_text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    
    await state.clear()

@router.callback_query(F.data == "contacts_tags")
async def contacts_tags_list(callback: CallbackQuery):
    """Показать контакты по тегам"""
    user_id = callback.from_user.id
    stats = await contacts_manager.get_stats(user_id)
    
    if not stats['tags']:
        await callback.message.edit_text(
            "🏷️ <b>Теги контактов</b>\n\n"
            "❌ <b>У вас пока нет тегов</b>\n\n"
            "💡 При создании контактов добавляйте теги для удобной группировки",
            reply_markup=create_contacts_menu(),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    # Сортируем теги по популярности
    sorted_tags = sorted(stats['tags'].items(), key=lambda x: x[1], reverse=True)
    
    tags_text = f"🏷️ <b>Ваши теги ({len(sorted_tags)})</b>\n\n"
    
    builder = InlineKeyboardBuilder()
    
    for tag, count in sorted_tags:
        builder.add(InlineKeyboardButton(
            text=f"#{tag} ({count})",
            callback_data=f"contacts_tag_{tag}"
        ))
    
    builder.add(InlineKeyboardButton(text="◀️ Назад", callback_data="contacts_menu"))
    builder.adjust(2, 1)
    
    await callback.message.edit_text(
        tags_text + "📂 <b>Выберите тег для просмотра:</b>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("contacts_tag_"))
async def contacts_by_tag(callback: CallbackQuery):
    """Показать контакты по выбранному тегу"""
    tag = callback.data.replace("contacts_tag_", "")
    user_id = callback.from_user.id
    
    contacts = await contacts_manager.get_contacts_by_tag(user_id, tag)
    
    if not contacts:
        await callback.message.edit_text(
            f"🏷️ <b>Тег: #{tag}</b>\n\n"
            "❌ <b>Контакты с этим тегом не найдены</b>",
            reply_markup=create_contacts_menu(),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    tag_text = f"🏷️ <b>Тег: #{tag}</b>\n\n"
    tag_text += f"📊 <b>Контактов:</b> {len(contacts)}\n\n"
    
    builder = InlineKeyboardBuilder()
    
    for contact in contacts:
        info_parts = []
        if contact.email:
            info_parts.append("📧")
        if contact.phone:
            info_parts.append("📱")
        if contact.telegram:
            info_parts.append("📲")
        
        info_str = " ".join(info_parts)
        button_text = f"{contact.name} {info_str}".strip()
        
        builder.add(InlineKeyboardButton(
            text=button_text,
            callback_data=f"contact_view_{contact.id}"
        ))
    
    builder.add(
        InlineKeyboardButton(text="🏷️ Все теги", callback_data="contacts_tags"),
        InlineKeyboardButton(text="◀️ Назад", callback_data="contacts_menu")
    )
    builder.adjust(1)
    
    await callback.message.edit_text(
        tag_text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("contact_delete_"))
async def contact_delete_confirm(callback: CallbackQuery):
    """Подтверждение удаления контакта"""
    contact_id = callback.data.split("_")[-1]
    user_id = callback.from_user.id
    
    contact = await contacts_manager.find_contact(user_id, contact_id)
    if not contact:
        await callback.answer("❌ Контакт не найден", show_alert=True)
        return
    
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="🗑️ Да, удалить", callback_data=f"contact_delete_confirm_{contact_id}"),
        InlineKeyboardButton(text="❌ Отменить", callback_data=f"contact_view_{contact_id}")
    )
    builder.adjust(1, 1)
    
    await callback.message.edit_text(
        f"⚠️ <b>Подтверждение удаления</b>\n\n"
        f"🗑️ Вы действительно хотите удалить контакт?\n\n"
        f"👤 <b>{contact.name}</b>\n"
        f"📧 {contact.email if contact.email else 'Не указан'}\n"
        f"📱 {contact.phone if contact.phone else 'Не указан'}\n\n"
        "⚠️ <b>Это действие нельзя отменить!</b>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("contact_delete_confirm_"))
async def contact_delete_execute(callback: CallbackQuery):
    """Выполнить удаление контакта"""
    contact_id = callback.data.split("_")[-1]
    user_id = callback.from_user.id
    
    contact = await contacts_manager.find_contact(user_id, contact_id)
    if not contact:
        await callback.answer("❌ Контакт не найден", show_alert=True)
        return
    
    success = await contacts_manager.delete_contact(user_id, contact_id)
    
    if success:
        await callback.message.edit_text(
            f"✅ <b>Контакт удален</b>\n\n"
            f"🗑️ Контакт \"{contact.name}\" успешно удален из ваших контактов",
            reply_markup=create_contacts_menu(),
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            "❌ <b>Ошибка удаления</b>\n\n"
            "Не удалось удалить контакт. Попробуйте еще раз.",
            reply_markup=create_contacts_menu(),
            parse_mode="HTML"
        )
    
    await callback.answer()

@router.callback_query(F.data.startswith("contact_email_"))
async def contact_send_email(callback: CallbackQuery):
    """Отправить email контакту"""
    contact_id = callback.data.split("_")[-1]
    user_id = callback.from_user.id
    
    contact = await contacts_manager.find_contact(user_id, contact_id)
    if not contact:
        await callback.answer("❌ Контакт не найден", show_alert=True)
        return
    
    if not contact.email:
        await callback.answer("❌ У контакта нет email адреса", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"📧 <b>Отправить письмо</b>\n\n"
        f"👤 <b>Получатель:</b> {contact.name}\n"
        f"📧 <b>Email:</b> {escape_email(contact.email)}\n\n"
        f"💡 <b>Чтобы отправить письмо, напишите:</b>\n"
        f"\"отправь {escape_email(contact.email)} об [тема письма]\"\n\n"
        f"🤖 <b>Или попросите AI написать письмо:</b>\n"
        f"\"напиши письмо {contact.name} о встрече\"",
        reply_markup=create_contact_actions_menu(contact_id),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("contact_call_"))
async def contact_call(callback: CallbackQuery):
    """Позвонить контакту"""
    contact_id = callback.data.split("_")[-1]
    user_id = callback.from_user.id
    
    contact = await contacts_manager.find_contact(user_id, contact_id)
    if not contact:
        await callback.answer("❌ Контакт не найден", show_alert=True)
        return
    
    print(f"DEBUG: Contact call - contact_id: {contact_id}, name: '{contact.name}', phone: '{contact.phone}', phone type: {type(contact.phone)}")
    
    if not contact.phone:
        await callback.answer("❌ У контакта нет номера телефона", show_alert=True)
        return
    
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="◀️ Назад", callback_data=f"contact_view_{contact_id}")
    )
    builder.adjust(1, 1)
    
    await callback.message.edit_text(
        f"📞 <b>Звонок контакту</b>\n\n"
        f"👤 <b>Имя:</b> {contact.name}\n"
        f"📱 <b>Телефон:</b> <code>{contact.phone}</code>\n\n"
        f"💡 <i>Нажмите на номер телефона чтобы скопировать</i>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("contact_telegram_"))
async def contact_telegram(callback: CallbackQuery):
    """Написать в Telegram контакту"""
    contact_id = callback.data.split("_")[-1]
    user_id = callback.from_user.id
    
    contact = await contacts_manager.find_contact(user_id, contact_id)
    if not contact:
        await callback.answer("❌ Контакт не найден", show_alert=True)
        return
    
    if not contact.telegram:
        await callback.answer("❌ У контакта нет Telegram", show_alert=True)
        return
    
    telegram_username = contact.telegram.lstrip('@')
    telegram_url = f"https://t.me/{telegram_username}"
    
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="📲 Написать в Telegram", url=telegram_url),
        InlineKeyboardButton(text="◀️ Назад", callback_data=f"contact_view_{contact_id}")
    )
    builder.adjust(1, 1)
    
    await callback.message.edit_text(
        f"📲 <b>Telegram контакт</b>\n\n"
        f"👤 <b>Имя:</b> {contact.name}\n"
        f"📲 <b>Telegram:</b> @{telegram_username}\n\n"
        f"💬 Нажмите кнопку чтобы открыть чат в Telegram",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("contact_edit_"))
async def contact_edit_start(callback: CallbackQuery, state: FSMContext):
    """Начать редактирование контакта"""
    contact_id = callback.data.split("_")[-1]
    user_id = callback.from_user.id
    
    contact = await contacts_manager.find_contact(user_id, contact_id)
    if not contact:
        await callback.answer("❌ Контакт не найден", show_alert=True)
        return
    
    # Сохраняем ID контакта в состояние
    await state.update_data(editing_contact_id=contact_id)
    
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="👤 Изменить имя", callback_data=f"edit_field_name_{contact_id}"),
        InlineKeyboardButton(text="📧 Изменить email", callback_data=f"edit_field_email_{contact_id}"),
        InlineKeyboardButton(text="📱 Изменить телефон", callback_data=f"edit_field_phone_{contact_id}"),
        InlineKeyboardButton(text="📲 Изменить Telegram", callback_data=f"edit_field_telegram_{contact_id}"),
        InlineKeyboardButton(text="🏢 Изменить компанию", callback_data=f"edit_field_company_{contact_id}"),
        InlineKeyboardButton(text="💼 Изменить должность", callback_data=f"edit_field_position_{contact_id}"),
        InlineKeyboardButton(text="🏷️ Изменить теги", callback_data=f"edit_field_tags_{contact_id}"),
        InlineKeyboardButton(text="📝 Изменить заметки", callback_data=f"edit_field_notes_{contact_id}"),
        InlineKeyboardButton(text="◀️ Назад к контакту", callback_data=f"contact_view_{contact_id}")
    )
    builder.adjust(2, 2, 2, 2, 1)
    
    await callback.message.edit_text(
        f"✏️ <b>Редактирование контакта</b>\n\n"
        f"{contact.format_display()}\n\n"
        "🔧 <b>Что хотите изменить?</b>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("edit_field_"))
async def contact_edit_field(callback: CallbackQuery, state: FSMContext):
    """Редактировать поле контакта"""
    parts = callback.data.split("_")
    field = parts[2]
    contact_id = parts[3]
    
    user_id = callback.from_user.id
    contact = await contacts_manager.find_contact(user_id, contact_id)
    
    if not contact:
        await callback.answer("❌ Контакт не найден", show_alert=True)
        return
    
    # Сохраняем информацию о редактируемом поле
    await state.update_data(editing_contact_id=contact_id, editing_field=field)
    
    field_names = {
        'name': 'имя',
        'email': 'email',
        'phone': 'телефон', 
        'telegram': 'Telegram',
        'company': 'компанию',
        'position': 'должность',
        'tags': 'теги',
        'notes': 'заметки'
    }
    
    current_value = getattr(contact, field, '')
    if field == 'tags' and current_value:
        current_value = ', '.join(current_value)
    
    field_instructions = {
        'name': "Введите новое имя контакта:",
        'email': "Введите новый email адрес:",
        'phone': "Введите новый номер телефона:",
        'telegram': "Введите новый Telegram никнейм:",
        'company': "Введите название компании:",
        'position': "Введите должность:",
        'tags': "Введите теги через запятую:",
        'notes': "Введите новые заметки:"
    }
    
    cancel_keyboard = InlineKeyboardBuilder()
    cancel_keyboard.add(
        InlineKeyboardButton(text="❌ Отменить", callback_data=f"contact_edit_{contact_id}")
    )
    
    await callback.message.edit_text(
        f"✏️ <b>Изменить {field_names.get(field, field)}</b>\n\n"
        f"👤 <b>Контакт:</b> {contact.name}\n"
        f"📝 <b>Текущее значение:</b> {current_value if current_value else 'Не указано'}\n\n"
        f"{field_instructions.get(field, 'Введите новое значение:')}\n\n"
        "✏️ <i>Напишите новое значение в следующем сообщении</i>",
        reply_markup=cancel_keyboard.as_markup(),
        parse_mode="HTML"
    )
    
    await state.set_state(ContactStates.editing_contact)
    await callback.answer()

@router.message(ContactStates.editing_contact)
async def contact_edit_process(message: Message, state: FSMContext):
    """Обработать изменение поля контакта"""
    data = await state.get_data()
    contact_id = data.get('editing_contact_id')
    field = data.get('editing_field')
    
    if not contact_id or not field:
        await message.answer("❌ Ошибка редактирования")
        await state.clear()
        return
    
    user_id = message.from_user.id
    contact = await contacts_manager.find_contact(user_id, contact_id)
    
    if not contact:
        await message.answer("❌ Контакт не найден")
        await state.clear()
        return
    
    new_value = message.text.strip()
    
    # Валидация в зависимости от поля
    if field == 'name':
        if len(new_value) < 2:
            await message.answer(
                "❌ <b>Имя слишком короткое</b>\n\n"
                "📝 Введите корректное имя (минимум 2 символа):",
                parse_mode="HTML"
            )
            return
    elif field == 'email' and new_value != "":
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, new_value):
            await message.answer(
                "❌ <b>Некорректный email адрес</b>\n\n"
                "📝 Введите правильный email:",
                parse_mode="HTML"
            )
            return
    elif field == 'phone' and new_value != "":
        if not re.search(r'\d', new_value):
            await message.answer(
                "❌ <b>Некорректный номер телефона</b>\n\n"
                "📝 Введите правильный номер:",
                parse_mode="HTML"
            )
            return
    elif field == 'telegram' and new_value != "":
        new_value = new_value.lstrip('@')
        if not re.match(r'^[a-zA-Z0-9_]{5,32}$', new_value):
            await message.answer(
                "❌ <b>Некорректный Telegram никнейм</b>\n\n"
                "📝 Введите правильный никнейм:",
                parse_mode="HTML"
            )
            return
    elif field == 'tags':
        if new_value:
            new_value = [tag.strip() for tag in new_value.split(',') if tag.strip()]
        else:
            new_value = []
    
    # Обновляем поле контакта
    if field == 'tags':
        contact.tags = new_value
    else:
        setattr(contact, field, new_value)
    
    # Сохраняем изменения
    success = await contacts_manager.update_contact(user_id, contact)
    
    if success:
        field_names = {
            'name': 'Имя',
            'email': 'Email',
            'phone': 'Телефон', 
            'telegram': 'Telegram',
            'company': 'Компания',
            'position': 'Должность',
            'tags': 'Теги',
            'notes': 'Заметки'
        }
        
        display_value = new_value
        if field == 'tags' and new_value:
            display_value = ', '.join(new_value)
        elif not new_value:
            display_value = "Удалено"
        
        await message.answer(
            f"✅ <b>Контакт обновлен</b>\n\n"
            f"👤 <b>Контакт:</b> {contact.name}\n"
            f"📝 <b>{field_names.get(field, field)}:</b> {display_value}\n\n"
            f"💡 Изменения сохранены",
            parse_mode="HTML"
        )
        
        # Показываем обновленную информацию о контакте
        await message.answer(
            f"📋 <b>Обновленная информация</b>\n\n{contact.format_display()}",
            reply_markup=create_contact_actions_menu(contact_id),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "❌ <b>Ошибка обновления</b>\n\n"
            "Не удалось сохранить изменения",
            parse_mode="HTML"
        )
    
    await state.clear()