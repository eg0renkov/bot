import os
import aiofiles
from aiogram import Router, F
from aiogram.types import Message, Voice, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from utils.openai_client import openai_client
from database.memory import memory
from database.vector_memory import vector_memory
from config.settings import settings
from utils.keyboards import keyboards
from utils.email_sender import email_sender
from utils.temp_emails import temp_emails
from utils.email_improver import email_improver
from utils.web_search import web_searcher
import re

router = Router()

def fix_transcription_errors(text: str) -> str:
    """Исправляет типичные ошибки транскрипции голосовых сообщений"""
    if not text:
        return text
    
    # Словарь типичных ошибок распознавания
    corrections = {
        # Команды добавления
        "добавь туда": "добавь",
        "добавь сюда": "добавь", 
        "дописать туда": "дописать",
        "дописки туда": "дописать",
        "дописка туда": "дописать",
        
        # Команды изменения
        "измени туда": "измени",
        "замени туда": "замени",
        "поменяй туда": "поменяй",
        
        # Обращения
        "добры день": "добрый день",
        "добрый деня": "добрый день",
        "доброе утра": "доброе утро",
        "здравствуй те": "здравствуйте",
        
        # Другие типичные ошибки
        "с уважение": "с уважением",
        "с уважением.": "с уважением,",
    }
    
    result = text
    for error, correction in corrections.items():
        result = result.replace(error, correction)
    
    # Убираем лишние "туда" после команд редактирования
    import re
    result = re.sub(r'\b(добавь|дописать|измени|замени|поменяй)\s+туда\b', r'\1', result, flags=re.IGNORECASE)
    
    if result != text:
        print(f"DEBUG: Fixed transcription: '{text}' -> '{result}'")
    
    return result

class EmailStates(StatesGroup):
    editing_subject = State()
    editing_body = State()

# Убираем старый обработчик /start - теперь он в menu_handlers.py

@router.message(Command("clear"))
async def clear_history(message: Message):
    """Очистить историю диалога"""
    user_id = message.from_user.id
    memory.clear_history(user_id)
    await message.answer("✅ История диалога очищена!")

@router.message(Command("cancel"))
async def cancel_command(message: Message, state: FSMContext):
    """Отменить любое текущее состояние"""
    current_state = await state.get_state()
    
    if current_state:
        await state.clear()
        await message.answer(
            "❌ <b>Операция отменена</b>\n\n"
            "🔙 Все состояния очищены. Вы можете начать заново.",
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "ℹ️ <b>Нет активных операций</b>\n\n"
            "💡 Используйте /cancel только когда находитесь в процессе настройки.",
            parse_mode="HTML"
        )

@router.message(Command("help"))
async def help_command(message: Message):
    """Показать справку"""
    help_text = """
🆘 Справка по использованию бота:

💬 Текстовые сообщения:
Просто напишите мне любой текст, и я отвечу с помощью AI.

🎤 Голосовые сообщения:
Отправьте голосовое сообщение - я его распознаю и отвечу.

📝 Команды:
/start - начать работу
/clear - очистить историю
/cancel - отменить текущую операцию (настройку email/календаря)
/help - эта справка

🧠 Память:
Я запоминаю наш разговор и могу ссылаться на предыдущие сообщения.

❓ Проблемы?
Если что-то не работает, попробуйте команду /clear
    """
    await message.answer(help_text)

@router.message(F.voice)
async def handle_voice(message: Message):
    """Обработчик голосовых сообщений"""
    if not settings.VOICE_ENABLED:
        await message.answer("Голосовые сообщения отключены.")
        return
    
    try:
        # Уведомляем пользователя о начале обработки
        status_message = await message.answer("🎤 Обрабатываю голосовое сообщение...")
        
        # Получаем файл
        voice: Voice = message.voice
        file_info = await message.bot.get_file(voice.file_id)
        
        # Скачиваем файл
        voice_file_path = f"temp_voice_{message.from_user.id}.ogg"
        await message.bot.download_file(file_info.file_path, voice_file_path)
        
        # Транскрибируем
        transcribed_text = await openai_client.transcribe_audio(voice_file_path)
        
        # Исправляем типичные ошибки транскрипции
        transcribed_text = fix_transcription_errors(transcribed_text)
        
        # Удаляем временный файл
        if os.path.exists(voice_file_path):
            os.remove(voice_file_path)
        
        if not transcribed_text or transcribed_text == "Не удалось распознать речь.":
            await status_message.edit_text("❌ Не удалось распознать речь. Попробуйте еще раз.")
            return
        
        # Обновляем статус
        await status_message.edit_text(f"📝 Распознано: {transcribed_text}\n\n🤖 Генерирую ответ...")
        
        user_id = message.from_user.id
        user_name = message.from_user.first_name or "Пользователь"
        if message.from_user.last_name:
            user_name += f" {message.from_user.last_name}"
        
        # ПРИОРИТЕТ 1: Проверяем команды календаря (как в текстовом обработчике)
        calendar_command = await extract_calendar_command(transcribed_text)
        if calendar_command:
            print(f"DEBUG: Voice message detected as calendar command: {calendar_command}")
            await status_message.delete()
            return await handle_calendar_command(message, calendar_command, user_id)
        
        # ПРИОРИТЕТ 2: Проверяем команды создания email 
        email_info = await extract_email_info(transcribed_text, user_name)
        if email_info:
            print(f"DEBUG: Voice message detected as email creation command: {email_info}")
            # Здесь должна быть логика создания email, но пока просто логируем
            await status_message.edit_text("📧 Команда создания email распознана из голосового сообщения!")
            return
        
        # ПРИОРИТЕТ 3: Проверяем команды редактирования email (только если не календарь и не создание email)
        edit_command = await extract_email_edit_command(transcribed_text)
        if edit_command:
            print(f"DEBUG: Voice message detected as email edit command: {edit_command}")
            # Обрабатываем как команду редактирования email
            await status_message.delete()
            return await handle_email_edit_command(message, edit_command, user_id)
        
        # Если это обычное голосовое сообщение, обрабатываем как AI чат
        print(f"DEBUG: Voice message processed as regular AI chat")
        
        # Получаем историю
        history = memory.get_history(user_id, limit=10)
        
        # Подготавливаем сообщения для AI
        messages = openai_client.prepare_messages_with_context(transcribed_text, history)
        
        # Получаем ответ от AI
        ai_response = await openai_client.chat_completion(messages)
        
        # Сохраняем в память
        memory.save_message(user_id, transcribed_text, ai_response)
        
        # Отправляем ответ с кнопками быстрых действий
        print(f"DEBUG: Sending voice response with quick_actions keyboard")
        try:
            response_text = f"📝 Ваше сообщение: {transcribed_text}\n\n🤖 Мой ответ:\n{ai_response}"
            quick_keyboard = keyboards.quick_actions()
            print(f"DEBUG: Voice handler - Quick keyboard created")
            
            await status_message.edit_text(
                response_text,
                reply_markup=quick_keyboard,
                parse_mode="HTML"
            )
            print(f"DEBUG: Voice response sent successfully with keyboard")
        except Exception as keyboard_error:
            print(f"DEBUG: Error sending voice response with keyboard: {keyboard_error}")
            # Fallback без клавиатуры
            await status_message.edit_text(f"📝 Ваше сообщение: {transcribed_text}\n\n🤖 Мой ответ:\n{ai_response}")
        
        # TTS ПОЛНОСТЬЮ ОТКЛЮЧЕН - озвучка только по кнопке "🎤 Озвучить"
        print(f"DEBUG: TTS disabled, no automatic voice response sent")
        
    except Exception as e:
        print(f"Ошибка обработки голосового сообщения: {e}")
        await message.answer("❌ Произошла ошибка при обработке голосового сообщения.")

async def format_email_subject(raw_subject: str) -> str:
    """ИИ-форматирование темы письма - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    # Импортируем исправленную функцию
    from handlers.email_fix import format_email_subject_safe
    
    # Используем исправленную версию
    return await format_email_subject_safe(raw_subject)

async def extract_email_info(text: str, user_name: str = None) -> dict:
    """Извлечь информацию о письме из текста - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    # Импортируем исправленную функцию
    from handlers.email_fix import extract_email_info_fixed
    
    # Используем исправленную версию
    result = await extract_email_info_fixed(text, user_name)
    
    # Возвращаем в том же формате что ожидает старый код
    return result

async def extract_calendar_command(text: str) -> dict:
    """Извлечь команду создания события календаря"""
    text_lower = text.lower()
    print(f"DEBUG extract_calendar_command: text='{text}', text_lower='{text_lower}'")
    
    # Проверяем что это НЕ email команда (содержит @ символ)
    if '@' in text:
        print("DEBUG: Rejected - contains @ symbol")
        return None
    
    # ВАЖНО: Проверяем что это НЕ команда контакта
    contact_exclusions = ['контакт', 'номер', 'телефон', '+7', '+3', '+8', '+9']
    found_exclusions = [ex for ex in contact_exclusions if ex in text_lower]
    if found_exclusions:
        print(f"DEBUG: Rejected - found contact exclusions: {found_exclusions}")
        return None
    
    calendar_patterns = [
        # Паттерны с "добавь" и временем (более специфичные)
        r"добав[ьи].*(?:что\s+)?(?:сегодня|завтра|в\s+\w+)\s+(?:в\s+)?(\d{1,2}:?\d{0,2}?)\s*(.+)",
        r"добав[ьи].*(?:что\s+)?(.+)\s+(?:сегодня|завтра|в\s+\w+)\s+(?:в\s+)?(\d{1,2}:?\d{0,2}?)",
        
        # Паттерны со "встреча"
        r"встреча\s+(.+)",
        r"(.+)\s+встреча",
        
        # Паттерны с указанием времени
        r"(.+)\s+в\s+(\d{1,2}:?\d{0,2}?)",
        
        # Общие паттерны создания событий
        r"создай\s+событие\s+(.+)",
        r"запланируй\s+(.+)",
        r"напомни\s+(.+)",
        
        # УБРАЛИ общий паттерн r"добав[ьи].*(?:что\s+)?(.+)" который ловил все команды "добавь"
        # Теперь "добавь" работает только с конкретными временными указаниями выше
    ]
    
    # Проверяем календарные ключевые слова (но исключаем "добавь" как единственный признак)
    calendar_keywords = ['встреча', 'событие', 'запланируй', 'напомни', 'сегодня', 'завтра']
    has_calendar_keywords = any(word in text_lower for word in calendar_keywords)
    
    # Для команд с "добавь" требуем дополнительные календарные признаки
    if 'добавь' in text_lower and not has_calendar_keywords:
        return None
    
    if not has_calendar_keywords and 'добавь' not in text_lower:
        return None
    
    for pattern in calendar_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return {
                "text": text,
                "match": match.groups(),
                "is_calendar": True
            }
    
    return None

