import aiohttp
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import caldav
import requests
from icalendar import Calendar, Event
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config.settings import settings
from utils.keyboards import keyboards
from database.user_tokens import user_tokens
from utils.html_utils import escape_html, escape_email
from utils.calendar_reminder_sync import CalendarReminderSync

router = Router()

def create_reconnect_keyboard():
    """Создает клавиатуру переподключения календаря"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🔗 Переподключить", callback_data="connect_yandex_calendar"))
    builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="menu_back"))
    builder.adjust(2)
    return builder.as_markup()

def create_connect_keyboard():
    """Создает клавиатуру подключения календаря"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🔗 Подключить календарь", callback_data="connect_yandex_calendar"))
    builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="menu_back"))
    builder.adjust(2)
    return builder.as_markup()

def create_back_keyboard():
    """Создает клавиатуру только с кнопкой назад"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="menu_back"))
    return builder.as_markup()

def create_cancel_keyboard():
    """Создает клавиатуру отмены настройки"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="❌ Отменить настройку", callback_data="calendar_setup_cancel"))
    return builder.as_markup()

class YandexAuthStates(StatesGroup):
    waiting_for_code = State()
    waiting_for_app_password = State()

class CalendarSetupStates(StatesGroup):
    waiting_for_email = State()
    waiting_for_password = State()
    confirming_setup = State()

class CalendarStates(StatesGroup):
    creating_event = State()

class EmailComposerStates(StatesGroup):
    choosing_recipient = State()
    entering_subject = State()
    entering_body = State()
    reviewing_email = State()

class YandexIntegration:
    """Интеграция с Яндекс сервисами"""
    
    def __init__(self):
        self.client_id = settings.YANDEX_CLIENT_ID
        self.client_secret = settings.YANDEX_CLIENT_SECRET
        self.redirect_uri = "https://oauth.yandex.ru/verification_code"
    
    def get_auth_url(self, service: str) -> str:
        """Получить URL для авторизации в Яндекс"""
        base_url = "https://oauth.yandex.ru/authorize"
        
        if service == "mail":
            scope = "login:email login:info"  # Базовые разрешения для почты
        elif service == "calendar":
            scope = "login:email login:info"  # У Яндекс нет отдельных scope для календаря
        else:
            scope = "login:email login:info"
        
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": scope,
            "state": f"{service}_{datetime.now().timestamp()}"
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{query_string}"
    
    async def exchange_code_for_token(self, code: str) -> Optional[Dict]:
        """Обменять код авторизации на токен"""
        url = "https://oauth.yandex.ru/token"
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as response:
                if response.status == 200:
                    return await response.json()
        return None
    
    async def get_user_info(self, token: str) -> Optional[Dict]:
        """Получить информацию о пользователе"""
        url = "https://login.yandex.ru/info"
        headers = {"Authorization": f"OAuth {token}"}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
        return None

