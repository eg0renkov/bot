from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from utils.keyboards import keyboards
from utils.drafts_manager import drafts_manager
from utils.openai_client import openai_client

router = Router()

# Состояния для работы с черновиками
class DraftStates(StatesGroup):
    creating_to = State()
    creating_subject = State()
    creating_body = State()
    editing_draft = State()
    ai_composing = State()

@router.callback_query(F.data == "mail_drafts")
async def show_drafts(callback: CallbackQuery):
    """Показать список черновиков (первая страница)"""
    await show_drafts_page(callback, page=0)

@router.callback_query(F.data.startswith("drafts_page_"))
async def show_drafts_page_handler(callback: CallbackQuery):
    """Показать конкретную страницу черновиков"""
    page = int(callback.data.replace("drafts_page_", ""))
    await show_drafts_page(callback, page)

async def show_drafts_page(callback: CallbackQuery, page: int = 0):
    """Показать страницу черновиков с пагинацией"""
    user_id = callback.from_user.id
    
    # Получаем страницу черновиков
    page_data = await drafts_manager.get_drafts_page(user_id, page=page, per_page=5)
    
    if page_data['total_drafts'] == 0:
        await callback.message.edit_text(
            "📋 <b>Черновики</b>\n\n"
            "У вас пока нет черновиков.\n\n"
            "📝 <b>Создать черновик:</b>\n"
            "• Нажмите «✍️ Написать письмо»\n"
            "• Используйте AI для генерации\n"
            "• Сохраняйте письма на потом\n\n"
            "💡 <i>Черновики хранятся автоматически</i>",
            reply_markup=keyboards.mail_menu(),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    # Формируем текст заголовка
    text = f"📋 <b>Черновики ({page_data['total_drafts']})</b>\n"
    if page_data['total_pages'] > 1:
        text += f"📄 Страница {page + 1} из {page_data['total_pages']}\n"
    text += "\n"
    
    # Создаем клавиатуру с черновиками
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    
    # Добавляем кнопки черновиков (по 5 на странице)
    for i, draft in enumerate(page_data['drafts']):
        subject = draft.subject or "Без темы"
        recipient = draft.recipient_name or draft.recipient_email or "Без получателя"
        
        # Ограничиваем длину текста на кнопке
        button_text = f"📧 {subject[:15]}{'...' if len(subject) > 15 else ''}"
        if recipient and recipient != "Без получателя":
            button_text += f" → {recipient[:10]}{'...' if len(recipient) > 10 else ''}"
        
        builder.button(
            text=button_text,
            callback_data=f"draft_open_{draft.id}"
        )
    
    # Добавляем кнопки пагинации если нужно
    pagination_buttons = []
    if page_data['has_prev']:
        pagination_buttons.append(("◀️ Пред", f"drafts_page_{page - 1}"))
    if page_data['has_next']:
        pagination_buttons.append(("След ▶️", f"drafts_page_{page + 1}"))
    
    # Добавляем кнопки пагинации в ряд
    if pagination_buttons:
        for btn_text, btn_data in pagination_buttons:
            builder.button(text=btn_text, callback_data=btn_data)
    
    # Кнопки управления
    builder.button(text="✍️ Новый черновик", callback_data="draft_create_new")
    builder.button(text="◀️ К почте", callback_data="category_mail")
    
    # Настраиваем расположение кнопок
    # 5 черновиков (по одной в ряд), пагинация (в один ряд), управление (в один ряд)
    adjust_pattern = [1] * len(page_data['drafts'])  # Черновики
    if pagination_buttons:
        adjust_pattern.append(len(pagination_buttons))  # Пагинация
    adjust_pattern.extend([1, 1])  # Управление
    
    builder.adjust(*adjust_pattern)
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    
    await callback.answer()

@router.callback_query(F.data == "draft_create_new")
async def create_new_draft(callback: CallbackQuery):
    """Начать создание нового черновика через основной композер"""
    # Перенаправляем в основной composer
    from handlers.yandex_integration import mail_compose_handler
    
    # Создаем новый callback с данными для композера
    callback.data = "mail_compose"
    await mail_compose_handler(callback)
    
    await callback.answer()

@router.callback_query(F.data.startswith("draft_send_"))
async def send_draft(callback: CallbackQuery):
    """Отправить черновик как письмо"""
    draft_id = callback.data.replace("draft_send_", "")
    user_id = callback.from_user.id
    
    try:
        # Получаем черновик
        draft = await drafts_manager.get_draft_by_id(user_id, draft_id)
        
        if not draft:
            await callback.answer("❌ Черновик не найден", show_alert=True)
            return
        
        # Проверяем наличие обязательных полей
        if not draft.recipient_email:
            await callback.answer("❌ Не указан получатель", show_alert=True)
            return
        
        if not draft.subject:
            await callback.answer("❌ Не указана тема письма", show_alert=True)
            return
        
        if not draft.body:
            await callback.answer("❌ Письмо пустое", show_alert=True)
            return
        
        # Показываем подтверждение отправки
        from utils.html_utils import escape_html
        
        text = f"📤 <b>Отправка письма</b>\n\n"
        text += f"👤 <b>Кому:</b> {escape_html(draft.recipient_name or draft.recipient_email)}\n"
        text += f"📝 <b>Тема:</b> {escape_html(draft.subject)}\n\n"
        text += f"📄 <b>Текст:</b>\n{escape_html(draft.get_preview(200))}\n\n"
        text += "✅ Отправить это письмо?"
        
        # Создаем клавиатуру подтверждения
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        builder.button(text="✅ Да, отправить", callback_data=f"draft_confirm_send_{draft_id}")
        builder.button(text="❌ Отмена", callback_data=f"draft_open_{draft_id}")
        
        builder.adjust(2)
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)[:50]}...", show_alert=True)
    
    await callback.answer()