async def smart_email_edit(current_body: str, edit_command: str, edit_text: str) -> str:
    """AI-powered умное редактирование письма с анализом контекста"""
    
    # Используем AI для умного анализа команды редактирования
    ai_prompt = f"""Проанализируй команду редактирования письма и отредактируй письмо ТОЧНО по инструкции.

ТЕКУЩЕЕ ПИСЬМО:
{current_body}

КОМАНДА ПОЛЬЗОВАТЕЛЯ: {edit_command}
ТЕКСТ ДЛЯ ДОБАВЛЕНИЯ/ИЗМЕНЕНИЯ: {edit_text}

ПРАВИЛА РЕДАКТИРОВАНИЯ:
1. ОБРАЩЕНИЯ ("добрый день", "здравствуйте", "привет" + имя):
   - Заменяй существующее обращение в первой строке
   - Если обращения нет - добавляй в самое начало
   - Формат: "Добрый день, [Имя]!" или "Добрый день!" (без имени)
   - Правильно склоняй имена (Александр, а не "Александра")

2. ПОДПИСИ ("с уважением", "всего доброго" + имя):
   - Заменяй существующую подпись в конце
   - Если подписи нет - добавляй в конец
   - Формат: "С уважением,\\n[Имя]"

3. ОСНОВНОЙ ТЕКСТ:
   - "добавь" = добавить в подходящее место по смыслу
   - "замени" = найти похожий текст и заменить
   - "дописать" = добавить в конец основного текста

4. ФОРМАТИРОВАНИЕ:
   - Сохраняй структуру письма (абзацы, переносы строк)
   - Правильная пунктуация и заглавные буквы
   - Логичные переносы строк

ВАЖНО: Верни ТОЛЬКО отредактированный текст письма, без комментариев и объяснений."""

    try:
        messages = [{"role": "user", "content": ai_prompt}]
        result = await openai_client.chat_completion(messages, temperature=0.1)
        
        # Проверяем, что результат разумный
        if result and len(result.strip()) > 10:
            print(f"DEBUG: AI edit result: {result[:100]}...")
            return result.strip()
        else:
            print(f"DEBUG: AI edit failed, using fallback")
            return await _fallback_email_edit(current_body, edit_command, edit_text)
            
    except Exception as e:
        print(f"DEBUG: AI edit error: {e}")
        return await _fallback_email_edit(current_body, edit_command, edit_text)

async def _fallback_email_edit(current_body: str, edit_command: str, edit_text: str) -> str:
    """Простое резервное редактирование если AI не работает"""
    command_lower = edit_command.lower()
    
    # Простая логика для обращений
    greeting_words = ['добрый день', 'доброе утро', 'здравствуйте', 'привет']
    if any(word in edit_text.lower() for word in greeting_words):
        lines = current_body.split('\n')
        formatted_greeting = edit_text.strip()
        if not formatted_greeting.endswith(('!', '.')):
            formatted_greeting += '!'
        lines[0] = formatted_greeting
        return '\n'.join(lines)
    
    # Простая логика для подписей
    signature_words = ['с уважением', 'всего доброго', 'до свидания']
    if any(word in edit_text.lower() for word in signature_words):
        return f"{current_body}\n\n{edit_text}"
    
    # По умолчанию - добавляем в конец
    return f"{current_body}\n\n{edit_text}"

async def handle_email_edit_command(message, edit_command: dict, user_id: int):
    """Обработать команду редактирования email"""
    # Ищем последнее письмо пользователя
    latest_email = temp_emails.get_user_latest_email(user_id)
    
    if not latest_email:
        await message.answer(
            "✏️ <b>Команда редактирования распознана</b>\n\n"
            "❌ <b>Не найдено письмо для редактирования</b>\n\n"
            "💡 <b>Сначала создайте письмо:</b>\n"
            "\"напиши письмо email@example.com - об теме\"",
            parse_mode="HTML"
        )
        return
    
    # Редактируем письмо с умным анализом
    try:
        current_body = latest_email['body']
        edit_text = edit_command['text']
        original_command = edit_command['original_command']
        
        print(f"DEBUG: Smart editing - Command: '{original_command}', Text: '{edit_text}'")
        
        # Используем умное редактирование
        new_body = await smart_email_edit(current_body, original_command, edit_text)
        
        print(f"DEBUG: Smart editing result - Body length: {len(new_body)}")
        
        # Обновляем письмо
        temp_emails.update_email(latest_email['id'], body=new_body)
        
        # Показываем обновленный просмотр
        print(f"DEBUG: Getting updated email data...")
        updated_email = temp_emails.get_email(latest_email['id'])
        
        if updated_email:
            preview_text = temp_emails.format_email_preview(updated_email)
            preview_text += f"\n\n✅ <i>Письмо обновлено: {edit_command['original_command']}</i>"
            
            print(f"DEBUG: Creating keyboard for updated email...")
            email_keyboard = keyboards.email_confirm_menu(latest_email['id'])
            
            print(f"DEBUG: Sending updated email preview...")
            await message.answer(
                preview_text,
                reply_markup=email_keyboard,
                parse_mode="HTML"
            )
            print(f"DEBUG: Updated email preview sent successfully")
        else:
            print(f"DEBUG: Failed to get updated email data")
            await message.answer(
                "❌ Ошибка при получении обновленного письма",
                parse_mode="HTML"
            )
            
    except Exception as e:
        print(f"Ошибка редактирования email: {e}")
        await message.answer(
            "❌ <b>Ошибка при редактировании письма</b>\n\n"
            "Попробуйте еще раз или создайте новое письмо",
            parse_mode="HTML"
        )

async def handle_calendar_command(message: Message, calendar_command: dict, user_id: int):
    """Обработать команду создания события календаря"""
    try:
        # Проверяем подключение календаря
        from database.user_tokens import user_tokens
        token_data = await user_tokens.get_token_data(user_id, "calendar")
        
        print(f"DEBUG: Calendar token_data for user {user_id}: {token_data}")
        print(f"DEBUG: app_password exists: {token_data.get('app_password') if token_data else 'token_data is None'}")
        
        if not token_data or not token_data.get("app_password"):
            await message.answer(
                "📅 <b>Команда создания события распознана</b>\n\n"
                "❌ <b>Календарь не подключен</b>\n\n"
                "Для создания событий необходимо:\n"
                "1. Подключить Яндекс.Календарь\n"
                "2. Предоставить разрешения\n\n"
                "💡 Нажмите «📱 Меню» → «📅 Подключить Календарь»",
                parse_mode="HTML",
                reply_markup=keyboards.main_menu()
            )
            return
        
        await message.answer(
            "📅 <b>Команда создания события распознана!</b>\n\n"
            f"📝 <b>Ваша команда:</b> {calendar_command['text']}\n\n"
            "🤖 Обрабатываю с помощью ИИ...",
            parse_mode="HTML"
        )
        
        # Создаем событие с помощью ИИ анализа
        await create_calendar_event_from_text(message, calendar_command['text'], user_id, token_data)
        
    except Exception as e:
        print(f"Ошибка обработки календарной команды: {e}")
        await message.answer("❌ Произошла ошибка при обработке команды создания события.")

async def create_calendar_event_from_text(message: Message, text: str, user_id: int, token_data: dict):
    """Создать событие календаря на основе текста с помощью ИИ"""
    try:
        # Используем ИИ для парсинга события
        from utils.openai_client import openai_client
        from datetime import datetime, timedelta
        
        prompt = f"""Проанализируй текст и извлеки информацию о событии календаря:

Текст: "{text}"

Верни JSON в формате:
{{
    "title": "название события",
    "start_time": "YYYY-MM-DDTHH:MM:SS",
    "end_time": "YYYY-MM-DDTHH:MM:SS",
    "description": "описание"
}}

ПРАВИЛА ПАРСИНГА ВРЕМЕНИ:
- "в 15" = 15:00 (а не 12:00!)
- "в 14" = 14:00 
- "в 9" = 09:00
- "в 10 утра" = 10:00
- "в 15 часов" = 15:00
- "в полдень" = 12:00
- "в час дня" = 13:00
- "в 2 часа" = 14:00 (если не указано утро/день)

ПРАВИЛА ДАТЫ:
- "завтра" = завтрашняя дата
- "сегодня" = сегодняшняя дата  
- "послезавтра" = через 2 дня
- Если дата не указана, используй сегодня

ПРАВИЛА ПРОДОЛЖИТЕЛЬНОСТИ:
- По умолчанию событие длится 1 час
- Все времена в UTC+3 (московское время)
- Если год не указан, используй текущий: 2025
- Если время не указано, используй 10:00

Сегодня: {datetime.now().strftime('%Y-%m-%d %H:%M')}"""

        messages = [{"role": "user", "content": prompt}]
        ai_response = await openai_client.chat_completion(messages, temperature=0.1)
        
        # Парсим ответ ИИ
        try:
            import json
            event_data = json.loads(ai_response.strip().strip('```json').strip('```'))
        except:
            await message.answer("❌ Не удалось распознать событие. Попробуйте по-другому.")
            return
        
        # Получаем данные календаря (используем app_password, а не access_token)
        app_password = token_data.get("app_password")
        user_email = token_data.get("email", "user@yandex.ru")
        
        print(f"DEBUG: Creating calendar client with email: {user_email}, password exists: {bool(app_password)}")
        
        # Создаем событие (используем app_password вместо access_token)
        from handlers.yandex_integration import YandexCalendar
        calendar_client = YandexCalendar(app_password, user_email)
        success = await calendar_client.create_event(
            title=event_data.get("title", "Новое событие"),
            start_time=event_data.get("start_time"),
            end_time=event_data.get("end_time"),
            description=event_data.get("description", "")
        )
        
        if success:
            await message.answer(
                f"✅ <b>Событие создано!</b>\n\n"
                f"📌 <b>Название:</b> {event_data.get('title')}\n"
                f"⏰ <b>Время:</b> {event_data.get('start_time', '').replace('T', ' ')}\n"
                f"📝 <b>Описание:</b> {event_data.get('description', 'Без описания')}",
                parse_mode="HTML",
                reply_markup=keyboards.main_menu()
            )
        else:
            await message.answer(
                "❌ <b>Ошибка создания события</b>\n\n"
                "Возможные причины:\n"
                "• Неверный формат времени\n"
                "• Нет доступа к календарю\n"
                "• Токен устарел",
                parse_mode="HTML"
            )
        
    except Exception as e:
        print(f"Ошибка создания события по тексту: {e}")
        await message.answer("❌ Произошла ошибка при создании события.")