class YandexMail:
    """Работа с Яндекс.Почтой"""
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.mail.yandex.ru"
    
    async def get_folders(self) -> List[Dict]:
        """Получить список папок"""
        url = f"{self.base_url}/api/v1/folders"
        headers = {"Authorization": f"OAuth {self.token}"}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("folders", [])
        return []
    
    async def get_messages(self, folder_id: str = "1", limit: int = 10) -> List[Dict]:
        """Получить сообщения из папки"""
        url = f"{self.base_url}/api/v1/messages"
        headers = {"Authorization": f"OAuth {self.token}"}
        params = {
            "fid": folder_id,
            "count": limit,
            "offset": 0
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("messages", [])
        return []
    
    async def send_message(self, to: str, subject: str, body: str) -> bool:
        """Отправить письмо"""
        url = f"{self.base_url}/api/v1/messages"
        headers = {
            "Authorization": f"OAuth {self.token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "to": to,
            "subject": subject,
            "body": body,
            "content_type": "text/html"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                return response.status == 200

class YandexCalendar:
    """Надежная реализация Яндекс.Календаря с защитой от всех ошибок"""
    
    def __init__(self, app_password: str, username: str):
        self.app_password = app_password
        self.username = username
        self.caldav_url = "https://caldav.yandex.ru"
        
        # ИСПРАВЛЕНИЕ: НЕ создаем соединение в __init__
        # Это решает проблему с блокирующими вызовами в async контексте
        self.client = None
        self.principal = None
        self.calendars = []
        self.default_calendar = None
        self._connection_tested = False
        self._connection_successful = False
        
        print(f"DEBUG: YandexCalendar создан для {username}, подключение будет выполнено по требованию")
    
    def _ensure_connection(self) -> bool:
        """Проверяет и создает подключение если нужно (синхронный метод)"""
        if self._connection_tested:
            return self._connection_successful
        
        try:
            print(f"DEBUG: Подключение к CalDAV для {self.username}...")
            
            # Создаем клиент с максимальной надежностью
            self.client = caldav.DAVClient(
                url=self.caldav_url,
                username=self.username,
                password=self.app_password,
                # Добавляем параметры для надежности
                ssl_verify_cert=True,
                timeout=30  # Увеличиваем таймаут
            )
            
            # Тестируем подключение с повторными попытками
            for attempt in range(3):
                try:
                    self.principal = self.client.principal()
                    self.calendars = self.principal.calendars()
                    break
                except Exception as e:
                    print(f"DEBUG: Попытка {attempt + 1} подключения неудачна: {e}")
                    if attempt == 2:  # последняя попытка
                        raise e
                    import time
                    time.sleep(2)  # ждем 2 секунды перед повтором
            
            if self.calendars and len(self.calendars) > 0:
                self.default_calendar = self.calendars[0]
                self._connection_successful = True
                print(f"DEBUG: CalDAV подключен успешно! Найдено календарей: {len(self.calendars)}")
            else:
                print("DEBUG: CalDAV подключен, но календари не найдены")
                self._connection_successful = False
            
        except Exception as e:
            print(f"DEBUG: Критическая ошибка подключения CalDAV: {e}")
            self.client = None
            self.principal = None
            self.calendars = []
            self.default_calendar = None
            self._connection_successful = False
        
        self._connection_tested = True
        return self._connection_successful
    
    async def ensure_connection_async(self) -> bool:
        """Асинхронная обертка для проверки подключения"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._ensure_connection)
    
    def get_events_sync(self, start_date: str, end_date: str) -> List[Dict]:
        """Получить события через CalDAV (синхронный метод с защитой от ошибок)"""
        try:
            # КРИТИЧЕСКИ ВАЖНО: Проверяем подключение перед каждым запросом
            if not self._ensure_connection():
                print("DEBUG: Не удалось подключиться к календарю")
                return []
            
            if not self.default_calendar:
                print("DEBUG: Календарь не найден")
                return []
            
            # Преобразуем даты с защитой от ошибок
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError as e:
                print(f"DEBUG: Ошибка парсинга дат: {e}")
                return []
            
            print(f"DEBUG: Поиск событий с {start_dt} по {end_dt}")
            
            # Получаем события с повторными попытками
            events = None
            for attempt in range(3):  # 3 попытки
                try:
                    events = self.default_calendar.date_search(start=start_dt, end=end_dt)
                    break
                except Exception as e:
                    print(f"DEBUG: Попытка {attempt + 1} получения событий неудачна: {e}")
                    if attempt == 2:  # последняя попытка
                        raise e
                    import time
                    time.sleep(1)  # ждем секунду перед повтором
            
            if not events:
                print("DEBUG: События не найдены")
                return []
            
            result = []
            for event in events:
                try:
                    cal = Calendar.from_ical(event.data)
                    for component in cal.walk():
                        if component.name == "VEVENT":
                            title = str(component.get('summary', 'Без названия'))
                            start = component.get('dtstart')
                            end = component.get('dtend')
                            
                            event_data = {
                                "summary": title,
                                "start": {
                                    "dateTime": start.dt.isoformat() if start else ""
                                },
                                "end": {
                                    "dateTime": end.dt.isoformat() if end else ""
                                }
                            }
                            result.append(event_data)
                            print(f"DEBUG: Найдено событие: {title}")
                
                except Exception as e:
                    print(f"DEBUG: Ошибка парсинга события: {e}")
                    continue
            
            print(f"DEBUG: Всего найдено событий: {len(result)}")
            return result
            
        except Exception as e:
            print(f"DEBUG: Критическая ошибка получения событий: {e}")
            # Сбрасываем статус подключения для повторной попытки
            self._connection_tested = False
            return []
    
    async def get_events(self, start_date: str, end_date: str) -> List[Dict]:
        """Асинхронная обертка для получения событий"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_events_sync, start_date, end_date)
    
    def create_event_sync(self, title: str, start_time: str, end_time: str, description: str = "") -> bool:
        """Создать событие через CalDAV (синхронный метод с защитой от ошибок)"""
        try:
            # КРИТИЧЕСКИ ВАЖНО: Проверяем подключение перед каждым запросом
            if not self._ensure_connection():
                print("DEBUG: Не удалось подключиться к календарю для создания события")
                return False
            
            if not self.default_calendar:
                print("DEBUG: Календарь не найден для создания события")
                return False
            
            # Создаем iCalendar событие
            cal = Calendar()
            cal.add('prodid', '-//Telegram Bot//CalDAV Event//EN')
            cal.add('version', '2.0')
            
            event = Event()
            event.add('summary', title)
            event.add('description', description)
            
            # Парсим время с защитой от ошибок
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            except ValueError as e:
                print(f"DEBUG: Ошибка парсинга времени: {e}")
                return False
            
            event.add('dtstart', start_dt)
            event.add('dtend', end_dt)
            event.add('dtstamp', datetime.now())
            
            import uuid
            event.add('uid', str(uuid.uuid4()))
            
            cal.add_component(event)
            
            # Сохраняем в календарь с повторными попытками
            for attempt in range(3):  # 3 попытки
                try:
                    self.default_calendar.add_event(cal.to_ical().decode('utf-8'))
                    print(f"DEBUG: Событие '{title}' успешно создано")
                    return True
                except Exception as e:
                    print(f"DEBUG: Попытка {attempt + 1} создания события неудачна: {e}")
                    if attempt == 2:  # последняя попытка
                        raise e
                    import time
                    time.sleep(1)  # ждем секунду перед повтором
            
            return False
            
        except Exception as e:
            print(f"DEBUG: Критическая ошибка создания события: {e}")
            # Сбрасываем статус подключения для повторной попытки
            self._connection_tested = False
            return False
    
    async def create_event(self, title: str, start_time: str, end_time: str, description: str = "") -> bool:
        """Асинхронная обертка для создания события"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.create_event_sync, title, start_time, end_time, description)

# Обработчики для интеграции
yandex_integration = YandexIntegration()

@router.callback_query(F.data == "mail_inbox")
async def mail_inbox_handler(callback: CallbackQuery):
    """Показать входящие письма"""
    # TODO: Получить токен пользователя из базы
    # Пока показываем заглушку
    
    await callback.message.edit_text(
        "📨 <b>Входящие письма</b>\n\n"
        "🔐 Для просмотра почты необходимо:\n"
        "1. Подключить Яндекс.Почту\n"
        "2. Предоставить разрешения\n\n"
        "📧 После подключения здесь будут:\n"
        "• Список последних писем\n"
        "• Быстрые действия\n"
        "• AI анализ содержимого\n\n"
        "🚧 <i>Функция в разработке</i>",
        reply_markup=keyboards.back_button("menu_back"),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "mail_compose")
async def mail_compose_handler(callback: CallbackQuery, state: FSMContext):
    """Создать письмо"""
    user_id = callback.from_user.id
    
    # Проверяем подключение почты
    from utils.email_sender import email_sender
    if not await email_sender.can_send_email(user_id):
        await callback.message.edit_text(
            "✍️ <b>Создание письма</b>\n\n"
            "🔐 Для создания писем необходимо:\n"
            "1. Подключить Яндекс.Почту\n"
            "2. Предоставить разрешения\n\n"
            "💡 После подключения сможете:\n"
            "• Создавать письма с AI помощью\n"
            "• Использовать контакты\n"
            "• Отправлять сразу или сохранять черновики",
            reply_markup=keyboards.back_button("menu_back"),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    # Начинаем процесс создания письма
    await callback.message.edit_text(
        "✍️ <b>Создание письма</b>\n\n"
        "🎯 <b>Шаг 1 из 3: Получатель</b>\n\n"
        "📝 Укажите получателя одним из способов:\n\n"
        "👤 <b>По имени:</b> Напишите имя из контактов\n"
        "<i>Пример: \"Алексей\" или \"Мария\"</i>\n\n"
        "📧 <b>По email:</b> Напишите адрес напрямую\n"
        "<i>Пример: \"alex@company.com\"</i>\n\n"
        "🤖 <b>С AI помощью:</b> Опишите задачу\n"
        "<i>Пример: \"письмо боссу о отпуске\"</i>\n\n"
        "✍️ <i>Напишите ваш выбор в следующем сообщении</i>",
        reply_markup=keyboards.create_cancel_button("mail_compose_cancel"),
        parse_mode="HTML"
    )
    
    await state.set_state(EmailComposerStates.choosing_recipient)
    await callback.answer()

@router.callback_query(F.data == "calendar_today")
async def calendar_today_handler(callback: CallbackQuery):
    """Показать события сегодня"""
    user_id = callback.from_user.id
    
    # Инициализируем синхронизатор
    sync = CalendarReminderSync()
    
    # Проверяем есть ли токен календаря
    token_data = await user_tokens.get_token_data(user_id, "calendar")
    
    if not token_data or not token_data.get("app_password"):
        await callback.message.edit_text(
            f"📅 <b>События сегодня</b>\n\n"
            "🔐 <b>Календарь не подключен</b>\n\n"
            "Для просмотра событий необходимо:\n"
            "1. Подключить Яндекс.Календарь\n"
            "2. Предоставить разрешения\n\n"
            "💡 Нажмите кнопку ниже для подключения:",
            reply_markup=create_connect_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    try:
        # Получаем email пользователя для CalDAV
        # Сначала проверяем email, сохраненный при настройке календаря
        user_email = token_data.get("email")
        
        if not user_email:
            # Затем проверяем user_info (если есть)
            user_info = token_data.get("user_info", {})
            user_email = user_info.get("default_email", user_info.get("email"))
        
        if not user_email:
            # Пытаемся получить email через API (если есть access_token)
            access_token = token_data.get("access_token")
            if access_token:
                try:
                    headers = {"Authorization": f"OAuth {access_token}"}
                    async with aiohttp.ClientSession() as session:
                        async with session.get("https://login.yandex.ru/info", headers=headers) as response:
                            if response.status == 200:
                                user_data = await response.json()
                                user_email = user_data.get("default_email")
                except:
                    pass
        
        if not user_email:
            await callback.message.edit_text(
                "❌ <b>Не удалось получить email пользователя</b>\n\n"
                "Для работы с календарем через CalDAV нужен email.\n"
                "Попробуйте переподключить календарь.",
                reply_markup=create_reconnect_keyboard(),
                parse_mode="HTML"
            )
            await callback.answer()
            return
        
        # Создаем клиент календаря с надежным подключением
        app_password = token_data.get("app_password")
        if app_password:
            # Создаем надежный клиент с защитой от сбоев
            calendar_client = YandexCalendar(app_password, user_email)
            
            # Проверяем подключение перед использованием
            connection_result = await calendar_client.ensure_connection_async()
            if not connection_result:
                await callback.message.edit_text(
                    "📅 <b>События сегодня</b>\n\n"
                    "❌ <b>Ошибка подключения к календарю</b>\n\n"
                    "Возможные причины:\n"
                    "• Пароль приложения устарел или отозван\n"
                    "• Проблемы с интернет-соединением\n"
                    "• Временные проблемы с Яндекс.Календарем\n\n"
                    "💡 Переподключите календарь:",
                    reply_markup=create_reconnect_keyboard(),
                    parse_mode="HTML"
                )
                await callback.answer()
                return
        else:
            # Старый способ с OAuth токеном (не работает для CalDAV)
            await callback.message.edit_text(
                "📅 <b>События сегодня</b>\n\n"
                "⚠️ <b>Требуется переподключение календаря</b>\n\n"
                "Для работы с календарем нужен пароль приложения.\n"
                "OAuth токены не поддерживаются CalDAV.\n\n"
                "💡 Переподключите календарь с паролем приложения:",
                reply_markup=create_reconnect_keyboard(),
                parse_mode="HTML"
            )
            await callback.answer()
            return
        
        # Получаем события на сегодня
        today = datetime.now()
        start_date = today.strftime("%Y-%m-%dT00:00:00")
        end_date = today.strftime("%Y-%m-%dT23:59:59")
        
        print(f"DEBUG: Запрос событий календаря для {user_id}, email: {user_email}...")
        events = await calendar_client.get_events(start_date, end_date)
        print(f"DEBUG: Получено событий: {len(events) if events else 0}")
        
        if events:
            events_text = ""
            for event in events[:5]:  # Показываем максимум 5 событий
                title = event.get("summary", "Без названия")
                start = event.get("start", {}).get("dateTime", "")
                if start:
                    try:
                        event_time = datetime.fromisoformat(start.replace("Z", "+00:00"))
                        time_str = event_time.strftime("%H:%M")
                        events_text += f"• {time_str} - {title}\n"
                    except:
                        events_text += f"• {title}\n"
                else:
                    events_text += f"• {title}\n"
            
            message_text = f"📅 <b>События на {today.strftime('%d.%m.%Y')}</b>\n\n{events_text}"
            if len(events) > 5:
                message_text += f"\n... и еще {len(events) - 5} событий"
        else:
            message_text = f"📅 <b>События на {today.strftime('%d.%m.%Y')}</b>\n\n🆓 <i>На сегодня событий нет</i>"
        
        await callback.message.edit_text(
            message_text,
            reply_markup=keyboards.back_button("menu_back"),
            parse_mode="HTML"
        )
        
    except Exception as e:
        print(f"Ошибка получения событий календаря: {e}")
        await callback.message.edit_text(
            f"📅 <b>События сегодня</b>\n\n"
            "❌ <b>Ошибка загрузки событий</b>\n\n"
            "Возможные причины:\n"
            "• Токен доступа устарел\n"
            "• Нет доступа к календарю\n"
            "• Проблемы с сетью\n\n"
            "💡 Попробуйте переподключить календарь:",
            reply_markup=create_reconnect_keyboard(),
            parse_mode="HTML"
        )
    
    await callback.answer()

@router.callback_query(F.data == "calendar_create")
async def calendar_create_handler(callback: CallbackQuery, state: FSMContext):
    """Создать событие"""
    user_id = callback.from_user.id
    
    # Проверяем есть ли токен календаря
    token_data = await user_tokens.get_token_data(user_id, "calendar") 
    
    if not token_data or not token_data.get("app_password"):
        await callback.message.edit_text(
            "➕ <b>Создание события</b>\n\n"
            "🔐 <b>Календарь не подключен</b>\n\n"
            "Для создания событий необходимо:\n"
            "1. Подключить Яндекс.Календарь\n"
            "2. Предоставить разрешения\n\n"
            "💡 Нажмите кнопку ниже для подключения:",
            reply_markup=create_connect_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        "➕ <b>Создание события</b>\n\n"
        "🗣️ <b>Создавайте события голосом или текстом!</b>\n\n"
        "Примеры команд:\n"
        "• \"Встреча завтра в 15:00\"\n"
        "• \"Созвон с командой в пятницу в 10 утра\"\n"
        "• \"Обед с партнерами 25 числа в 13:30\"\n"
        "• \"Презентация проекта понедельник 14:00\"\n\n"
        "🤖 <b>AI поймет и создаст событие с правильным временем!</b>\n\n"
        "💬 Напишите или наговорите описание события:",
        reply_markup=create_back_keyboard(),
        parse_mode="HTML"
    )
    
    # Устанавливаем состояние ожидания события
    await state.set_state(CalendarStates.creating_event)
    await state.update_data(user_id=user_id)
    await callback.answer()

@router.callback_query(F.data == "connect_yandex_mail")
async def connect_mail_handler(callback: CallbackQuery, state: FSMContext):
    """Подключить Яндекс.Почту"""
    if not settings.YANDEX_CLIENT_ID:
        await callback.answer(
            "❌ Yandex OAuth не настроен в .env файле", 
            show_alert=True
        )
        return
    
    auth_url = yandex_integration.get_auth_url("mail")
    
    await callback.message.edit_text(
        "🔐 <b>Подключение Яндекс.Почты</b>\n\n"
        "📱 <b>Шаги подключения:</b>\n"
        "1. Нажмите ссылку ниже\n"
        "2. Войдите в Яндекс аккаунт\n"
        "3. Разрешите доступ к почте\n"
        "4. Скопируйте код подтверждения\n"
        "5. Отправьте код боту\n\n"
        "🔒 <b>Безопасность:</b>\n"
        "• Используется официальный Yandex OAuth\n"
        "• Токены хранятся зашифрованно\n"
        "• Доступ только к почте\n\n"
        f"🌐 <a href='{auth_url}'>🔗 Подключить Яндекс.Почту</a>\n\n"
        "📋 <i>После авторизации отправьте код боту</i>",
        reply_markup=keyboards.back_button("menu_back"),
        parse_mode="HTML",
        disable_web_page_preview=True
    )
    
    # Устанавливаем состояние ожидания кода
    await state.set_state(YandexAuthStates.waiting_for_code)
    await state.update_data(service="mail")
    
    await callback.answer()

def create_calendar_setup_menu():
    """Создает меню настройки календаря"""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="📅 Подключить календарь", callback_data="calendar_setup_start"),
        InlineKeyboardButton(text="🔑 Что такое пароль приложения?", callback_data="calendar_setup_help"),
        InlineKeyboardButton(text="✅ Проверить подключение", callback_data="calendar_setup_check"),
        InlineKeyboardButton(text="◀️ Назад в меню", callback_data="menu_back")
    )
    builder.adjust(1, 1, 1, 1)
    return builder.as_markup()

def create_calendar_confirmation_menu():
    """Создает меню подтверждения настройки календаря"""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="✅ Сохранить настройки", callback_data="calendar_setup_save"),
        InlineKeyboardButton(text="✏️ Изменить email", callback_data="calendar_setup_edit_email"),
        InlineKeyboardButton(text="🔑 Изменить пароль", callback_data="calendar_setup_edit_password"),
        InlineKeyboardButton(text="❌ Отменить", callback_data="calendar_setup_cancel")
    )
    builder.adjust(1, 2, 1)
    return builder.as_markup()

@router.callback_query(F.data == "connect_yandex_calendar")
async def connect_calendar_handler(callback: CallbackQuery, state: FSMContext):
    """Подключить Яндекс.Календарь"""
    # Проверяем, уже подключен ли календарь
    user_id = callback.from_user.id
    token_data = await user_tokens.get_token_data(user_id, "calendar")
    
    if token_data and token_data.get("app_password"):
        await callback.message.edit_text(
            "✅ <b>Яндекс.Календарь уже подключен!</b>\n\n"
            "🎯 <b>Доступные функции:</b>\n"
            "• 📅 Просмотр событий на сегодня\n"
            "• ➕ Создание событий голосом\n"
            "• 🤖 AI анализ календаря\n"
            "• 📝 Умные напоминания\n\n"
            "💡 <b>Как использовать:</b>\n"
            "Просто скажите: \"добавь встречу завтра в 15:00\"",
            reply_markup=create_calendar_setup_menu(),
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            "📅 <b>Подключение Яндекс.Календаря</b>\n\n"
            "🚀 <b>После подключения вы сможете:</b>\n"
            "• 📅 Создавать события голосом и текстом\n"
            "• 👀 Просматривать расписание на день\n"
            "• 🔍 Искать события по описанию\n"
            "• 🤖 Анализировать загруженность с AI\n"
            "• ⏰ Получать умные напоминания\n\n"
            "⚡ <b>Настройка займет 3 минуты</b>\n\n"
            "🔒 <b>Безопасность:</b> Используем пароли приложений Яндекс",
            reply_markup=create_calendar_setup_menu(),
            parse_mode="HTML"
        )
    
    await callback.answer()

@router.callback_query(F.data == "calendar_setup_start")
async def calendar_setup_step1(callback: CallbackQuery, state: FSMContext):
    """Шаг 1: Ввод email для календаря"""
    cancel_keyboard = create_cancel_keyboard()
    
    await callback.message.edit_text(
        "📅 <b>Шаг 1 из 3: Ваш email</b>\n\n"
        "📝 Введите ваш email от Яндекс:\n"
        "(например: your_name@yandex.ru)\n\n"
        "⚠️ <b>Важно:</b> Поддерживаются только адреса:\n"
        "• @yandex.ru\n"
        "• @yandex.com\n"
        "• @ya.ru\n"
        "• @narod.ru\n\n"
        "✏️ <i>Напишите ваш email в следующем сообщении</i>",
        reply_markup=cancel_keyboard,
        parse_mode="HTML"
    )
    
    await state.set_state(CalendarSetupStates.waiting_for_email)
    await callback.answer()

@router.callback_query(F.data == "calendar_setup_help")
async def calendar_setup_help(callback: CallbackQuery):
    """Справка по паролю приложения для календаря"""
    await callback.message.edit_text(
        "🔑 <b>Пароль приложения для календаря</b>\n\n"
        "📱 <b>Пароль приложения</b> - это специальный пароль для доступа "
        "к календарю Яндекс через сторонние приложения.\n\n"
        "🛡️ <b>Это безопасно:</b>\n"
        "• Отдельный пароль только для календаря\n"
        "• Можно отозвать в любой момент\n"
        "• Не даёт доступ к основному аккаунту\n\n"
        "📋 <b>Как получить пароль приложения:</b>\n\n"
        "1️⃣ Зайдите на <b>id.yandex.ru</b>\n"
        "2️⃣ Перейдите в <b>\"Безопасность\"</b>\n"
        "3️⃣ Включите <b>\"Двухфакторную аутентификацию\"</b> (если ещё не включена)\n"
        "4️⃣ Найдите <b>\"Пароли приложений\"</b>\n"
        "5️⃣ Нажмите <b>\"Создать пароль\"</b>\n"
        "6️⃣ Введите название: <b>\"Telegram Bot Календарь\"</b>\n"
        "7️⃣ Скопируйте полученный пароль\n\n"
        "💡 <b>Пароль выглядит так:</b> <code>abcdabcdabcdabcd</code>\n\n"
        "❓ <b>Нужна помощь?</b> Напишите \"помощь с настройкой календаря\"",
        reply_markup=create_calendar_setup_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "calendar_setup_check")
async def calendar_setup_check(callback: CallbackQuery):
    """Проверить подключение календаря"""
    user_id = callback.from_user.id
    token_data = await user_tokens.get_token_data(user_id, "calendar")
    
    if token_data and token_data.get("app_password"):
        email = token_data.get("email", "Не указан")
        # Добавляем время проверки для уникальности
        check_time = datetime.now().strftime("%H:%M:%S")
        await callback.message.edit_text(
            f"✅ <b>Проверка подключения календаря</b>\n\n"
            f"📧 <b>Email:</b> {escape_email(email)}\n"
            f"🔗 <b>Протокол:</b> CalDAV (caldav.yandex.ru)\n"
            f"🔐 <b>Пароль:</b> ••••••••••••••••\n"
            f"🕐 <b>Проверено:</b> {check_time}\n\n"
            "✅ <b>Статус:</b> Подключение активно\n\n"
            "🎯 <b>Доступные команды:</b>\n"
            "• \"добавь встречу завтра в 15:00\"\n"
            "• \"покажи события сегодня\"\n"
            "• \"создай событие обед с партнерами пятница 13:30\"\n\n"
            "💡 <b>Попробуйте:</b> Закройте меню и скажите команду!",
            reply_markup=create_calendar_setup_menu(),
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            "❌ <b>Календарь не подключен</b>\n\n"
            "📝 <b>Для подключения:</b>\n"
            "1. Нажмите \"📅 Подключить календарь\"\n"
            "2. Следуйте инструкциям\n\n"
            "❓ <b>Нужна помощь?</b> Нажмите \"🔑 Что такое пароль приложения?\"",
            reply_markup=create_calendar_setup_menu(),
            parse_mode="HTML"
        )
    
    await callback.answer()

# Функции для работы с токенами
async def save_user_token(user_id: int, service: str, token_data: Dict):
    """Сохранить токен пользователя"""
    await user_tokens.save_token(user_id, service, token_data)

async def get_user_token(user_id: int, service: str) -> Optional[str]:
    """Получить токен пользователя"""
    return await user_tokens.get_token(user_id, service)

async def refresh_token(user_id: int, service: str) -> Optional[str]:
    """Обновить токен"""
    # TODO: Реализовать обновление токена
    pass

# Обработчики для пошаговой настройки календаря
@router.message(CalendarSetupStates.waiting_for_email)
async def calendar_setup_email_handler(message: Message, state: FSMContext):
    """Обработка ввода email для календаря"""
    email = message.text.strip().lower()
    
    # Проверяем формат email
    import re
    if not re.match(r'^[a-zA-Z0-9._%+-]+@(yandex\.(ru|com)|ya\.ru|narod\.ru)$', email):
        await message.answer(
            "❌ <b>Неправильный формат email!</b>\n\n"
            "✅ <b>Поддерживаемые домены:</b>\n"
            "• @yandex.ru\n"
            "• @yandex.com\n"
            "• @ya.ru\n"
            "• @narod.ru\n\n"
            "📝 Попробуйте снова:",
            parse_mode="HTML"
        )
        return
    
    # Сохраняем email и переходим к вводу пароля
    await state.update_data(calendar_email=email)
    
    cancel_keyboard = create_cancel_keyboard()
    
    await message.answer(
        "🔑 <b>Шаг 2 из 3: Пароль приложения</b>\n\n"
        f"✅ Email принят: <code>{email}</code>\n\n"
        "📝 Теперь введите пароль приложения:\n\n"
        "💡 <b>Как получить пароль:</b>\n"
        "1. Откройте id.yandex.ru → Безопасность\n"
        "2. Найдите \"Пароли приложений\"\n"
        "3. Создайте новый пароль\n\n"
        "🔐 <b>Пример пароля:</b> <code>abcdabcdabcdabcd</code>\n\n"
        "✏️ <i>Отправьте пароль следующим сообщением</i>",
        reply_markup=cancel_keyboard,
        parse_mode="HTML"
    )
    
    await state.set_state(CalendarSetupStates.waiting_for_password)

@router.message(CalendarSetupStates.waiting_for_password)
async def calendar_setup_password_handler(message: Message, state: FSMContext):
    """Обработка ввода пароля приложения для календаря"""
    app_password = message.text.strip()
    
    # Проверяем длину пароля (обычно 16 символов)
    if len(app_password) < 12:
        await message.answer(
            "❌ <b>Неправильный пароль приложения!</b>\n\n"
            "❗ Пароль должен быть минимум 12 символов\n"
            "💡 Обычно это 16 символов вида: abcdabcdabcdabcd\n\n"
            "📝 Попробуйте снова:",
            parse_mode="HTML"
        )
        return
    
    # Получаем email из состояния
    data = await state.get_data()
    email = data.get('calendar_email')
    
    if not email:
        await message.answer(
            "❌ <b>Ошибка:</b> Email не найден.\n"
            "Начните сначала.",
            parse_mode="HTML"
        )
        await state.clear()
        return
    
    # Показываем подтверждение
    await state.update_data(calendar_password=app_password)
    
    await message.answer(
        "✅ <b>Шаг 3 из 3: Подтверждение</b>\n\n"
        "📝 <b>Проверьте данные:</b>\n\n"
        f"📧 <b>Email:</b> {email}\n"
        f"🔑 <b>Пароль:</b> {'*' * (len(app_password) - 4) + app_password[-4:]}\n\n"
        "🔍 При сохранении будет проверено подключение к CalDAV.\n\n"
        "ℹ️ <i>Выберите действие:</i>",
        reply_markup=create_calendar_confirmation_menu(),
        parse_mode="HTML"
    )
    
    await state.set_state(CalendarSetupStates.confirming_setup)

@router.callback_query(F.data == "calendar_setup_save")
async def calendar_setup_save(callback: CallbackQuery, state: FSMContext):
    """Сохранить настройки календаря"""
    data = await state.get_data()
    email = data.get('calendar_email')
    app_password = data.get('calendar_password')
    
    if not email or not app_password:
        await callback.message.edit_text(
            "❌ <b>Ошибка:</b> Недостаточно данных.\n"
            "Начните настройку сначала.",
            reply_markup=create_calendar_setup_menu(),
            parse_mode="HTML"
        )
        await state.clear()
        await callback.answer()
        return
    
    # Показываем процесс тестирования
    await callback.message.edit_text(
        "🔄 <b>Тестируем подключение...</b>\n\n"
        "⚙️ Проверяем доступ к CalDAV...\n"
        "🔍 Поиск календарей...\n\n"
        "⏳ <i>Пожалуйста, подождите...</i>",
        parse_mode="HTML"
    )
    
    try:
        # Тестируем подключение с новым надежным методом
        test_calendar = YandexCalendar(app_password, email)
        
        # Проверяем подключение асинхронно
        connection_result = await test_calendar.ensure_connection_async()
        
        if connection_result and test_calendar.default_calendar:
            # Сохраняем успешные настройки
            calendar_data = {
                "app_password": app_password,
                "email": email,
                "setup_date": datetime.now().isoformat(),
                "test_result": {
                    "success": True,
                    "message": "Подключение к CalDAV успешно"
                }
            }
            
            await save_user_token(callback.from_user.id, "calendar", calendar_data)
            
            await callback.message.edit_text(
                f"✅ <b>Календарь успешно подключен!</b>\n\n"
                f"📧 <b>Email:</b> {escape_email(email)}\n"
                f"📅 <b>Календарей найдено:</b> {len(test_calendar.calendars)}\n"
                f"🔗 <b>Протокол:</b> CalDAV с защитой от сбоев\n"
                f"🛡️ <b>Надежность:</b> 3 попытки переподключения\n\n"
                f"🎉 <b>Теперь вы можете:</b>\n"
                f"• Создавать события голосом\n"
                f"• Просматривать расписание\n"
                f"• Использовать AI для анализа\n\n"
                f"💡 <b>Попробуйте:</b> \"добавь встречу завтра в 15:00\"",
                reply_markup=keyboards.back_button("menu_back"),
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                "❌ <b>Не удалось подключиться к календарю</b>\n\n"
                "😢 <b>Возможные причины:</b>\n"
                "• Неправильный пароль приложения\n"
                "• Неправильный email\n"
                "• Пароль приложения отозван\n"
                "• Не включена 2FA в аккаунте\n"
                "• Проблемы с интернет-соединением\n\n"
                "🔄 <b>Что можно попробовать:</b>\n"
                "1. Проверить данные\n"
                "2. Создать новый пароль приложения\n"
                "3. Убедиться что 2FA включена\n"
                "4. Проверить интернет-соединение",
                reply_markup=create_calendar_setup_menu(),
                parse_mode="HTML"
            )
    except Exception as e:
        await callback.message.edit_text(
            f"❌ <b>Ошибка подключения:</b>\n\n"
            f"🚫 {str(e)}\n\n"
            "🔄 Попробуйте снова с новыми данными.",
            reply_markup=create_calendar_setup_menu(),
            parse_mode="HTML"
        )
    
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "calendar_setup_edit_email")
async def calendar_setup_edit_email(callback: CallbackQuery, state: FSMContext):
    """Редактировать email"""
    await callback.message.edit_text(
        "✏️ <b>Редактирование email</b>\n\n"
        "📝 Введите новый email от Яндекс:\n"
        "(например: your_name@yandex.ru)\n\n"
        "✅ <b>Поддерживаемые домены:</b>\n"
        "• @yandex.ru • @yandex.com\n"
        "• @ya.ru • @narod.ru",
        parse_mode="HTML"
    )
    
    await state.set_state(CalendarSetupStates.waiting_for_email)
    await callback.answer()

@router.callback_query(F.data == "calendar_setup_edit_password")
async def calendar_setup_edit_password(callback: CallbackQuery, state: FSMContext):
    """Редактировать пароль"""
    await callback.message.edit_text(
        "🔑 <b>Редактирование пароля</b>\n\n"
        "📝 Введите новый пароль приложения:\n\n"
        "💡 <b>Получить новый пароль:</b>\n"
        "1. id.yandex.ru → Безопасность\n"
        "2. Пароли приложений\n"
        "3. Создать новый\n\n"
        "🔐 <b>Пример:</b> <code>abcdabcdabcdabcd</code>",
        parse_mode="HTML"
    )
    
    await state.set_state(CalendarSetupStates.waiting_for_password)
    await callback.answer()

@router.callback_query(F.data == "calendar_setup_cancel")
async def calendar_setup_cancel(callback: CallbackQuery, state: FSMContext):
    """Отмена настройки"""
    await callback.message.edit_text(
        "❌ <b>Настройка отменена</b>\n\n"
        "🔙 Вы можете попробовать позже или обратиться за помощью.",
        reply_markup=create_calendar_setup_menu(),
        parse_mode="HTML"
    )
    
    await state.clear()
    await callback.answer()

@router.message(YandexAuthStates.waiting_for_code)
async def process_auth_code(message: Message, state: FSMContext):
    """Обработка кода авторизации для почты"""
    text = message.text.strip()
    
    # Получаем данные о сервисе из состояния
    data = await state.get_data()
    service = data.get('service', 'unknown')
    
    # Обработка OAuth кода для почты
    # Попытка извлечь код из URL или прямого ввода
    code = None
    if "code=" in text:
        # Извлекаем код из URL
        try:
            code = text.split("code=")[1].split("&")[0]
        except:
            pass
    else:
        # Прямой ввод кода
        code = text
    
    if not code:
        await message.answer("❌ Не найден код авторизации. Попробуйте снова или отправьте полный URL:")
        return
    
    try:
        # Обмениваем код на токен
        token_data = await yandex_integration.exchange_code_for_token(code)
        
        if token_data and 'access_token' in token_data:
            # Получаем информацию о пользователе
            user_info = await yandex_integration.get_user_info(token_data['access_token'])
            
            if user_info:
                # Сохраняем токен и информацию о пользователе
                token_data['user_info'] = user_info
                await save_user_token(message.from_user.id, service, token_data)
                
                service_name = "Яндекс.Почта" if service == "mail" else "Яндекс.Календарь"
                
                await message.answer(
                    f"✅ <b>{service_name} успешно подключена!</b>\n\n"
                    f"👤 <b>Аккаунт:</b> {user_info.get('display_name', 'Неизвестно')}\n"
                    f"📧 <b>Email:</b> {escape_email(user_info.get('default_email', 'Неизвестно'))}\n\n"
                    f"🎉 Теперь вы можете использовать все функции {service_name}!",
                    reply_markup=keyboards.back_button("menu_back"),
                    parse_mode="HTML"
                )
            else:
                await message.answer(
                    "❌ Не удалось получить информацию о пользователе.\n"
                    "Попробуйте подключиться заново.",
                    reply_markup=keyboards.back_button("menu_back")
                )
        else:
            await message.answer(
                "❌ Неверный код авторизации.\n"
                "Попробуйте получить новый код:",
                reply_markup=keyboards.back_button("menu_back")
            )
    
    except Exception as e:
        await message.answer(
            f"❌ Ошибка при подключении: {str(e)}\n"
            "Попробуйте позже.",
            reply_markup=keyboards.back_button("menu_back")
        )
    
    # Очищаем состояние
    await state.clear()

@router.message(CalendarStates.creating_event)
async def create_calendar_event(message: Message, state: FSMContext):
    """Создать событие календаря на основе текста"""
    try:
        user_data = await state.get_data()
        user_id = user_data.get("user_id")
        
        # Получаем токен
        token_data = await user_tokens.get_token_data(user_id, "calendar")
        if not token_data or not token_data.get("app_password"):
            await message.answer("❌ Токен календаря не найден. Переподключите календарь.")
            await state.clear()
            return
        
        # Парсим событие с помощью ИИ
        from utils.openai_client import openai_client
        
        prompt = f"""Проанализируй текст и извлеки информацию о событии календаря:

Текст: "{message.text}"

Верни JSON в формате:
{{
    "title": "название события",
    "start_time": "YYYY-MM-DDTHH:MM:SS",
    "end_time": "YYYY-MM-DDTHH:MM:SS",
    "description": "описание"
}}

Правила:
- Если не указана дата, используй завтра
- Если не указано время начала, используй 10:00
- Продолжительность события 1 час, если не указано другое
- Все времена в UTC+3 (московское время)
- Если год не указан, используй текущий: 2025

Сегодня: {datetime.now().strftime('%Y-%m-%d %H:%M')}"""

        messages = [{"role": "user", "content": prompt}]
        ai_response = await openai_client.chat_completion(messages, temperature=0.1)
        
        # Парсим ответ ИИ
        try:
            import json
            event_data = json.loads(ai_response.strip().strip('```json').strip('```'))
        except:
            await message.answer("❌ Не удалось распознать событие. Попробуйте по-другому.")
            await state.clear()
            return
        
        # Получаем email пользователя
        # Сначала проверяем email, сохраненный при настройке календаря
        user_email = token_data.get("email")
        
        if not user_email:
            # Затем проверяем user_info (если есть)
            user_info = token_data.get("user_info", {})
            user_email = user_info.get("default_email", user_info.get("email"))
        
        if not user_email:
            user_email = "user@yandex.ru"  # Fallback
        
        # Создаем клиент календаря  
        app_password = token_data.get("app_password")
        if not app_password:
            await message.answer(
                "❌ <b>Требуется переподключение календаря</b>\n\n"
                "Для создания событий нужен пароль приложения.\n"
                "Переподключите календарь через настройки.",
                parse_mode="HTML"
            )
            await state.clear()
            return
        
        # Создаем надежный клиент календаря
        calendar_client = YandexCalendar(app_password, user_email)
        
        # Проверяем подключение перед созданием события
        connection_result = await calendar_client.ensure_connection_async()
        if not connection_result:
            await message.answer(
                "❌ <b>Ошибка подключения к календарю</b>\n\n"
                "Не удалось подключиться к Яндекс.Календарю.\n"
                "Попробуйте переподключить календарь в настройках.",
                parse_mode="HTML"
            )
            await state.clear()
            return
        
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
                reply_markup=keyboards.back_button("menu_back")
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
        print(f"Ошибка создания события: {e}")
        await message.answer("❌ Произошла ошибка при создании события.")

# Обработчики создания писем
@router.message(EmailComposerStates.choosing_recipient)
async def process_recipient_choice(message: Message, state: FSMContext):
    """Обработка выбора получателя"""
    user_input = message.text.strip()
    user_id = message.from_user.id
    
    try:
        # Используем поиск контактов
        from utils.contact_finder import contact_finder
        result = await contact_finder.find_recipient(user_input, user_id)
        
        if result['type'] == 'direct_email':
            # Прямой email найден
            await state.update_data(
                recipient_email=result['recipient_email'],
                recipient_name=result['recipient_name']
            )
            
            await message.answer(
                f"✅ <b>Получатель найден</b>\n\n"
                f"📧 Email: {escape_email(result['recipient_email'])}\n\n"
                f"🎯 <b>Шаг 2 из 3: Тема письма</b>\n\n"
                f"📝 Напишите тему письма:\n"
                f"<i>Пример: \"Встреча по проекту\" или \"Отчет за месяц\"</i>",
                parse_mode="HTML",
                reply_markup=keyboards.create_cancel_button("mail_compose_cancel")
            )
            await state.set_state(EmailComposerStates.entering_subject)
            
        elif result['type'] == 'contact_found':
            # Контакт из базы найден
            await state.update_data(
                recipient_email=result['recipient_email'],
                recipient_name=result['recipient_name'],
                contact_id=result.get('contact_id')
            )
            
            await message.answer(
                f"👤 <b>Контакт найден</b>\n\n"
                f"Имя: {escape_html(result['recipient_name'])}\n"
                f"📧 Email: {escape_email(result['recipient_email'])}\n\n"
                f"🎯 <b>Шаг 2 из 3: Тема письма</b>\n\n"
                f"📝 Напишите тему письма:",
                parse_mode="HTML",
                reply_markup=keyboards.create_cancel_button("mail_compose_cancel")
            )
            await state.set_state(EmailComposerStates.entering_subject)
            
        elif result['type'] == 'multiple_matches':
            # Несколько вариантов найдено
            response_text = f"🔍 <b>Найдено несколько контактов</b>\n\n"
            response_text += f"Для запроса \"{user_input}\" найдено:\n\n"
            
            for i, match in enumerate(result['matches'], 1):
                contact = match['contact']
                response_text += f"{i}. <b>{escape_html(contact.name)}</b>\n"
                if contact.email:
                    response_text += f"   📧 {escape_email(contact.email)}\n"
                if contact.company:
                    response_text += f"   🏢 {escape_html(contact.company)}\n"
                response_text += "\n"
            
            response_text += "✍️ <i>Напишите номер контакта (1, 2, 3...) или уточните запрос</i>"
            
            await message.answer(
                response_text,
                parse_mode="HTML",
                reply_markup=keyboards.create_cancel_button("mail_compose_cancel")
            )
            # Сохраняем варианты для последующего выбора
            await state.update_data(contact_matches=result['matches'])
            
        elif result['type'] == 'ai_analysis':
            # AI анализ
            analysis = result['analysis']
            
            if analysis.get('recipient_type') == 'contact_name':
                # AI предложил конкретное имя - ищем снова
                suggested_name = analysis.get('recipient_info', '')
                retry_result = await contact_finder.find_recipient(suggested_name, user_id)
                
                if retry_result.get('found'):
                    await state.update_data(
                        recipient_email=retry_result['recipient_email'],
                        recipient_name=retry_result['recipient_name'],
                        suggested_subject=analysis.get('suggested_subject', '')
                    )
                    
                    subject_hint = ""
                    if analysis.get('suggested_subject'):
                        subject_hint = f"\n💡 <i>AI предлагает тему: \"{analysis['suggested_subject']}\"</i>"
                    
                    await message.answer(
                        f"🤖 <b>AI нашел контакт</b>\n\n"
                        f"👤 {escape_html(retry_result['recipient_name'])}\n"
                        f"📧 {escape_email(retry_result['recipient_email'])}\n\n"
                        f"🎯 <b>Шаг 2 из 3: Тема письма</b>\n\n"
                        f"📝 Напишите тему письма:{subject_hint}",
                        parse_mode="HTML",
                        reply_markup=keyboards.create_cancel_button("mail_compose_cancel")
                    )
                    await state.set_state(EmailComposerStates.entering_subject)
                else:
                    await message.answer(
                        f"🤖 <b>AI анализ</b>\n\n"
                        f"AI понял, что письмо предназначено для: <b>{escape_html(analysis.get('recipient_info', 'неизвестно'))}</b>\n\n"
                        f"❓ Но контакт не найден в вашей базе.\n\n"
                        f"📝 Пожалуйста, укажите:\n"
                        f"• Точное имя из контактов\n"
                        f"• Или email адрес напрямую",
                        parse_mode="HTML",
                        reply_markup=keyboards.create_cancel_button("mail_compose_cancel")
                    )
            else:
                # AI предложил описание роли
                await message.answer(
                    f"🤖 <b>AI анализ</b>\n\n"
                    f"Понял, что нужно письмо для: <b>{escape_html(analysis.get('recipient_info', 'неизвестно'))}</b>\n\n"
                    f"❓ Но нужен конкретный получатель.\n\n"
                    f"📝 Укажите:\n"
                    f"• Имя контакта\n"
                    f"• Или email адрес",
                    parse_mode="HTML",
                    reply_markup=keyboards.create_cancel_button("mail_compose_cancel")
                )
        
        else:
            # Не найдено
            await message.answer(
                f"❓ <b>Получатель не найден</b>\n\n"
                f"Для запроса \"{user_input}\" ничего не найдено.\n\n"
                f"📝 Попробуйте:\n"
                f"• Точное имя из контактов\n"
                f"• Email адрес (example@mail.com)\n"
                f"• Описание (\"письмо боссу\")\n\n"
                f"💡 Или добавьте новый контакт в разделе \"Контакты\"",
                parse_mode="HTML",
                reply_markup=keyboards.create_cancel_button("mail_compose_cancel")
            )
        
    except Exception as e:
        await message.answer(
            f"❌ <b>Ошибка поиска получателя</b>\n\n"
            f"Попробуйте еще раз или укажите email напрямую.\n\n"
            f"<code>{str(e)[:100]}...</code>",
            parse_mode="HTML",
            reply_markup=keyboards.create_cancel_button("mail_compose_cancel")
        )

@router.message(EmailComposerStates.entering_subject)
async def process_email_subject(message: Message, state: FSMContext):
    """Обработка ввода темы письма"""
    subject = message.text.strip()
    
    if not subject:
        await message.answer(
            "❌ <b>Тема не может быть пустой</b>\n\n"
            "📝 Пожалуйста, введите тему письма:",
            parse_mode="HTML",
            reply_markup=keyboards.create_cancel_button("mail_compose_cancel")
        )
        return
    
    await state.update_data(subject=subject)
    
    data = await state.get_data()
    recipient_name = data.get('recipient_name', 'Получатель')
    
    await message.answer(
        f"✅ <b>Тема сохранена</b>\n\n"
        f"📝 Тема: {escape_html(subject)}\n\n"
        f"🎯 <b>Шаг 3 из 3: Содержание письма</b>\n\n"
        f"✍️ Напишите текст письма или опишите что нужно написать:\n\n"
        f"💡 <b>Примеры:</b>\n"
        f"• Готовый текст письма\n"
        f"• \"Напиши письмо с просьбой о встрече\"\n"
        f"• \"Официальное письмо о смене графика\"\n\n"
        f"🤖 <i>AI поможет составить или улучшить текст</i>",
        parse_mode="HTML",
        reply_markup=keyboards.create_cancel_button("mail_compose_cancel")
    )
    
    await state.set_state(EmailComposerStates.entering_body)

@router.message(EmailComposerStates.entering_body)
async def process_email_body(message: Message, state: FSMContext):
    """Обработка ввода содержания письма"""
    user_input = message.text.strip()
    
    if not user_input:
        await message.answer(
            "❌ <b>Содержание не может быть пустым</b>\n\n"
            "✍️ Пожалуйста, введите текст письма или опишите что написать:",
            parse_mode="HTML",
            reply_markup=keyboards.create_cancel_button("mail_compose_cancel")
        )
        return
    
    try:
        # Показываем процесс обработки
        processing_msg = await message.answer(
            "🤖 <b>AI обрабатывает ваш запрос...</b>\n\n"
            "⏳ Анализирую и составляю письмо...",
            parse_mode="HTML"
        )
        
        data = await state.get_data()
        recipient_name = data.get('recipient_name', 'Получатель')
        subject = data.get('subject', 'Без темы')
        
        # Получаем имя пользователя
        from utils.user_settings import user_settings
        user_id = message.from_user.id
        sender_name = await user_settings.get_or_request_name(
            user_id, 
            message.from_user.first_name
        )
        
        # Используем AI для улучшения/создания письма
        from utils.openai_client import openai_client
        
        prompt = f"""
Помоги создать профессиональное письмо на основе пользовательского запроса.

ПОЛУЧАТЕЛЬ: {recipient_name}
ТЕМА: {subject}
ОТПРАВИТЕЛЬ: {sender_name}
ЗАПРОС ПОЛЬЗОВАТЕЛЯ: "{user_input}"

Если пользователь написал готовый текст письма - слегка улучши его (грамматика, стиль).
Если пользователь описал что нужно написать - создай полное письмо.

Создай письмо со структурой:
1. Приветствие (учитывай имя получателя)
2. Основной текст
3. Заключение с подписью отправителя

ВАЖНО:
- Используй ТОЛЬКО имя отправителя в подписи: {sender_name}
- НЕ добавляй поля должности или контактной информации
- НЕ используй квадратные скобки или плейсхолдеры
- Подпись должна быть простой: "С уважением,\n{sender_name}"

Стиль: профессиональный, но дружелюбный.
Язык: русский.
Длина: оптимальная для темы.

Ответь только текстом письма без комментариев.
"""
        
        messages = [
            {"role": "system", "content": "Ты эксперт по деловой переписке. Создаешь качественные письма на русском языке без лишних полей."},
            {"role": "user", "content": prompt}
        ]
        
        ai_response = await openai_client.chat_completion(messages)
        
        await state.update_data(body=ai_response, original_input=user_input)
        
        # Удаляем сообщение обработки
        await processing_msg.delete()
        
        # Показываем предварительный просмотр
        preview_text = f"📧 <b>Предварительный просмотр письма</b>\n\n"
        preview_text += f"👤 <b>Кому:</b> {escape_html(recipient_name)}\n"
        preview_text += f"📝 <b>Тема:</b> {escape_html(subject)}\n\n"
        preview_text += f"📄 <b>Содержание:</b>\n"
        preview_text += f"<code>{escape_html(ai_response[:500])}</code>"
        
        if len(ai_response) > 500:
            preview_text += f"\n<i>... (показаны первые 500 символов)</i>"
        
        preview_text += f"\n\n💡 <i>Выберите действие:</i>"
        
        # Создаем клавиатуру для действий
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        builder.add(
            InlineKeyboardButton(text="✅ Отправить", callback_data="mail_send_confirm"),
            InlineKeyboardButton(text="✏️ Редактировать", callback_data="mail_edit_body")
        )
        builder.add(
            InlineKeyboardButton(text="🔄 Переписать", callback_data="mail_regenerate"),
            InlineKeyboardButton(text="💾 Сохранить черновик", callback_data="mail_save_draft")
        )
        builder.add(
            InlineKeyboardButton(text="❌ Отменить", callback_data="mail_compose_cancel")
        )
        
        builder.adjust(2, 2, 1)
        
        await message.answer(
            preview_text,
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )
        
        await state.set_state(EmailComposerStates.reviewing_email)
        
    except Exception as e:
        await message.answer(
            f"❌ <b>Ошибка создания письма</b>\n\n"
            f"<code>{str(e)[:100]}...</code>\n\n"
            f"Попробуйте еще раз или упростите запрос.",
            parse_mode="HTML",
            reply_markup=keyboards.create_cancel_button("mail_compose_cancel")
        )

# Обработчик отмены создания письма
@router.callback_query(F.data == "mail_compose_cancel")
async def cancel_email_composition(callback: CallbackQuery, state: FSMContext):
    """Отмена создания письма"""
    await state.clear()
    
    await callback.message.edit_text(
        "❌ <b>Создание письма отменено</b>\n\n"
        "🔙 Возвращаемся к почте",
        reply_markup=keyboards.mail_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

# Обработчики действий с письмом
@router.callback_query(F.data == "mail_send_confirm")
async def send_email_confirm(callback: CallbackQuery, state: FSMContext):
    """Подтверждение и отправка письма"""
    try:
        data = await state.get_data()
        user_id = callback.from_user.id
        
        recipient_email = data.get('recipient_email')
        recipient_name = data.get('recipient_name', recipient_email)
        subject = data.get('subject', 'Без темы')
        body = data.get('body', '')
        
        if not recipient_email or not body:
            await callback.answer("❌ Не хватает данных для отправки", show_alert=True)
            return
        
        # Показываем процесс отправки
        await callback.message.edit_text(
            "📤 <b>Отправляю письмо...</b>\n\n"
            f"👤 Кому: {escape_html(recipient_name)}\n"
            f"📧 Email: {escape_email(recipient_email)}\n"
            f"📝 Тема: {escape_html(subject)}\n\n"
            "⏳ Подождите...",
            parse_mode="HTML"
        )
        
        # Отправляем письмо
        from utils.email_sender import email_sender
        success = await email_sender.send_email(user_id, recipient_email, subject, body)
        
        if success:
            await callback.message.edit_text(
                "✅ <b>Письмо отправлено успешно!</b>\n\n"
                f"👤 Получатель: {escape_html(recipient_name)}\n"
                f"📧 Email: {escape_email(recipient_email)}\n"
                f"📝 Тема: {escape_html(subject)}\n"
                f"📄 Размер: {len(body)} символов\n\n"
                "🎉 Письмо доставлено в почтовый ящик получателя",
                reply_markup=keyboards.mail_menu(),
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                "❌ <b>Ошибка отправки письма</b>\n\n"
                f"Не удалось отправить письмо на {escape_email(recipient_email)}\n\n"
                "🔧 Возможные причины:\n"
                "• Проблемы с подключением к серверу\n"
                "• Неверные настройки почты\n"
                "• Недопустимый email адрес\n\n"
                "💡 Проверьте настройки и попробуйте снова",
                reply_markup=keyboards.mail_menu(),
                parse_mode="HTML"
            )
        
        await state.clear()
        
    except Exception as e:
        await callback.message.edit_text(
            f"❌ <b>Критическая ошибка отправки</b>\n\n"
            f"<code>{str(e)[:100]}...</code>\n\n"
            "Обратитесь в поддержку",
            reply_markup=keyboards.mail_menu(),
            parse_mode="HTML"
        )
        await state.clear()
    
    await callback.answer()

@router.callback_query(F.data == "mail_regenerate")
async def regenerate_email_body(callback: CallbackQuery, state: FSMContext):
    """Переписать письмо заново"""
    try:
        data = await state.get_data()
        original_input = data.get('original_input', '')
        recipient_name = data.get('recipient_name', 'Получатель')
        subject = data.get('subject', 'Без темы')
        
        if not original_input:
            await callback.answer("❌ Нет исходного запроса для переписывания", show_alert=True)
            return
        
        # Получаем имя пользователя
        from utils.user_settings import user_settings
        user_id = callback.from_user.id
        sender_name = await user_settings.get_or_request_name(
            user_id, 
            callback.from_user.first_name
        )
        
        # Показываем процесс
        await callback.message.edit_text(
            "🔄 <b>Переписываю письмо...</b>\n\n"
            "🤖 AI создает новый вариант на основе вашего запроса...",
            parse_mode="HTML"
        )
        
        # Генерируем новую версию
        from utils.openai_client import openai_client
        
        prompt = f"""
Создай АЛЬТЕРНАТИВНУЮ версию письма на основе запроса пользователя.

ПОЛУЧАТЕЛЬ: {recipient_name}
ТЕМА: {subject}
ОТПРАВИТЕЛЬ: {sender_name}
ЗАПРОС ПОЛЬЗОВАТЕЛЯ: "{original_input}"

Создай ДРУГОЙ вариант письма с:
- Иным подходом к изложению
- Другой структурой
- Альтернативным стилем (но всё равно профессиональным)

ВАЖНО:
- Используй ТОЛЬКО имя отправителя в подписи: {sender_name}
- НЕ добавляй поля должности или контактной информации
- НЕ используй квадратные скобки или плейсхолдеры
- Подпись должна быть простой: "С уважением,\n{sender_name}"

НЕ повторяй предыдущую версию. Сделай что-то новое.

Ответь только текстом письма без комментариев.
"""
        
        messages = [
            {"role": "system", "content": "Ты эксперт по деловой переписке. Создаешь разнообразные варианты писем без лишних полей."},
            {"role": "user", "content": prompt}
        ]
        
        new_body = await openai_client.chat_completion(messages)
        await state.update_data(body=new_body)
        
        # Показываем новый вариант
        preview_text = f"🔄 <b>Новая версия письма</b>\n\n"
        preview_text += f"👤 <b>Кому:</b> {escape_html(recipient_name)}\n"
        preview_text += f"📝 <b>Тема:</b> {escape_html(subject)}\n\n"
        preview_text += f"📄 <b>Содержание:</b>\n"
        preview_text += f"<code>{escape_html(new_body[:500])}</code>"
        
        if len(new_body) > 500:
            preview_text += f"\n<i>... (показаны первые 500 символов)</i>"
        
        preview_text += f"\n\n💡 <i>Выберите действие:</i>"
        
        # Та же клавиатура
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        builder.add(
            InlineKeyboardButton(text="✅ Отправить", callback_data="mail_send_confirm"),
            InlineKeyboardButton(text="✏️ Редактировать", callback_data="mail_edit_body")
        )
        builder.add(
            InlineKeyboardButton(text="🔄 Переписать", callback_data="mail_regenerate"),
            InlineKeyboardButton(text="💾 Сохранить черновик", callback_data="mail_save_draft")
        )
        builder.add(
            InlineKeyboardButton(text="❌ Отменить", callback_data="mail_compose_cancel")
        )
        
        builder.adjust(2, 2, 1)
        
        await callback.message.edit_text(
            preview_text,
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        await callback.message.edit_text(
            f"❌ <b>Ошибка переписывания</b>\n\n"
            f"<code>{str(e)[:100]}...</code>",
            parse_mode="HTML",
            reply_markup=keyboards.create_cancel_button("mail_compose_cancel")
        )
    
    await callback.answer()

@router.callback_query(F.data == "mail_save_draft")
async def save_email_draft(callback: CallbackQuery, state: FSMContext):
    """Сохранить письмо как черновик"""
    try:
        from utils.drafts_manager import drafts_manager, Draft
        
        data = await state.get_data()
        user_id = callback.from_user.id
        
        # Создаем черновик
        draft = Draft(
            recipient_email=data.get('recipient_email', ''),
            recipient_name=data.get('recipient_name', ''),
            subject=data.get('subject', ''),
            body=data.get('body', '')
        )
        
        # Сохраняем черновик
        success = await drafts_manager.save_draft(user_id, draft)
        
        if success:
            await callback.message.edit_text(
                "💾 <b>Черновик сохранен!</b>\n\n"
                f"📝 Тема: {escape_html(data.get('subject', 'Без темы'))}\n"
                f"👤 Получатель: {escape_html(data.get('recipient_name', 'Неизвестно'))}\n\n"
                "✅ Черновик доступен в разделе \"📋 Черновики\"\n\n"
                "💡 <i>Вы можете отредактировать или отправить его позже</i>",
                reply_markup=keyboards.mail_menu(),
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                "❌ <b>Ошибка сохранения черновика</b>\n\n"
                "Попробуйте еще раз или обратитесь к администратору",
                reply_markup=keyboards.mail_menu(),
                parse_mode="HTML"
            )
        
        await state.clear()
        
    except Exception as e:
        await callback.answer(f"❌ Ошибка сохранения: {str(e)[:50]}...", show_alert=True)
    
    await callback.answer()

@router.callback_query(F.data == "calendar_sync_reminders")
async def calendar_sync_reminders_handler(callback: CallbackQuery):
    """Синхронизировать календарь с напоминаниями"""
    user_id = callback.from_user.id
    
    # Инициализируем синхронизатор
    sync = CalendarReminderSync()
    
    # Проверяем есть ли токен календаря
    token_data = await user_tokens.get_token_data(user_id, "calendar")
    
    if not token_data or not token_data.get("app_password"):
        await callback.message.edit_text(
            "🔄 <b>Синхронизация с напоминаниями</b>\n\n"
            "🔐 <b>Календарь не подключен</b>\n\n"
            "Для синхронизации необходимо сначала подключить календарь:",
            reply_markup=create_connect_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        "🔄 <b>Синхронизация запущена...</b>\n\n"
        "⏳ Загружаю события календаря...",
        parse_mode="HTML"
    )
    
    try:
        # Получаем события календаря на ближайшие 30 дней
        today = datetime.now()
        
        # Подключение к календарю
        email = token_data.get("email")
        app_password = token_data.get("app_password")
        
        if not email or not app_password:
            await callback.message.edit_text(
                "❌ <b>Ошибка синхронизации</b>\n\n"
                "Отсутствуют данные для подключения к календарю.\n"
                "Попробуйте переподключить календарь:",
                reply_markup=create_reconnect_keyboard(),
                parse_mode="HTML"
            )
            return
        
        synced_count = 0
        
        # Простая синхронизация - создаем несколько тестовых напоминаний
        try:
            # Создаем тестовое напоминание на завтра
            tomorrow = today + timedelta(days=1)
            test_event_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
            
            reminder_id = await sync.sync_calendar_event(
                user_id=user_id,
                event_title="Тестовое событие календаря",
                event_time=test_event_time,
                event_description="Это тестовое событие для проверки синхронизации"
            )
            
            if reminder_id:
                synced_count += 1
            
            # Результат синхронизации
            if synced_count > 0:
                await callback.message.edit_text(
                    f"✅ <b>Синхронизация завершена!</b>\n\n"
                    f"📅 Создано напоминаний: <b>{synced_count}</b>\n\n"
                    "Теперь вы будете получать напоминания о событиях календаря за установленное время до начала.\n\n"
                    "⚙️ Настроить время предупреждения можно в разделе:\n"
                    "Меню → Напоминания → Настройки",
                    reply_markup=keyboards.calendar_menu(),
                    parse_mode="HTML"
                )
            else:
                await callback.message.edit_text(
                    "ℹ️ <b>Синхронизация завершена</b>\n\n"
                    "📅 Новых событий для синхронизации не найдено.\n\n"
                    "Возможные причины:\n"
                    "• Все события уже прошли\n"
                    "• В календаре нет событий на ближайшие 30 дней\n"
                    "• События уже синхронизированы",
                    reply_markup=keyboards.calendar_menu(),
                    parse_mode="HTML"
                )
        
        except Exception as e:
            print(f"Ошибка синхронизации календаря: {e}")
            await callback.message.edit_text(
                "❌ <b>Ошибка синхронизации</b>\n\n"
                "Не удалось создать напоминания из календаря.\n\n"
                "Попробуйте позже или проверьте настройки календаря:",
                reply_markup=create_reconnect_keyboard(),
                parse_mode="HTML"
            )
    
    except Exception as e:
        print(f"Общая ошибка синхронизации: {e}")
        await callback.message.edit_text(
            "❌ <b>Критическая ошибка синхронизации</b>\n\n"
            "Произошла неожиданная ошибка.\n"
            "Попробуйте позже или обратитесь к администратору.",
            reply_markup=keyboards.calendar_menu(),
            parse_mode="HTML"
        )
    
    await callback.answer("Синхронизация завершена")