@router.callback_query(F.data.startswith("draft_confirm_send_"))
async def confirm_send_draft(callback: CallbackQuery):
    """Подтвердить отправку черновика"""
    draft_id = callback.data.replace("draft_confirm_send_", "")
    user_id = callback.from_user.id
    
    try:
        # Получаем черновик
        draft = await drafts_manager.get_draft_by_id(user_id, draft_id)
        
        if not draft:
            await callback.answer("❌ Черновик не найден", show_alert=True)
            return
        
        # Импортируем функцию отправки
        from handlers.yandex_integration import send_email
        from utils.user_settings import user_settings
        
        # Получаем имя отправителя
        sender_name = await user_settings.get_or_request_name(
            user_id, 
            callback.from_user.first_name
        )
        
        # Отправляем письмо
        success = await send_email(
            recipient_email=draft.recipient_email,
            subject=draft.subject,
            body=draft.body,
            sender_name=sender_name,
            user_id=user_id
        )
        
        if success:
            # Удаляем черновик после успешной отправки
            await drafts_manager.delete_draft(user_id, draft_id)
            
            await callback.message.edit_text(
                "✅ <b>Письмо отправлено!</b>\n\n"
                f"👤 Получатель: {draft.recipient_name or draft.recipient_email}\n"
                f"📝 Тема: {draft.subject}\n\n"
                "📋 Черновик автоматически удален",
                reply_markup=keyboards.back_button("category_mail"),
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                "❌ <b>Ошибка отправки письма</b>\n\n"
                "Проверьте настройки почты и попробуйте снова",
                reply_markup=create_draft_actions_keyboard(draft_id),
                parse_mode="HTML"
            )
        
    except Exception as e:
        await callback.answer(f"❌ Ошибка отправки: {str(e)[:50]}...", show_alert=True)
    
    await callback.answer()

# Старые обработчики удалены - используем основной email composer

@router.callback_query(F.data.startswith("draft_open_"))
async def open_draft(callback: CallbackQuery):
    """Открыть черновик"""
    draft_id = callback.data.replace("draft_open_", "")
    user_id = callback.from_user.id
    
    draft = await drafts_manager.get_draft_by_id(user_id, draft_id)
    
    if not draft:
        await callback.answer("❌ Черновик не найден", show_alert=True)
        return
    
    text = f"📧 <b>Черновик письма</b>\n\n"
    text += f"👤 <b>Кому:</b> {draft.recipient_name or draft.recipient_email or 'Не указано'}\n"
    text += f"📝 <b>Тема:</b> {draft.subject or 'Без темы'}\n"
    text += f"📅 <b>Создан:</b> {draft.created_at[:16] if draft.created_at else 'Неизвестно'}\n"
    text += f"🔄 <b>Обновлен:</b> {draft.updated_at[:16] if draft.updated_at else 'Неизвестно'}\n\n"
    
    # Показываем предпросмотр текста
    preview = draft.get_preview(500)
    text += f"📄 <b>Текст:</b>\n{preview}"
    
    if len(draft.body or '') > 500:
        text += "\n\n<i>... текст обрезан ...</i>"
    
    await callback.message.edit_text(
        text,
        reply_markup=create_draft_actions_keyboard(draft_id),
        parse_mode="HTML"
    )
    
    await callback.answer()