async def extract_email_edit_command(text: str) -> dict:
    """Извлечь команду редактирования email"""
    
    # ВАЖНО: Если текст содержит email адрес, это команда создания письма, а не редактирования!
    import re
    if re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text):
        print(f"DEBUG: Text contains email address, skipping edit command extraction")
        return None
    
    # ВАЖНО: Проверяем что это НЕ команда контакта
    text_lower = text.lower()
    contact_exclusions = ['контакт', 'номер', 'телефон', '+7', '+3', '+8', '+9']
    found_exclusions = [ex for ex in contact_exclusions if ex in text_lower]
    if found_exclusions:
        print(f"DEBUG: Email edit skipped - found contact exclusions: {found_exclusions}")
        return None
    
    # Сначала нормализуем текст для голосовых команд
    # Убираем лишние слова типа "пиши" в начале
    normalized_text = text.strip()
    if normalized_text.lower().startswith(('пиши,', 'пиши ', 'напиши,', 'напиши ')):
        # Удаляем слово "пиши" из начала
        parts = normalized_text.split(' ', 1)
        if len(parts) > 1:
            normalized_text = parts[1].strip()
            # Убираем лишнюю запятую
            if normalized_text.startswith(','):
                normalized_text = normalized_text[1:].strip()
    
    edit_patterns = [
        # Команды добавления/дописывания
        r"допиш[иь].*?(.+)",
        r"доба[вь].*?(.+)",
        r"дополн[иь].*?(.+)",
        r"добавь\s+(.+)",
        r"дописать\s+(.+)",
        r"дополнить\s+(.+)",
        r"приба[вь].*?(.+)",
        r"включ[иь].*?(.+)",
        r"вста[вь].*?(.+)",
        
        # Команды изменения/замены
        r"измен[иь].*?(.+)",
        r"замен[иь].*?(.+)",
        r"поменя[йь].*?(.+)",
        r"смен[иь].*?(.+)",
        r"обнов[иь].*?(.+)",
        
        # Команды исправления/редактирования
        r"исправ[ьи].*?(.+)",
        r"поправ[ьи].*?(.+)",
        r"откорректир.*?(.+)",
        r"редактир.*?(.+)",
        r"правк[аи].*?(.+)",
        
        # Команды переписывания
        r"перепиш[иь].*?(.+)",
        r"перефразир.*?(.+)",
        r"переформулир.*?(.+)",
        r"переработ.*?(.+)",
        
        # Команды улучшения
        r"улучш[иь].*?(.+)",
        r"доработа[йь].*?(.+)",
        r"усовершенств.*?(.+)",
        
        # Альтернативные формы
        r"сдела[йь].*?(.+)",
        r"напиш[иь].*?(еще|также|тоже|дополнительно).*?(.+)"
    ]
    
    # Проверяем оба варианта - исходный текст и нормализованный
    for text_to_check in [text, normalized_text]:
        for pattern in edit_patterns:
            match = re.search(pattern, text_to_check, re.IGNORECASE)
            if match:
                edit_text = match.group(1).strip()
                return {
                    "type": "edit",
                    "text": edit_text,
                    "original_command": text  # Всегда возвращаем исходную команду
                }
    
    # Проверяем, не является ли весь текст обращением после "пиши"
    if normalized_text != text and any(word in normalized_text.lower() for word in ['добрый день', 'доброе утро', 'здравствуйте']):
        return {
            "type": "edit",
            "text": normalized_text,
            "original_command": text
        }
    
    return None

async def extract_search_query(text: str) -> str:
    """Извлечь поисковый запрос из текста"""
    # Паттерны для поиска писем
    search_patterns = [
        r"найди письма от (.+)",
        r"найти письма от (.+)",
        r"найди письма (.+)",
        r"найти письма (.+)",
        r"поиск писем от (.+)",
        r"поиск писем (.+)",
        r"покажи письма от (.+)",
        r"покажи письма (.+)",
        r"письма от (.+)",
        r"ищи письма (.+)",
    ]
    
    for pattern in search_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            query = match.group(1).strip()
            # Убираем лишние слова
            query = re.sub(r'\b(письма|письмо|от|об|про|о|в|за|с)\b', '', query, flags=re.IGNORECASE).strip()
            return query if query else None
    
    return None

async def extract_web_search_query(text: str) -> dict:
    """Определить, является ли запрос веб-поиском и его тип"""
    text_lower = text.lower().strip()
    
    # Исключения - если это запрос на создание письма/календаря/контактов
    email_keywords = [
        'написать письмо', 'напиши письмо', 'отправить письмо', 'отправь письмо',
        'создать письмо', 'создай письмо', 'составить письмо', 'составь письмо',
        'email', 'мейл', 'почта'
    ]
    
    calendar_keywords = [
        'создать событие', 'создай событие', 'добавить событие', 'добавь событие',
        'календарь', 'встреча', 'напоминание'
    ]
    
    # Если запрос содержит команды создания письма или календаря - НЕ веб-поиск
    for keyword in email_keywords + calendar_keywords:
        if keyword in text_lower:
            return None
    
    # Ключевые слова для новостей
    news_keywords = [
        'новости', 'актуальные новости', 'свежие новости', 'последние новости',
        'что происходит', 'события сегодня', 'новости сегодня', 'новости на сегодня',
        'что нового', 'актуальная информация', 'сводка новостей', 'новостная сводка'
    ]
    
    # Ключевые слова для обычного поиска
    search_keywords = [
        'найди информацию', 'поищи информацию', 'найди в интернете', 'поиск в интернете',
        'что такое', 'расскажи о', 'информация о', 'найди данные о', 'поищи данные о',
        'актуальная информация о', 'последняя информация о'
    ]
    
    # Проверяем на новости
    for keyword in news_keywords:
        if keyword in text_lower:
            # Убираем ключевое слово и возвращаем остальное как запрос
            query = text_lower.replace(keyword, '').strip()
            if not query:
                query = 'последние новости'
            return {'type': 'news', 'query': query}
    
    # Проверяем на обычный поиск
    for keyword in search_keywords:
        if keyword in text_lower:
            query = text_lower.replace(keyword, '').strip()
            if query:
                return {'type': 'search', 'query': query}
    
    # Проверяем вопросительные конструкции, которые могут быть поиском
    question_patterns = [
        r'что такое (.+)\??',
        r'кто такой (.+)\??',
        r'кто такая (.+)\??', 
        r'где находится (.+)\??',
        r'как работает (.+)\??',
        r'сколько стоит (.+)\??',
        r'когда происходит (.+)\??',
        r'(.+) это что\??',
        r'актуальные (.+)\??',
        r'расскажи про (.+)',
        r'расскажи о (.+)',
        r'информация про (.+)',
        r'информация о (.+)'
    ]
    
    for pattern in question_patterns:
        match = re.search(pattern, text_lower)
        if match:
            query = match.group(1).strip()
            # Если упоминаются новости - это поиск новостей
            if 'новост' in query:
                return {'type': 'news', 'query': query}
            return {'type': 'search', 'query': query}
    
    # Дополнительная проверка на имена собственные и организации
    # Если сообщение содержит заглавные буквы в середине (признак имен/брендов)
    # и это вопросительное предложение или информационный запрос
    if (('?' in text or 'что' in text_lower or 'кто' in text_lower or 
         'где' in text_lower or 'как' in text_lower or 'расскажи' in text_lower) and
        re.search(r'[А-Я][а-я]+ [А-Я][а-я]+', text)):  # Имя Фамилия
        # Убираем вопросительные слова и возвращаем как поисковый запрос
        query = text.strip()
        return {'type': 'search', 'query': query}
    
    return None

def truncate_message(text: str, max_length: int = 3800) -> str:
    """Безопасно обрезать сообщение для Telegram"""
    if len(text) <= max_length:
        return text
    
    # Ищем последний полный результат перед лимитом
    lines = text.split('\n')
    result = ""
    
    for line in lines:
        if len(result + line + '\n') > max_length - 150:  # Оставляем место для сообщения об обрезке
            break
        result += line + '\n'
    
    result += "\n📝 _Результаты сокращены из-за ограничений Telegram (макс. 4096 символов)_\n\n💡 _Используйте более конкретные запросы для получения точных результатов_"
    
    return result

