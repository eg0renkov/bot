"""
Обработчики команд веб-поиска
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from utils.keyboards import BotKeyboards
from utils.web_search import web_searcher

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

router = Router()
logger = logging.getLogger(__name__)

class WebSearchStates(StatesGroup):
    """Состояния для веб-поиска"""
    waiting_for_query = State()
    waiting_for_news_query = State()

keyboards = BotKeyboards()

@router.callback_query(F.data == "web_search")
async def web_search_menu(callback: CallbackQuery):
    """Меню веб-поиска"""
    try:
        keyboard = keyboards.web_search_menu()
        
        text = """🌐 **Веб-поиск**

Выберите тип поиска:

🔍 **Обычный поиск** - поиск по всему интернету
📰 **Поиск новостей** - только свежие новости
💡 **Умный поиск** - поиск с AI-анализом результатов

Поиск работает через SERP API и возвращает актуальную информацию."""

        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Ошибка меню веб-поиска: {e}")
        await callback.answer("❌ Ошибка загрузки меню поиска")

@router.callback_query(F.data == "web_search_general")
async def start_general_search(callback: CallbackQuery, state: FSMContext):
    """Начать обычный поиск"""
    try:
        await state.set_state(WebSearchStates.waiting_for_query)
        
        keyboard = keyboards.create_cancel_button("web_search")
        
        await callback.message.edit_text(
            text="🔍 **Обычный веб-поиск**\n\nВведите ваш поисковый запрос:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Ошибка запуска поиска: {e}")
        await callback.answer("❌ Ошибка запуска поиска")

@router.callback_query(F.data == "web_search_news")
async def start_news_search(callback: CallbackQuery, state: FSMContext):
    """Начать поиск новостей"""
    try:
        await state.set_state(WebSearchStates.waiting_for_news_query)
        
        keyboard = keyboards.create_cancel_button("web_search")
        
        await callback.message.edit_text(
            text="📰 **Поиск новостей**\n\nВведите тему для поиска новостей:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Ошибка запуска поиска новостей: {e}")
        await callback.answer("❌ Ошибка запуска поиска новостей")

@router.callback_query(F.data == "web_search_smart")
async def start_smart_search(callback: CallbackQuery, state: FSMContext):
    """Начать умный поиск"""
    try:
        await state.set_state(WebSearchStates.waiting_for_query)
        await state.update_data(smart_search=True)
        
        keyboard = keyboards.create_cancel_button("web_search")
        
        await callback.message.edit_text(
            text="💡 **Умный поиск**\n\nВведите ваш вопрос. AI проанализирует результаты и даст краткий ответ:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Ошибка запуска умного поиска: {e}")
        await callback.answer("❌ Ошибка запуска умного поиска")

@router.message(WebSearchStates.waiting_for_query)
async def process_search_query(message: Message, state: FSMContext):
    """Обработать поисковый запрос"""
    try:
        query = message.text.strip()
        if not query:
            await message.answer("❌ Введите непустой поисковый запрос")
            return
        
        # Показываем индикатор загрузки
        search_msg = await message.answer("🔍 Выполняю поиск, пожалуйста подождите...")
        
        # Получаем данные состояния
        data = await state.get_data()
        is_smart_search = data.get('smart_search', False)
        
        try:
            if is_smart_search:
                # Умный поиск с суммаризацией
                result = await web_searcher.search_and_summarize(query)
            else:
                # Обычный поиск
                result = await web_searcher.quick_search(query)
            
            # Обрезаем результат если он слишком длинный
            result = truncate_message(result)
            
            # Создаем клавиатуру с дополнительными действиями
            keyboard = keyboards.search_results_menu()
            
            await search_msg.edit_text(
                text=result,
                reply_markup=keyboard,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
            
        except Exception as search_error:
            logger.error(f"Ошибка выполнения поиска: {search_error}")
            await search_msg.edit_text(
                text=f"❌ Ошибка поиска: {search_error}",
                reply_markup=keyboards.back_button("web_search")
            )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка обработки поискового запроса: {e}")
        await message.answer(
            "❌ Ошибка обработки запроса",
            reply_markup=keyboards.back_button("web_search")
        )
        await state.clear()

@router.message(WebSearchStates.waiting_for_news_query)
async def process_news_query(message: Message, state: FSMContext):
    """Обработать запрос поиска новостей"""
    try:
        query = message.text.strip()
        if not query:
            await message.answer("❌ Введите непустой поисковый запрос")
            return
        
        # Показываем индикатор загрузки
        search_msg = await message.answer("📰 Ищу новости, пожалуйста подождите...")
        
        try:
            # Поиск новостей
            async with web_searcher:
                news_results = await web_searcher.search_news(query, num_results=5)
                
                if not news_results:
                    result = f"📰 По запросу '{query}' новостей не найдено."
                else:
                    result = f"📰 **Новости по запросу:** {query}\n\n"
                    
                    for i, news in enumerate(news_results, 1):
                        title = news.get('title', 'Без названия')[:70]
                        source = news.get('source', 'Неизвестный источник')
                        date = news.get('date', '')
                        snippet = news.get('snippet', '')[:150]
                        link = news.get('link', '')
                        
                        result += f"📰 **{i}. {title}**\n"
                        result += f"   📅 {date} | 📡 {source}\n"
                        if snippet:
                            result += f"   {snippet}...\n"
                        if link:
                            result += f"   🔗 [Читать полностью]({link})\n"
                        result += "\n"
            
            # Обрезаем результат если он слишком длинный
            result = truncate_message(result)
            
            # Создаем клавиатуру
            keyboard = keyboards.search_results_menu()
            
            await search_msg.edit_text(
                text=result,
                reply_markup=keyboard,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
            
        except Exception as search_error:
            logger.error(f"Ошибка поиска новостей: {search_error}")
            await search_msg.edit_text(
                text=f"❌ Ошибка поиска новостей: {search_error}",
                reply_markup=keyboards.back_button("web_search")
            )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка обработки запроса новостей: {e}")
        await message.answer(
            "❌ Ошибка обработки запроса",
            reply_markup=keyboards.back_button("web_search")
        )
        await state.clear()

@router.callback_query(F.data == "search_new_query")
async def new_search(callback: CallbackQuery, state: FSMContext):
    """Новый поиск"""
    await web_search_menu(callback)

@router.callback_query(F.data == "search_to_menu")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    """Вернуться в главное меню"""
    await state.clear()
    
    from handlers.menu_handlers import show_main_menu
    await show_main_menu(callback)

# Команда для быстрого поиска из любого места
@router.message(F.text.startswith("/search "))
async def quick_search_command(message: Message):
    """Быстрая команда поиска /search [запрос]"""
    try:
        query = message.text[8:].strip()  # Убираем "/search "
        if not query:
            await message.answer("❌ Введите поисковый запрос после команды\nПример: /search погода в Москве")
            return
        
        search_msg = await message.answer("🔍 Выполняю поиск...")
        
        try:
            result = await web_searcher.quick_search(query)
            result = truncate_message(result)
            keyboard = keyboards.search_results_menu()
            
            await search_msg.edit_text(
                text=result,
                reply_markup=keyboard,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
            
        except Exception as search_error:
            logger.error(f"Ошибка быстрого поиска: {search_error}")
            await search_msg.edit_text(
                text=f"❌ Ошибка поиска: {search_error}",
                reply_markup=keyboards.back_button("menu_back")
            )
    
    except Exception as e:
        logger.error(f"Ошибка команды быстрого поиска: {e}")
        await message.answer("❌ Ошибка выполнения поиска")

# Команда для поиска новостей
@router.message(F.text.startswith("/news "))
async def quick_news_command(message: Message):
    """Быстрая команда поиска новостей /news [запрос]"""
    try:
        query = message.text[6:].strip()  # Убираем "/news "
        if not query:
            await message.answer("❌ Введите тему для поиска новостей\nПример: /news технологии")
            return
        
        search_msg = await message.answer("📰 Ищу новости...")
        
        try:
            async with web_searcher:
                news_results = await web_searcher.search_news(query, num_results=3)
                result = web_searcher.format_search_results(news_results, max_results=3)
            
            result = truncate_message(result)
            keyboard = keyboards.search_results_menu()
            
            await search_msg.edit_text(
                text=result,
                reply_markup=keyboard,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
            
        except Exception as search_error:
            logger.error(f"Ошибка поиска новостей: {search_error}")
            await search_msg.edit_text(
                text=f"❌ Ошибка поиска новостей: {search_error}",
                reply_markup=keyboards.back_button("menu_back")
            )
    
    except Exception as e:
        logger.error(f"Ошибка команды поиска новостей: {e}")
        await message.answer("❌ Ошибка выполнения поиска новостей")