@router.callback_query(F.data.startswith("draft_edit_"))
async def edit_draft(callback: CallbackQuery, state: FSMContext):
    """Редактировать черновик"""
    draft_id = callback.data.replace("draft_edit_", "")
    
    await callback.message.edit_text(
        "✏️ <b>Редактирование черновика</b>\n\n"
        "Что вы хотите изменить?",
        reply_markup=create_edit_menu(draft_id),
        parse_mode="HTML"
    )
    
    await state.update_data(editing_draft_id=draft_id)
    await callback.answer()

@router.callback_query(F.data.startswith("draft_delete_"))
async def delete_draft(callback: CallbackQuery):
    """Удалить черновик"""
    draft_id = callback.data.replace("draft_delete_", "")
    
    # Показываем подтверждение
    await callback.message.edit_text(
        "🗑️ <b>Удаление черновика</b>\n\n"
        "Вы уверены, что хотите удалить этот черновик?\n\n"
        "⚠️ <i>Это действие нельзя отменить!</i>",
        reply_markup=create_delete_confirmation(draft_id),
        parse_mode="HTML"
    )
    
    await callback.answer()

@router.callback_query(F.data.startswith("draft_confirm_delete_"))
async def confirm_delete_draft(callback: CallbackQuery):
    """Подтвердить удаление черновика"""
    draft_id = callback.data.replace("draft_confirm_delete_", "")
    user_id = callback.from_user.id
    
    success = await drafts_manager.delete_draft(user_id, draft_id)
    if success:
        await callback.message.edit_text(
            "✅ <b>Черновик удален!</b>",
            reply_markup=keyboards.back_button("mail_drafts"),
            parse_mode="HTML"
        )
    else:
        await callback.answer("❌ Ошибка удаления", show_alert=True)

@router.callback_query(F.data == "draft_clear_old")
async def clear_old_drafts(callback: CallbackQuery):
    """Очистить старые черновики (заглушка)"""
    await callback.answer(
        "🗃️ Функция очистки в разработке",
        show_alert=True
    )

# Вспомогательные функции для клавиатур
def create_draft_actions_keyboard(draft_id: str):
    """Клавиатура действий с черновиком"""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    
    builder.button(text="✏️ Редактировать", callback_data=f"draft_edit_{draft_id}")
    builder.button(text="📤 Отправить", callback_data=f"draft_send_{draft_id}")
    builder.button(text="📋 Копировать", callback_data=f"draft_copy_{draft_id}")
    builder.button(text="🗑️ Удалить", callback_data=f"draft_delete_{draft_id}")
    builder.button(text="◀️ К черновикам", callback_data="mail_drafts")
    
    builder.adjust(2, 2, 1)
    return builder.as_markup()

def create_edit_menu(draft_id: str):
    """Меню редактирования черновика"""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    
    builder.button(text="👤 Изменить получателя", callback_data=f"draft_edit_to_{draft_id}")
    builder.button(text="📝 Изменить тему", callback_data=f"draft_edit_subject_{draft_id}")
    builder.button(text="📄 Изменить текст", callback_data=f"draft_edit_body_{draft_id}")
    builder.button(text="🤖 Улучшить с AI", callback_data=f"draft_improve_ai_{draft_id}")
    builder.button(text="◀️ Назад", callback_data=f"draft_open_{draft_id}")
    
    builder.adjust(2, 1, 1, 1)
    return builder.as_markup()

def create_delete_confirmation(draft_id: str):
    """Подтверждение удаления"""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    
    builder.button(text="✅ Да, удалить", callback_data=f"draft_confirm_delete_{draft_id}")
    builder.button(text="❌ Отмена", callback_data=f"draft_open_{draft_id}")
    
    builder.adjust(2)
    return builder.as_markup()