async def handle_web_search_command(message: Message, web_search_info: dict):
    """Обработать команду веб-поиска"""
    try:
        search_type = web_search_info['type']
        query = web_search_info['query']
        
        # Показываем статус поиска
        if search_type == 'news':
            status_msg = await message.answer(f"📰 Ищу новости: {query}\n\n⏳ Подождите...")
        else:
            status_msg = await message.answer(f"🔍 Выполняю поиск: {query}\n\n⏳ Подождите...")
        
        # Выполняем поиск
        try:
            if search_type == 'news':
                # Для общих запросов новостей используем сводку
                if query.strip() in ['последние новости', 'актуальные новости', '', 'сегодня', 'на сегодня']:
                    result = await web_searcher.get_daily_news_summary()
                else:
                    # Для конкретных запросов используем обычный поиск новостей
                    async with web_searcher:
                        news_results = await web_searcher.search_news(query, num_results=8)
                        
                        if not news_results:
                            result = f"📰 По запросу '{query}' новостей не найдено."
                        else:
                            result = f"📰 **Новости по запросу:** {query}\n\n"
                            
                            for i, news in enumerate(news_results[:5], 1):  # Показываем только 5 лучших
                                title = news.get('title', 'Без названия')[:100]
                                source = news.get('source', 'Неизвестный источник')
                                date = news.get('date', '')
                                snippet = news.get('snippet', '')[:120]
                                link = news.get('link', '')
                                
                                result += f"📰 **{i}. {title}**\n"
                                result += f"   📡 {source}"
                                if date:
                                    result += f" | 📅 {date}"
                                result += "\n"
                                if snippet:
                                    result += f"   {snippet}...\n"
                                if link:
                                    result += f"   🔗 [Ссылка на источник]({link})\n"
                                result += "\n"
            else:
                # Обычный поиск
                result = await web_searcher.quick_search(query)
            
            # Обрезаем результат если он слишком длинный
            result = truncate_message(result)
            
            # Создаем клавиатуру с дополнительными действиями
            keyboard = keyboards.search_results_menu()
            
            await status_msg.edit_text(
                text=result,
                reply_markup=keyboard,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
            
        except Exception as search_error:
            print(f"ERROR: Web search failed: {search_error}")
            await status_msg.edit_text(
                text=f"❌ Ошибка поиска: {search_error}",
                reply_markup=keyboards.back_button("menu_back")
            )
    
    except Exception as e:
        print(f"ERROR: handle_web_search_command: {e}")
        await message.answer("❌ Ошибка обработки веб-поиска")

@router.message(F.text)
async def handle_text_message(message: Message):
    """Обработчик текстовых сообщений"""
    print(f"🔥 HANDLER STARTED: handle_text_message called with text: '{message.text}'")
    try:
        user_id = message.from_user.id
        user_message = message.text
        
        # Получаем имя пользователя
        user_name = message.from_user.first_name or "Пользователь"
        if message.from_user.last_name:
            user_name += f" {message.from_user.last_name}"
        
        # Проверяем, является ли это командой создания события календаря (ПРИОРИТЕТ!)
        print(f"DEBUG: Checking calendar command for: '{user_message}'")
        calendar_command = await extract_calendar_command(user_message)
        print(f"DEBUG: Calendar command result: {calendar_command}")
        
        # Проверяем, является ли это командой отправки письма (ПРИОРИТЕТ НАД РЕДАКТИРОВАНИЕМ!)
        print(f"DEBUG: Checking for email command in text: '{user_message}'")
        email_info = await extract_email_info(user_message, user_name)
        print(f"DEBUG: Email extraction result: {email_info}")
        
        # Проверяем, является ли это командой редактирования email (ТОЛЬКО если не создание письма)
        edit_command = None
        if not email_info:
            print(f"DEBUG: Checking for email edit command in text: '{user_message}'")
            edit_command = await extract_email_edit_command(user_message)
            print(f"DEBUG: Email edit extraction result: {edit_command}")
        
        # Проверяем, является ли это командой поиска писем
        search_query = await extract_search_query(user_message)
        
        # Проверяем, является ли это веб-поисковым запросом
        web_search_info = await extract_web_search_query(user_message)
        
        if calendar_command:
            # Обрабатываем команду создания события календаря
            return await handle_calendar_command(message, calendar_command, user_id)
        
        if edit_command:
            # Используем общую функцию обработки редактирования
            return await handle_email_edit_command(message, edit_command, user_id)
        
        if web_search_info:
            # Обрабатываем веб-поиск
            return await handle_web_search_command(message, web_search_info)
        
        if search_query:
            # Проверяем, подключена ли почта
            if not await email_sender.can_send_email(user_id):
                await message.answer(
                    "🔍 <b>Для поиска писем нужно подключить Яндекс.Почту</b>\n\n"
                    "🔧 <b>Как подключить:</b>\n"
                    "1. Нажмите «📱 Меню»\n"
                    "2. Выберите «📧 Подключить Почту»\n"
                    "3. Пройдите авторизацию\n\n"
                    "💡 После подключения сможете искать письма!",
                    parse_mode="HTML",
                    reply_markup=keyboards.main_menu()
                )
                return
            
            try:
                # Показываем статус поиска
                from utils.html_utils import escape_html
                status_msg = await message.answer(f"🔍 Ищу письма по запросу: <b>{escape_html(search_query)}</b>\n\n⏳ Поиск...")
                
                # Выполняем поиск
                from utils.email_sender_real import real_email_sender
                search_results = await real_email_sender.search_emails(user_id, search_query, limit=10)
                
                # Сохраняем результаты для детального просмотра
                import json
                import os
                search_cache_dir = "data/search_cache"
                os.makedirs(search_cache_dir, exist_ok=True)
                
                cache_file = os.path.join(search_cache_dir, f"user_{user_id}_last_search.json")
                cache_data = {
                    'query': search_query,
                    'results': search_results,
                    'timestamp': __import__('datetime').datetime.now().isoformat()
                }
                
                try:
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        json.dump(cache_data, f, ensure_ascii=False, indent=2)
                except Exception as cache_error:
                    print(f"Ошибка сохранения кэша поиска: {cache_error}")
                
                if not search_results:
                    await status_msg.edit_text(
                        f"🔍 <b>Поиск завершен</b>\n\n"
                        f"📝 <b>Запрос:</b> {escape_html(search_query)}\n"
                        f"📭 <b>Результат:</b> Письма не найдены\n\n"
                        f"💡 <b>Попробуйте:</b>\n"
                        f"• Изменить запрос\n"
                        f"• Проверить правописание\n"
                        f"• Использовать другие ключевые слова",
                        parse_mode="HTML"
                    )
                    return
                
                # Формируем результаты поиска  
                from utils.html_utils import truncate_and_escape
                
                results_text = f"🔍 <b>Результаты поиска</b>\n\n"
                results_text += f"📝 <b>Запрос:</b> {escape_html(search_query)}\n"
                results_text += f"📬 <b>Найдено:</b> {len(search_results)} писем\n\n"
                
                for i, email_data in enumerate(search_results, 1):
                    sender = email_data.get('sender', 'Неизвестный отправитель')
                    subject = email_data.get('subject', 'Без темы')
                    date = email_data.get('date', '')
                    
                    # Экранируем и обрезаем длинные значения
                    sender_escaped = truncate_and_escape(sender, 25)
                    subject_escaped = truncate_and_escape(subject, 35)
                    
                    results_text += f"<b>{i}.</b> 👤 {sender_escaped}\n"
                    results_text += f"📝 {subject_escaped}\n"
                    if date:
                        results_text += f"🕐 {escape_html(str(date)[:16])}\n"
                    results_text += "\n"
                
                # Ограничиваем длину сообщения
                if len(results_text) > 3500:
                    results_text = results_text[:3500] + "\n\n..."
                
                # Создаем клавиатуру с кнопками
                from aiogram.utils.keyboard import InlineKeyboardBuilder
                builder = InlineKeyboardBuilder()
                
                # Кнопка детального просмотра
                builder.button(
                    text="📖 Детальный просмотр", 
                    callback_data=f"search_details_{len(search_results)}"
                )
                
                # Кнопка в меню входящих
                builder.button(
                    text="📨 К входящим", 
                    callback_data="mail_inbox"
                )
                
                # Кнопка новый поиск
                builder.button(
                    text="🔍 Новый поиск", 
                    callback_data="mail_search"
                )
                
                # Кнопка выхода
                builder.button(
                    text="❌ Выйти", 
                    callback_data="menu_back"
                )
                
                builder.adjust(1, 3)  # Первая кнопка отдельно, остальные в ряд
                
                await status_msg.edit_text(
                    results_text, 
                    parse_mode="HTML",
                    reply_markup=builder.as_markup()
                )
                return
                
            except Exception as e:
                await status_msg.edit_text(
                    f"❌ <b>Ошибка поиска писем</b>\n\n"
                    f"💥 <b>Проблема:</b> {escape_html(str(e)[:100])}...\n\n"
                    f"🔧 <b>Попробуйте позже или обратитесь в поддержку</b>",
                    parse_mode="HTML"
                )
                return
        
        if email_info:
            print(f"DEBUG: Email info detected: {email_info}")
            
            # Дополнительная валидация данных письма
            if not email_info.get('email') or not email_info.get('subject') or not email_info.get('body'):
                print(f"DEBUG: Invalid email_info data - missing required fields")
                await message.answer(
                    "❌ <b>Ошибка в данных письма</b>\n\n"
                    "🔧 <b>Проверьте что команда содержит:</b>\n"
                    "• Email адрес получателя\n"
                    "• Тему письма\n\n"
                    "💡 <b>Пример:</b>\n"
                    "\"отправь test@example.com о важной встрече\"",
                    parse_mode="HTML"
                )
                return
            
            # Проверяем что тело письма не пустое и не слишком короткое
            body_clean = email_info['body'].strip()
            if len(body_clean) < 10:
                print(f"DEBUG: Body too short: '{body_clean}' (length: {len(body_clean)})")
                await message.answer(
                    "❌ <b>Слишком короткое тело письма</b>\n\n"
                    "🔧 <b>Попробуйте:</b>\n"
                    "• Добавить больше деталей в команду\n"
                    "• Использовать более развернутую формулировку\n\n"
                    "💡 <b>Пример:</b>\n"
                    "\"отправь test@example.com о важной встрече завтра в 10 утра\"",
                    parse_mode="HTML"
                )
                return
            
            # Проверяем, подключена ли почта
            can_send = await email_sender.can_send_email(user_id)
            print(f"DEBUG: can_send_email result: {can_send}")
            
            if not can_send:
                print(f"DEBUG: Email not connected for user {user_id}")
                await message.answer(
                    "📧 <b>Для отправки писем нужно подключить Яндекс.Почту</b>\n\n"
                    "🔧 <b>Как подключить:</b>\n"
                    "1. Нажмите «📱 Меню»\n"
                    "2. Выберите «📧 Подключить Почту»\n"
                    "3. Пройдите авторизацию\n\n"
                    "💡 После подключения сможете отправлять письма!",
                    parse_mode="HTML",
                    reply_markup=keyboards.main_menu()
                )
                return
            else:
                print(f"DEBUG: Email IS connected for user {user_id}, proceeding with email creation...")
            try:
                # Автоматически улучшаем письмо с новым промптом
                status_msg = await message.answer("🤖 Обрабатываю письмо...")
                
                print(f"DEBUG: Starting email processing for user {user_id}")
                print(f"DEBUG: Email recipient: {email_info['email']}")
                print(f"DEBUG: Original subject: '{email_info['subject']}'")
                print(f"DEBUG: Original body length: {len(email_info['body'])}")
                print(f"DEBUG: Original body preview: '{email_info['body'][:100]}...'")
                
                # Убеждаемся что у нас есть валидные данные
                if not email_info['body'] or len(email_info['body'].strip()) < 5:
                    raise ValueError(f"Body is too short or empty: '{email_info['body']}'")
                
                # ОТКЛЮЧАЕМ автоматическое улучшение - пользователь может нажать кнопку "Улучшить письмо"
                print(f"DEBUG: Using original email content without auto-improvement")
                improved_subject = email_info["subject"] 
                improved_body = email_info["body"]
                
                # Создаем временное письмо
                print(f"DEBUG: Creating temp email...")
                print(f"DEBUG: Email data - to: {email_info['email']}, subject: {improved_subject}, body length: {len(improved_body)}")
                try:
                    email_id = temp_emails.create_email(
                        user_id=user_id,
                        to_email=email_info["email"],
                        subject=improved_subject,
                        body=improved_body
                    )
                    print(f"DEBUG: Temp email created with ID: {email_id}")
                except Exception as create_error:
                    print(f"DEBUG: Failed to create temp email: {create_error}")
                    import traceback
                    print(f"DEBUG: Full create email error: {traceback.format_exc()}")
                    raise create_error
                
                # Удаляем статусное сообщение
                await status_msg.delete()
                
                # Показываем предварительный просмотр
                print(f"DEBUG: Getting email data for preview...")
                try:
                    email_data = temp_emails.get_email(email_id)
                    if not email_data:
                        raise Exception(f"Failed to get email data for ID: {email_id}")
                    
                    preview_text = temp_emails.format_email_preview(email_data)
                    print(f"DEBUG: Preview text created, length: {len(preview_text)}")
                    
                    # Добавляем пометку об улучшении если было изменение
                    if improved_subject != email_info.get("original_subject", improved_subject) or \
                       improved_body != email_info.get("original_body", improved_body):
                        preview_text += "\n\n✨ <i>Письмо было автоматически улучшено AI</i>"
                    
                    print(f"DEBUG: Creating email confirm menu for email_id: {email_id}")
                    keyboard = keyboards.email_confirm_menu(email_id)
                    print(f"DEBUG: Keyboard created: {type(keyboard)}")
                    
                    print(f"DEBUG: Sending preview message...")
                    await message.answer(
                        preview_text,
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
                    print(f"DEBUG: Preview message sent successfully")
                    return  # ВАЖНО: Выходим из функции после отправки email
                    
                except Exception as preview_error:
                    print(f"DEBUG: Preview creation failed: {preview_error}")
                    raise preview_error
                
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                print(f"DEBUG: Full error traceback:")
                print(error_details)
                print(f"Ошибка обработки письма: {e}")
                
                # Удаляем статусное сообщение если оно есть
                try:
                    if 'status_msg' in locals():
                        await status_msg.delete()
                except:
                    pass
                
                await message.answer(
                    "❌ <b>Произошла ошибка при обработке письма</b>\n\n"
                    f"🔧 <b>Детали:</b> {str(e)[:200]}\n\n"
                    "💡 <b>Попробуйте:</b>\n"
                    "• Отправить команду еще раз\n"
                    "• Использовать более простую формулировку\n"
                    "• Проверить интернет-соединение",
                    parse_mode="HTML",
                    reply_markup=keyboards.main_menu()
                )
                return
        
        # Уведомляем о начале обработки
        status_message = await message.answer("🤖 Думаю...")
        
        # Используем векторную память если доступна
        if vector_memory:
            # Получаем расширенный контекст
            context = await vector_memory.get_enhanced_context(user_id, user_message, 5)
            
            # Подготавливаем сообщения с векторным контекстом
            messages = await prepare_messages_with_vector_context(user_message, context)
        else:
            # Используем обычную память
            history = memory.get_history(user_id, limit=10)
            messages = openai_client.prepare_messages_with_context(user_message, history)
        
        # Получаем ответ от AI
        ai_response = await openai_client.chat_completion(messages)
        
        # Проверяем вопросы об имени и личной информации ПЕРЕД отправкой ответа
        name_question_handled = await handle_name_questions(message, user_message, ai_response)
        if name_question_handled:
            return  # Выходим, так как вопрос об имени уже обработан
        
        # Проверяем, не просит ли пользователь добавить контакт
        await check_and_create_contact(message, user_message, ai_response)
        
        # Сохраняем в память
        if vector_memory:
            await vector_memory.save_conversation(user_id, user_message, ai_response)
            # Анализируем и извлекаем знания
            await vector_memory.analyze_and_extract_knowledge(user_id, f"{user_message} {ai_response}")
        else:
            memory.save_message(user_id, user_message, ai_response)
        
        # Отправляем ответ с кнопками быстрых действий
        print(f"DEBUG: Sending AI response with quick_actions keyboard")
        try:
            quick_keyboard = keyboards.quick_actions()
            print(f"DEBUG: Quick keyboard created: {quick_keyboard}")
            
            if len(ai_response) > settings.MAX_MESSAGE_LENGTH:
                # Если ответ слишком длинный, разбиваем на части
                parts = [ai_response[i:i+settings.MAX_MESSAGE_LENGTH] 
                        for i in range(0, len(ai_response), settings.MAX_MESSAGE_LENGTH)]
                
                print(f"DEBUG: Message too long, sending {len(parts)} parts")
                await status_message.edit_text(
                    parts[0], 
                    reply_markup=quick_keyboard,
                    parse_mode="HTML"
                )
                for part in parts[1:]:
                    await message.answer(part, parse_mode="HTML")
            else:
                print(f"DEBUG: Sending single message with keyboard")
                await status_message.edit_text(
                    ai_response,
                    reply_markup=quick_keyboard,
                    parse_mode="HTML"
                )
                print(f"DEBUG: Message sent successfully with keyboard")
        except Exception as keyboard_error:
            print(f"DEBUG: Error sending message with keyboard: {keyboard_error}")
            # Fallback без клавиатуры
            await status_message.edit_text(ai_response, parse_mode="HTML")
        
        # TTS убран - озвучка только по запросу или для голосовых сообщений
        print(f"DEBUG: Текстовый ответ отправлен без автоматической озвучки")
            
    except Exception as e:
        print(f"Ошибка обработки текстового сообщения: {e}")
        await message.answer("❌ Произошла ошибка при обработке сообщения. Попробуйте еще раз.")

async def prepare_messages_with_vector_context(current_message: str, context: dict) -> list:
    """Подготовить сообщения с векторным контекстом"""
    messages = [
        {
            "role": "system",
            "content": """Ты полезный AI-ассистент с долгосрочной памятью. 
            Используй предоставленный контекст для более персонализированных ответов.
            Отвечай на русском языке естественно и дружелюбно.
            Если есть релевантная информация из прошлых разговоров, используй её."""
        }
    ]
    
    # Добавляем контекст из базы знаний
    if context.get('knowledge_base'):
        knowledge_text = "Важная информация о пользователе:\n"
        for kb in context['knowledge_base']:
            knowledge_text += f"- {kb['topic']}: {kb['content']}\n"
        
        messages.append({
            "role": "system", 
            "content": knowledge_text
        })
    
    # Добавляем похожие разговоры
    if context.get('similar_conversations'):
        similar_text = "Похожие темы из прошлого:\n"
        for conv in context['similar_conversations'][:2]:  # Только первые 2
            similar_text += f"Пользователь спрашивал: {conv['user_message'][:100]}...\n"
            similar_text += f"Ответ был: {conv['ai_response'][:100]}...\n\n"
        
        messages.append({
            "role": "system",
            "content": similar_text
        })
    
    # Добавляем недавнюю историю
    for item in context.get('recent_history', []):
        if item.get('user_message'):
            messages.append({
                "role": "user",
                "content": item['user_message']
            })
        if item.get('ai_response'):
            messages.append({
                "role": "assistant",
                "content": item['ai_response']
            })
    
    # Добавляем текущее сообщение
    messages.append({
        "role": "user",
        "content": current_message
    })
    
    return messages

def correct_name_case(name: str) -> str:
    """Исправляет склонение русских имен в именительный падеж"""
    if not name:
        return name
    
    # Словарь частых окончаний русских имен в разных падежах
    name_corrections = {
        # Мужские имена
        'александра': 'Александр',
        'леонида': 'Леонид', 
        'владимира': 'Владимир',
        'дмитрия': 'Дмитрий',
        'сергея': 'Сергей',
        'андрея': 'Андрей',
        'алексея': 'Алексей',
        'николая': 'Николай',
        'михаила': 'Михаил',
        'павла': 'Павел',
        'игоря': 'Игорь',
        'олега': 'Олег',
        'антона': 'Антон',
        'романа': 'Роман',
        'максима': 'Максим',
        'артема': 'Артем',
        'ивана': 'Иван',
        'петра': 'Петр',
        'юрия': 'Юрий',
        'виктора': 'Виктор',
        'евгения': 'Евгений',
        'константина': 'Константин',
        'валерия': 'Валерий',
        
        # Женские имена
        'анны': 'Анна',
        'елены': 'Елена', 
        'марии': 'Мария',
        'ольги': 'Ольга',
        'татьяны': 'Татьяна',
        'наталии': 'Наталия',
        'наталье': 'Наталья',
        'светланы': 'Светлана',
        'ирины': 'Ирина',
        'людмилы': 'Людмила',
        'галины': 'Галина',
        'валентины': 'Валентина',
        'нины': 'Нина',
        'любови': 'Любовь',
        'екатерины': 'Екатерина',
        'алены': 'Алена',
        'юлии': 'Юлия',
        'анастасии': 'Анастасия',
        'дарьи': 'Дарья',
        'веры': 'Вера',
        'надежды': 'Надежда',
        'софии': 'София',
        'виктории': 'Виктория'
    }
    
    name_lower = name.lower().strip()
    
    # Проверяем точное совпадение
    if name_lower in name_corrections:
        return name_corrections[name_lower]
    
    # Проверяем по паттернам окончаний
    if name_lower.endswith('а') and len(name_lower) > 3:
        # Мужские имена на -а (Леонида -> Леонид)
        base_name = name_lower[:-1]
        if base_name + 'а' in name_corrections:
            return name_corrections[base_name + 'а']
        # Попробуем добавить "д" (Леонида -> Леонид)
        if not base_name.endswith('д'):
            test_name = base_name + 'д'
            if test_name.capitalize() in ['Леонид', 'Давид', 'Эдуард']:
                return test_name.capitalize()
    
    # Если не нашли соответствие, просто делаем первую букву заглавной
    return name.strip().capitalize()

async def check_and_create_contact(message: Message, user_message: str, ai_response: str):
    """Проверяет сообщения пользователя и ответы AI на предмет создания контактов"""
    try:
        user_id = message.from_user.id
        
        # Паттерны для обнаружения команд создания контактов
        contact_patterns = [
            # Основные команды с именем и номером телефона
            r"добав[ьи]\s+контакт\s+([А-Яа-я]+(?:\s+[А-Яа-я]+)*)\s+(\+?[0-9\-\(\)\s]{7,15})",
            r"создай\s+контакт\s+([А-Яа-я]+(?:\s+[А-Яа-я]+)*)\s+(\+?[0-9\-\(\)\s]{7,15})",
            r"сохрани\s+контакт\s+([А-Яа-я]+(?:\s+[А-Яа-я]+)*)\s+(\+?[0-9\-\(\)\s]{7,15})",
            r"запиши\s+контакт\s+([А-Яа-я]+(?:\s+[А-Яа-я]+)*)\s+(\+?[0-9\-\(\)\s]{7,15})",
            
            # С именем и email
            r"добав[ьи]\s+контакт\s+([А-Яа-я]+(?:\s+[А-Яа-я]+)*)\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
            r"создай\s+контакт\s+([А-Яа-я]+(?:\s+[А-Яа-я]+)*)\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
            
            # Основные команды только с именем (fallback)
            r"добав[ьи]\s+контакт\s+(.+)",
            r"создай\s+контакт\s+(.+)",
            r"сохрани\s+контакт\s+(.+)",
            r"запиши\s+контакт\s+(.+)",
            r"новый\s+контакт\s+(.+)",
            
            # Представление себя (для создания профиля пользователя)
            r"меня\s+зовут\s+(.+)",
            r"мое\s+имя\s+(.+)",
            r"я\s+([А-Яа-я]{2,}(?:\s+[А-Яа-я]{2,})*)",
            
            # Старые паттерны для обратной совместимости
            r"добав[ьи]\s+(.+?)\s*[-–—]\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
            r"контакт\s+(.+?)\s*[-–—]\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
            
            # Просто имя и email через пробел
            r"([А-Яа-я]{2,}(?:\s+[А-Яа-я]{2,})*)\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"
        ]
        
        import re
        
        # Проверяем сообщение пользователя
        for pattern in contact_patterns:
            match = re.search(pattern, user_message, re.IGNORECASE)
            if match:
                print(f"DEBUG: Contact creation pattern matched: {pattern}")
                
                if len(match.groups()) >= 2:
                    # Есть и имя и второй параметр (email или телефон)
                    name = match.group(1).strip()
                    second_param = match.group(2).strip() if match.group(2) else None
                    
                    # Определяем, что во второй группе - email или телефон
                    if second_param and '@' in second_param:
                        # Это email
                        email = second_param.strip()
                        phone = None
                    elif second_param and (second_param.startswith('+') or re.match(r'^[0-9\-\(\)\s]+$', second_param)):
                        # Это номер телефона
                        phone = second_param.strip()
                        email = None
                        print(f"DEBUG: Detected phone number: '{phone}'")
                    elif '@' in match.group(1):
                        # Email в первой группе, парсим по-другому
                        parts = match.group(1).strip().split()
                        email_part = None
                        name_parts = []
                        
                        for part in parts:
                            if '@' in part:
                                email_part = part
                            else:
                                name_parts.append(part)
                        
                        name = ' '.join(name_parts).strip()
                        email = email_part
                        phone = None
                    else:
                        email = None
                        phone = None
                else:
                    # Только один параметр - парсим его
                    contact_text = match.group(1).strip()
                    
                    # Пытаемся найти email в тексте
                    email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', contact_text)
                    
                    # Пытаемся найти телефон в тексте
                    phone_match = re.search(r'(\+?[0-9\-\(\)\s]{7,15})', contact_text)
                    
                    if email_match:
                        email = email_match.group(1)
                        phone = None
                        # Имя - это всё остальное
                        name = contact_text.replace(email, '').strip()
                        # Убираем лишние символы
                        name = re.sub(r'[-–—\s]+$', '', name).strip()
                    elif phone_match:
                        phone = phone_match.group(1)
                        email = None
                        print(f"DEBUG: Fallback detected phone: '{phone}'")
                        # Имя - это всё остальное
                        name = contact_text.replace(phone, '').strip()
                        # Убираем лишние символы
                        name = re.sub(r'[-–—\s]+$', '', name).strip()
                    else:
                        # Нет email и телефона, только имя
                        name = contact_text
                        email = None
                        phone = None
                
                if name and len(name) > 1:
                    # Исправляем склонение имен перед созданием контакта
                    corrected_name = correct_name_case(name)
                    
                    # Проверяем, это представление себя или создание контакта для другого
                    is_self_introduction = any(re.search(pattern, user_message, re.IGNORECASE) for pattern in [
                        r"меня\s+зовут", r"мое\s+имя", r"я\s+"
                    ])
                    
                    await create_contact_from_text(message, corrected_name, email, user_id, is_self_introduction, phone)
                    return True
        
        # Проверяем ответ AI на наличие информации о контактах
        ai_patterns = [
            r"создал\s+контакт\s+(.+)",
            r"добавил\s+контакт\s+(.+)",
            r"сохранил\s+контакт\s+(.+)",
            r"контакт\s+(.+?)\s+создан",
            r"контакт\s+(.+?)\s+добавлен"
        ]
        
        for pattern in ai_patterns:
            match = re.search(pattern, ai_response, re.IGNORECASE)
            if match:
                print(f"DEBUG: AI response indicates contact creation: {match.group(1)}")
                # AI подтвердил создание контакта, но не создаём дубликат
                return True
        
        return False
        
    except Exception as e:
        print(f"Ошибка проверки создания контакта: {e}")
        return False

async def handle_name_questions(message: Message, user_message: str, ai_response: str) -> bool:
    """Обрабатывает вопросы об имени и личной информации"""
    try:
        user_id = message.from_user.id
        
        # Паттерны вопросов об имени
        name_question_patterns = [
            r"как\s+меня\s+зовут",
            r"как\s+мое\s+имя",
            r"какое\s+мое\s+имя",
            r"как\s+меня\s+звать",
            r"мое\s+имя",
            r"знаешь\s+мое\s+имя",
            r"помнишь\s+мое\s+имя",
            r"как\s+меня\s+называть",
            r"знаешь.*как.*зовут",
            r"помнишь.*как.*зовут"
        ]
        
        import re
        user_message_lower = user_message.lower()
        
        # Проверяем, задает ли пользователь вопрос об имени
        is_name_question = any(re.search(pattern, user_message_lower) for pattern in name_question_patterns)
        
        if not is_name_question:
            return False
            
        # Проверяем, есть ли у пользователя уже сохраненная информация об имени
        from database.contacts import contacts_manager
        
        # Ищем контакты пользователя или информацию в памяти
        user_contacts = await contacts_manager.get_all_contacts(user_id)
        user_contact = None
        
        # Ищем контакт с пометкой "личная информация" или похожим
        for contact in user_contacts:
            if contact.notes and ("личная информация" in contact.notes.lower() or 
                                "мое имя" in contact.notes.lower() or
                                "пользователь" in contact.notes.lower()):
                user_contact = contact
                break
        
        if user_contact:
            # У пользователя есть сохраненная информация
            await message.answer(
                f"👋 <b>Привет, {user_contact.name}!</b>\n\n"
                f"✅ <b>Я помню тебя!</b>\n\n"
                f"📝 <b>Информация о тебе:</b>\n"
                f"👤 <b>Имя:</b> {user_contact.name}\n"
                + (f"📧 <b>Email:</b> {user_contact.email}\n" if user_contact.email else "") +
                + (f"📱 <b>Телефон:</b> {user_contact.phone}\n" if user_contact.phone else "") +
                + (f"📝 <b>Заметки:</b> {user_contact.notes}\n" if user_contact.notes else "") +
                f"\n💡 <b>Хочешь обновить информацию?</b> Просто скажи: \"Меня зовут [новое имя]\"",
                parse_mode="HTML"
            )
        else:
            # У пользователя нет сохраненной информации - предлагаем познакомиться
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()
            
            builder.button(text="👋 Давай знакомиться!", callback_data="introduce_myself")
            builder.button(text="📝 Сохранить имя сейчас", callback_data="save_name_now")
            builder.button(text="🤖 Просто общаться", callback_data="just_chat")
            
            builder.adjust(1, 1, 1)
            
            await message.answer(
                f"👋 <b>Привет!</b>\n\n"
                f"😊 <b>Я пока не знаю, как тебя зовут, но с радостью познакомлюсь!</b>\n\n"
                f"🤝 <b>Я умею:</b>\n"
                f"• 📝 Запоминать твое имя и контактную информацию\n"
                f"• 👥 Управлять контактами\n"
                f"• 📧 Отправлять письма\n"
                f"• 📅 Работать с календарем\n"
                f"• 🧠 Запоминать наши разговоры\n\n"
                f"💡 <b>Что хочешь сделать?</b>",
                parse_mode="HTML",
                reply_markup=builder.as_markup()
            )
        
        # Сохраняем в память корректную информацию
        if vector_memory:
            corrected_response = f"Пользователь спросил о своем имени. {'Я знаю его имя: ' + user_contact.name if user_contact else 'Я предложил познакомиться.'}"
            await vector_memory.save_conversation(user_id, user_message, corrected_response)
        else:
            from database.memory import memory
            corrected_response = f"Пользователь спросил о своем имени. {'Я знаю его имя: ' + user_contact.name if user_contact else 'Я предложил познакомиться.'}"
            memory.save_message(user_id, user_message, corrected_response)
        
        return True
        
    except Exception as e:
        print(f"Ошибка обработки вопроса об имени: {e}")
        return False

async def create_contact_from_text(message: Message, name: str, email: str, user_id: int, is_self_introduction: bool = False, phone: str = None):
    """Создает контакт на основе извлеченных данных"""
    try:
        # Импортируем необходимые модули
        from database.contacts import contacts_manager, Contact
        
        # Очищаем и валидируем данные
        name = name.strip()
        if not name or len(name) < 2:
            await message.answer("❌ Имя контакта слишком короткое")
            return False
        
        # Проверяем email если есть
        if email:
            email = email.strip().lower()
            import re
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                await message.answer(f"❌ Некорректный email адрес: {email}")
                return False
        
        # Проверяем, не существует ли уже такой контакт
        existing_contacts = await contacts_manager.search_contacts(user_id, name)
        
        if existing_contacts:
            for contact in existing_contacts:
                if contact.name.lower() == name.lower():
                    await message.answer(
                        f"ℹ️ <b>Контакт уже существует</b>\n\n"
                        f"👤 <b>Имя:</b> {contact.name}\n"
                        f"📧 <b>Email:</b> {contact.email or 'не указан'}\n"
                        f"📱 <b>Телефон:</b> {contact.phone or 'не указан'}\n\n"
                        f"💡 Используйте другое имя или отредактируйте существующий контакт.",
                        parse_mode="HTML"
                    )
                    return False
        
        # Определяем тип контакта и заметки
        if is_self_introduction:
            notes = "Личная информация пользователя - мое имя"
            contact_type = "профиль пользователя"
        else:
            notes = "Создан автоматически из сообщения"
            contact_type = "контакт"
        
        # Создаем объект контакта
        new_contact = Contact(
            name=name,
            email=email or '',
            phone=phone or '',
            notes=notes
        )
        
        print(f"DEBUG: Creating contact - name: '{name}', email: '{email}', phone: '{phone}'")
        
        # Добавляем контакт в базу
        success = await contacts_manager.add_contact(user_id, new_contact)
        contact_id = new_contact.id if success else None
        
        if contact_id:
            if is_self_introduction:
                success_message = f"🎉 <b>Приятно познакомиться, {name}!</b>\n\n"
                success_message += f"✅ <b>Я запомнил твою информацию:</b>\n"
                success_message += f"👤 <b>Имя:</b> {name}\n"
                
                if email:
                    success_message += f"📧 <b>Email:</b> {email}\n"
                
                success_message += f"\n🤖 <b>Теперь я буду обращаться к тебе по имени!</b>\n"
                success_message += f"💡 <b>Чтобы обновить информацию, скажи:</b> \"Меня зовут [новое имя]\""
            else:
                success_message = f"✅ <b>Контакт создан!</b>\n\n"
                success_message += f"👤 <b>Имя:</b> {name}\n"
                
                if email:
                    success_message += f"📧 <b>Email:</b> {email}\n"
                
                if phone:
                    success_message += f"📱 <b>Телефон:</b> {phone}\n"
                
                success_message += f"\n💡 Найти контакт: Меню → 👥 Контакты"
            
            # Создаем клавиатуру с действиями
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()
            
            if is_self_introduction:
                builder.button(text="📱 Меню", callback_data="menu_back")
                builder.button(text="✏️ Обновить информацию", callback_data=f"contact_edit_{contact_id}")
                if email:
                    builder.button(text="📧 Написать себе письмо", callback_data=f"contact_email_{email}")
                builder.adjust(1, 1, 1)
            else:
                builder.button(text="👥 К контактам", callback_data="contacts_menu")
                builder.button(text="✏️ Редактировать", callback_data=f"contact_edit_{contact_id}")
                if email:
                    builder.button(text="📧 Написать письмо", callback_data=f"contact_email_{email}")
                builder.adjust(2, 1)
            
            await message.answer(
                success_message,
                parse_mode="HTML",
                reply_markup=builder.as_markup()
            )
            
            print(f"DEBUG: Contact created successfully - ID: {contact_id}, Name: {name}, Email: {email}, Phone: {phone}")
            return True
        else:
            await message.answer("❌ Ошибка при создании контакта")
            return False
            
    except Exception as e:
        print(f"Ошибка создания контакта: {e}")
        await message.answer(
            f"❌ <b>Ошибка создания контакта</b>\n\n"
            f"🔧 <b>Причина:</b> {str(e)[:100]}\n\n"
            f"💡 Попробуйте создать контакт через меню: 👥 Контакты",
            parse_mode="HTML"
        )
        return False

# Обработчики кнопок подтверждения писем
@router.callback_query(F.data.startswith("email_send_"))
async def send_email_callback(callback: CallbackQuery):
    """Отправить письмо"""
    email_id = callback.data.split("_")[-1]
    email_data = temp_emails.get_email(email_id)
    
    if not email_data:
        await callback.answer("❌ Письмо не найдено", show_alert=True)
        return
    
    # Проверяем права пользователя
    if email_data["user_id"] != callback.from_user.id:
        await callback.answer("❌ Нет доступа к письму", show_alert=True)
        return
    
    # Отправляем письмо
    success = await email_sender.send_email(
        user_id=email_data["user_id"],
        to_email=email_data["to_email"],
        subject=email_data["subject"],
        body=email_data["body"]
    )
    
    if success:
        await callback.message.edit_text(
            f"✅ <b>Письмо отправлено!</b>\n\n"
            f"📧 <b>Кому:</b> {email_data['to_email']}\n"
            f"📝 <b>Тема:</b> {email_data['subject']}\n"
            f"💌 <b>Текст:</b> {email_data['body'][:150]}{'...' if len(email_data['body']) > 150 else ''}",
            parse_mode="HTML"
        )
        # Удаляем временное письмо
        temp_emails.delete_email(email_id)
    else:
        await callback.message.edit_text("❌ Ошибка отправки письма. Попробуйте позже.")
    
    await callback.answer()

@router.callback_query(F.data.startswith("email_edit_subject_"))
async def edit_subject_callback(callback: CallbackQuery, state: FSMContext):
    """Редактировать тему письма"""
    email_id = callback.data.split("_")[-1]
    email_data = temp_emails.get_email(email_id)
    
    if not email_data or email_data["user_id"] != callback.from_user.id:
        await callback.answer("❌ Письмо не найдено", show_alert=True)
        return
    
    # Создаем клавиатуру с кнопкой "Назад"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад к письму", callback_data=f"email_back_{email_id}")]
    ])
    
    await callback.message.edit_text(
        f"✏️ <b>Редактирование темы письма</b>\n\n"
        f"📧 <b>Кому:</b> {email_data['to_email']}\n"
        f"📝 <b>Текущая тема:</b> {email_data['subject']}\n\n"
        f"💡 Напишите новую тему письма:",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    
    await state.set_state(EmailStates.editing_subject)
    await state.update_data(email_id=email_id)
    await callback.answer()

@router.callback_query(F.data.startswith("email_edit_body_"))
async def edit_body_callback(callback: CallbackQuery, state: FSMContext):
    """Редактировать текст письма"""
    email_id = callback.data.split("_")[-1]
    email_data = temp_emails.get_email(email_id)
    
    if not email_data or email_data["user_id"] != callback.from_user.id:
        await callback.answer("❌ Письмо не найдено", show_alert=True)
        return
    
    # Создаем клавиатуру с кнопкой "Назад"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад к письму", callback_data=f"email_back_{email_id}")]
    ])
    
    await callback.message.edit_text(
        f"📝 <b>Редактирование текста письма</b>\n\n"
        f"📧 <b>Кому:</b> {email_data['to_email']}\n"
        f"📝 <b>Тема:</b> {email_data['subject']}\n\n"
        f"💌 <b>Текущий текст:</b>\n{email_data['body']}\n\n"
        f"💡 Напишите новый текст письма:",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    
    await state.set_state(EmailStates.editing_body)
    await state.update_data(email_id=email_id)
    await callback.answer()

@router.callback_query(F.data.startswith("email_save_draft_"))
async def save_draft_callback(callback: CallbackQuery):
    """Сохранить письмо в черновики"""
    try:
        email_id = callback.data.split("_")[-1]
        email_data = temp_emails.get_email(email_id)
        
        if not email_data or email_data["user_id"] != callback.from_user.id:
            await callback.answer("❌ Письмо не найдено", show_alert=True)
            return
        
        # Импортируем здесь, чтобы избежать циклических импортов
        from database.drafts import drafts_manager
        
        # Сохраняем в черновики
        draft_data = {
            "to": email_data["to_email"],
            "subject": email_data["subject"],
            "body": email_data["body"]
        }
        draft_id = drafts_manager.create_draft(email_data["user_id"], draft_data)
        
        await callback.message.edit_text(
            f"💾 <b>Письмо сохранено в черновики!</b>\n\n"
            f"📧 <b>Кому:</b> {email_data['to_email']}\n"
            f"📝 <b>Тема:</b> {email_data['subject']}\n"
            f"🆔 <b>ID черновика:</b> {draft_id}\n\n"
            f"💡 Вы можете найти его в разделе 'Черновики' через меню.",
            parse_mode="HTML"
        )
        
        # Удаляем временное письмо
        temp_emails.delete_email(email_id)
        await callback.answer("✅ Сохранено в черновики!")
        
    except Exception as e:
        print(f"Ошибка сохранения в черновики: {e}")
        await callback.answer("❌ Ошибка сохранения", show_alert=True)

@router.callback_query(F.data.startswith("email_improve_"))
async def improve_email_callback(callback: CallbackQuery):
    """Улучшить письмо с помощью AI"""
    email_id = callback.data.split("_")[-1]
    email_data = temp_emails.get_email(email_id)
    
    if not email_data or email_data["user_id"] != callback.from_user.id:
        await callback.answer("❌ Письмо не найдено", show_alert=True)
        return
    
    # Показываем статус улучшения
    await callback.message.edit_text(
        "🤖 <b>Улучшаю письмо с помощью AI...</b>\n\n"
        "⏳ Исправляю грамматику, пунктуацию и стиль...",
        parse_mode="HTML"
    )
    
    try:
        # Улучшаем письмо
        improved_subject, improved_body = await email_improver.improve_email(
            email_data["subject"], 
            email_data["body"]
        )
        
        # Обновляем письмо
        temp_emails.update_email(email_id, subject=improved_subject, body=improved_body)
        email_data = temp_emails.get_email(email_id)
        
        # Показываем улучшенный предварительный просмотр
        preview_text = temp_emails.format_email_preview(email_data)
        preview_text += "\n\n✨ <i>Письмо улучшено AI: исправлена грамматика, пунктуация и стиль</i>"
        
        await callback.message.edit_text(
            preview_text,
            reply_markup=keyboards.email_confirm_menu(email_id),
            parse_mode="HTML"
        )
        
    except Exception as e:
        await callback.message.edit_text(
            "❌ <b>Ошибка улучшения письма</b>\n\n"
            "Попробуйте позже или отредактируйте письмо вручную.",
            reply_markup=keyboards.email_confirm_menu(email_id),
            parse_mode="HTML"
        )
    
    await callback.answer()

@router.callback_query(F.data.startswith("email_expand_"))
async def expand_email_callback(callback: CallbackQuery):
    """Дополнить письмо с помощью AI"""
    email_id = callback.data.split("_")[-1]
    email_data = temp_emails.get_email(email_id)
    
    if not email_data or email_data["user_id"] != callback.from_user.id:
        await callback.answer("❌ Письмо не найдено", show_alert=True)
        return
    
    # Показываем статус дополнения
    await callback.message.edit_text(
        "🧠 <b>Дополняю письмо с помощью AI...</b>\n\n"
        "⏳ Добавляю детали, контекст и улучшаю содержание...",
        parse_mode="HTML"
    )
    
    try:
        from utils.openai_client import openai_client
        
        # Создаем промпт для дополнения письма
        prompt = f"""Дополни это деловое письмо, сделав его более развернутым и содержательным:

ТЕМА: {email_data["subject"]}

ТЕКУЩИЙ ТЕКСТ:
{email_data["body"]}

ТРЕБОВАНИЯ:
1. Сохрани вежливый деловой тон
2. Добавь больше деталей и контекста
3. Сделай письмо более убедительным
4. Длина: 3-5 абзацев
5. Сохрани структуру: приветствие + основная часть + заключение + подпись
6. НЕ изменяй тему письма

Верни только дополненный текст письма:"""

        messages = [
            {"role": "system", "content": "Ты - эксперт по деловой переписке. Дополняй письма, делая их более содержательными и убедительными, сохраняя деловой стиль."},
            {"role": "user", "content": prompt}
        ]
        
        expanded_body = await openai_client.chat_completion(messages)
        
        # Обновляем письмо
        temp_emails.update_email(email_id, body=expanded_body)
        email_data = temp_emails.get_email(email_id)
        
        # Показываем дополненный предварительный просмотр
        preview_text = temp_emails.format_email_preview(email_data)
        preview_text += "\n\n🧠 <i>Письмо дополнено AI: добавлены детали и контекст</i>"
        
        await callback.message.edit_text(
            preview_text,
            reply_markup=keyboards.email_confirm_menu(email_id),
            parse_mode="HTML"
        )
        
    except Exception as e:
        await callback.message.edit_text(
            "❌ <b>Ошибка дополнения письма</b>\n\n"
            "Попробуйте позже или отредактируйте письмо вручную.",
            reply_markup=keyboards.email_confirm_menu(email_id),
            parse_mode="HTML"
        )
    
    await callback.answer()

@router.callback_query(F.data.startswith("email_back_"))
async def back_to_email_callback(callback: CallbackQuery, state: FSMContext):
    """Вернуться к просмотру письма"""
    email_id = callback.data.split("_")[-1]
    email_data = temp_emails.get_email(email_id)
    
    if not email_data or email_data["user_id"] != callback.from_user.id:
        await callback.answer("❌ Письмо не найдено", show_alert=True)
        return
    
    # Очищаем состояние редактирования
    await state.clear()
    
    # Показываем письмо с кнопками
    preview_text = temp_emails.format_email_preview(email_data)
    await callback.message.edit_text(
        preview_text,
        reply_markup=keyboards.email_confirm_menu(email_id),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("email_cancel_"))
async def cancel_email_callback(callback: CallbackQuery):
    """Отменить отправку письма"""
    email_id = callback.data.split("_")[-1]
    
    await callback.message.edit_text(
        "❌ <b>Отправка письма отменена</b>\n\n"
        "💡 Вы можете снова создать письмо, написав команду отправки.",
        parse_mode="HTML"
    )
    
    # Удаляем временное письмо
    temp_emails.delete_email(email_id)
    await callback.answer()

# Обработчики состояний редактирования
@router.message(EmailStates.editing_subject)
async def handle_subject_edit(message: Message, state: FSMContext):
    """Обработка редактирования темы"""
    data = await state.get_data()
    email_id = data.get("email_id")
    
    if not email_id:
        await state.clear()
        await message.answer("❌ Ошибка редактирования")
        return
    
    new_subject = message.text.strip()
    if not new_subject:
        await message.answer("❌ Тема не может быть пустой. Попробуйте снова:")
        return
    
    # Обновляем тему
    temp_emails.update_email(email_id, subject=new_subject)
    email_data = temp_emails.get_email(email_id)
    
    # Показываем обновленный предварительный просмотр
    preview_text = temp_emails.format_email_preview(email_data)
    
    await message.answer(
        preview_text,
        reply_markup=keyboards.email_confirm_menu(email_id),
        parse_mode="HTML"
    )
    
    await state.clear()

@router.message(EmailStates.editing_body)
async def handle_body_edit(message: Message, state: FSMContext):
    """Обработка редактирования текста"""
    data = await state.get_data()
    email_id = data.get("email_id")
    
    if not email_id:
        await state.clear()
        await message.answer("❌ Ошибка редактирования")
        return
    
    new_body = message.text.strip()
    if not new_body:
        await message.answer("❌ Текст письма не может быть пустым. Попробуйте снова:")
        return
    
    # Обновляем текст
    temp_emails.update_email(email_id, body=new_body)
    email_data = temp_emails.get_email(email_id)
    
    # Показываем обновленный предварительный просмотр
    preview_text = temp_emails.format_email_preview(email_data)
    
    await message.answer(
        preview_text,
        reply_markup=keyboards.email_confirm_menu(email_id),
        parse_mode="HTML"
    )
    
    await state.clear()

@router.callback_query(F.data.startswith("search_details_"))
async def search_details_callback(callback: CallbackQuery):
    """Детальный просмотр результатов поиска"""
    user_id = callback.from_user.id
    
    try:
        # Загружаем кэшированные результаты поиска
        import json
        import os
        from utils.html_utils import escape_html, truncate_and_escape
        
        cache_file = os.path.join("data/search_cache", f"user_{user_id}_last_search.json")
        
        if not os.path.exists(cache_file):
            await callback.answer("❌ Результаты поиска не найдены", show_alert=True)
            return
        
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        search_results = cache_data.get('results', [])
        search_query = cache_data.get('query', 'неизвестно')
        
        if not search_results:
            await callback.answer("❌ Нет результатов для детального просмотра", show_alert=True)
            return
        
        # Формируем детальный просмотр
        detailed_text = f"📖 <b>Детальный просмотр поиска</b>\n\n"
        detailed_text += f"🔍 <b>Запрос:</b> {escape_html(search_query)}\n"
        detailed_text += f"📬 <b>Найдено писем:</b> {len(search_results)}\n\n"
        
        for i, email_data in enumerate(search_results, 1):
            sender = email_data.get('sender', 'Неизвестный отправитель')
            subject = email_data.get('subject', 'Без темы')
            date = email_data.get('date', '')
            content = email_data.get('content', email_data.get('body', ''))
            
            detailed_text += f"<b>📧 Письмо {i}:</b>\n"
            detailed_text += f"👤 <b>От:</b> {truncate_and_escape(sender, 40)}\n"
            detailed_text += f"📝 <b>Тема:</b> {truncate_and_escape(subject, 50)}\n"
            
            if date:
                detailed_text += f"🕐 <b>Дата:</b> {escape_html(str(date)[:19])}\n"
            
            # Показываем предпросмотр содержания
            if content:
                content_preview = truncate_and_escape(content.strip(), 150)
                detailed_text += f"📄 <b>Содержание:</b>\n{content_preview}\n"
            
            detailed_text += "\n" + "─" * 30 + "\n\n"
            
            # Ограничиваем размер сообщения
            if len(detailed_text) > 3500:
                detailed_text = detailed_text[:3500] + "\n\n<i>... показаны первые письма ...</i>"
                break
        
        # Создаем клавиатуру
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        builder.button(text="📨 К входящим", callback_data="mail_inbox")
        builder.button(text="🔍 Новый поиск", callback_data="mail_search")
        builder.button(text="◀️ Назад к результатам", callback_data="search_back")
        builder.button(text="❌ Выйти", callback_data="menu_back")
        
        builder.adjust(2, 2)
        
        await callback.message.edit_text(
            detailed_text,
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        await callback.answer(f"❌ Ошибка загрузки деталей: {str(e)[:50]}...", show_alert=True)
    
    await callback.answer()

@router.callback_query(F.data == "search_back")
async def search_back_callback(callback: CallbackQuery):
    """Возврат к кратким результатам поиска"""
    user_id = callback.from_user.id
    
    try:
        import json
        import os
        from utils.html_utils import escape_html, truncate_and_escape
        
        cache_file = os.path.join("data/search_cache", f"user_{user_id}_last_search.json")
        
        if not os.path.exists(cache_file):
            await callback.answer("❌ Результаты поиска не найдены", show_alert=True)
            return
        
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        search_results = cache_data.get('results', [])
        search_query = cache_data.get('query', 'неизвестно')
        
        # Воссоздаем краткие результаты (повторяем логику из основного поиска)
        results_text = f"🔍 <b>Результаты поиска</b>\n\n"
        results_text += f"📝 <b>Запрос:</b> {escape_html(search_query)}\n"
        results_text += f"📬 <b>Найдено:</b> {len(search_results)} писем\n\n"
        
        for i, email_data in enumerate(search_results, 1):
            sender = email_data.get('sender', 'Неизвестный отправитель')
            subject = email_data.get('subject', 'Без темы')
            date = email_data.get('date', '')
            
            sender_escaped = truncate_and_escape(sender, 25)
            subject_escaped = truncate_and_escape(subject, 35)
            
            results_text += f"<b>{i}.</b> 👤 {sender_escaped}\n"
            results_text += f"📝 {subject_escaped}\n"
            if date:
                results_text += f"🕐 {escape_html(str(date)[:16])}\n"
            results_text += "\n"
        
        # Создаем клавиатуру
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        builder.button(
            text="📖 Детальный просмотр", 
            callback_data=f"search_details_{len(search_results)}"
        )
        builder.button(text="📨 К входящим", callback_data="mail_inbox")
        builder.button(text="🔍 Новый поиск", callback_data="mail_search")
        builder.button(text="❌ Выйти", callback_data="menu_back")
        
        builder.adjust(1, 3)
        
        await callback.message.edit_text(
            results_text,
            parse_mode="HTML", 
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)[:50]}...", show_alert=True)
    
    await callback.answer()

# Обработчики кнопок знакомства
@router.callback_query(F.data == "introduce_myself")
async def introduce_myself_callback(callback: CallbackQuery):
    """Начать процесс знакомства"""
    await callback.message.edit_text(
        f"👋 <b>Отлично! Давай знакомиться!</b>\n\n"
        f"💬 <b>Напиши мне:</b>\n"
        f"\"Меня зовут [твое имя]\"\n\n"
        f"📧 <b>Можешь также добавить email:</b>\n"
        f"\"Меня зовут Иван, мой email ivan@example.com\"\n\n"
        f"💡 Я запомню эту информацию и буду к тебе обращаться по имени!",
        parse_mode="HTML"
    )
    await callback.answer("Жду твое сообщение с именем! 😊")

@router.callback_query(F.data == "save_name_now")  
async def save_name_now_callback(callback: CallbackQuery):
    """Сохранить имя прямо сейчас"""
    await callback.message.edit_text(
        f"📝 <b>Сохранение имени</b>\n\n"
        f"✏️ <b>Напиши свое имя в следующем сообщении</b>\n\n"
        f"Примеры:\n"
        f"• \"Александр\"\n"
        f"• \"Мария Петрова\"\n"
        f"• \"Иван email@example.com\"\n\n"
        f"💡 Я сохраню эту информацию и буду обращаться к тебе по имени!",
        parse_mode="HTML"
    )
    await callback.answer("Напиши свое имя!")

@router.callback_query(F.data == "just_chat")
async def just_chat_callback(callback: CallbackQuery):
    """Просто общаться без сохранения имени"""
    await callback.message.edit_text(
        f"🤖 <b>Хорошо, давай просто общаться!</b>\n\n"
        f"💬 <b>Я готов помочь тебе с:</b>\n"
        f"• Ответами на вопросы\n"
        f"• Отправкой писем\n"  
        f"• Работой с календарем\n"
        f"• Управлением контактами\n"
        f"• Напоминаниями\n\n"
        f"📝 <b>Если позже захочешь, чтобы я запомнил твое имя, просто скажи:</b>\n"
        f"\"Меня зовут [имя]\"",
        parse_mode="HTML"
    )
    await callback.answer("Готов к общению! 😊")

@router.message(~F.text & ~F.voice)
async def handle_other_messages(message: Message):
    """Обработчик других типов сообщений (не текст и не голос)"""
    await message.answer("🤔 Я пока умею работать только с текстовыми и голосовыми сообщениями.")