"""
Модуль для веб-поиска через SERP API
"""
import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from config.settings import settings

logger = logging.getLogger(__name__)

class WebSearcher:
    """Класс для веб-поиска через SERP API"""
    
    def __init__(self):
        """Инициализация поисковика"""
        self.api_key = settings.SERP_API_KEY
        self.base_url = "https://serpapi.com/search.json"
        self.session = None
    
    async def __aenter__(self):
        """Асинхронный контекст менеджер - вход"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Асинхронный контекст менеджер - выход"""
        if self.session:
            await self.session.close()
    
    async def search(
        self,
        query: str,
        num_results: int = 10,
        location: str = "Russia",
        language: str = "ru"
    ) -> List[Dict[str, Any]]:
        """
        Выполнить веб-поиск
        
        Args:
            query: Поисковый запрос
            num_results: Количество результатов
            location: Локация поиска
            language: Язык поиска
            
        Returns:
            Список результатов поиска
        """
        if not self.api_key:
            logger.error("SERP API ключ не настроен")
            return []
        
        try:
            params = {
                'q': query,
                'api_key': self.api_key,
                'engine': 'google',
                'num': num_results,
                'location': location,
                'hl': language,
                'gl': 'ru'
            }
            
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_results(data)
                else:
                    logger.error(f"Ошибка SERP API: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Ошибка веб-поиска: {e}")
            return []
    
    def _parse_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Парсить результаты SERP API
        
        Args:
            data: Сырые данные от API
            
        Returns:
            Список обработанных результатов
        """
        results = []
        
        # Основные результаты поиска
        organic_results = data.get('organic_results', [])
        for result in organic_results:
            parsed_result = {
                'title': result.get('title', ''),
                'link': result.get('link', ''),
                'snippet': result.get('snippet', ''),
                'source': 'organic',
                'position': result.get('position', 0)
            }
            results.append(parsed_result)
        
        # Новости (если есть)
        news_results = data.get('news_results', [])
        for result in news_results:
            parsed_result = {
                'title': result.get('title', ''),
                'link': result.get('link', ''),
                'snippet': result.get('snippet', ''),
                'source': 'news',
                'date': result.get('date', ''),
                'thumbnail': result.get('thumbnail', '')
            }
            results.append(parsed_result)
        
        # Ответы (featured snippets)
        answer_box = data.get('answer_box')
        if answer_box:
            parsed_result = {
                'title': answer_box.get('title', ''),
                'link': answer_box.get('link', ''),
                'snippet': answer_box.get('snippet', ''),
                'source': 'answer_box',
                'type': answer_box.get('type', '')
            }
            results.insert(0, parsed_result)  # Ставим в начало
        
        # Блок знаний
        knowledge_graph = data.get('knowledge_graph')
        if knowledge_graph:
            parsed_result = {
                'title': knowledge_graph.get('title', ''),
                'description': knowledge_graph.get('description', ''),
                'source': 'knowledge_graph',
                'type': knowledge_graph.get('type', ''),
                'thumbnail': knowledge_graph.get('thumbnail', '')
            }
            results.insert(0, parsed_result)  # Ставим в начало
        
        return results
    
    async def search_news(
        self,
        query: str,
        num_results: int = 10,
        language: str = "ru",
        country: str = "ru"
    ) -> List[Dict[str, Any]]:
        """
        Поиск новостей
        
        Args:
            query: Поисковый запрос
            num_results: Количество результатов
            language: Язык поиска
            
        Returns:
            Список новостей
        """
        if not self.api_key:
            logger.error("SERP API ключ не настроен")
            return []
        
        try:
            # Улучшаем запрос для получения качественных новостей
            if not query or query.strip() in ['последние новости', 'актуальные новости', '']:
                query = 'новости России сегодня'
            
            params = {
                'q': query,
                'api_key': self.api_key,
                'engine': 'google_news',
                'num': num_results,
                'hl': language,
                'gl': country,
                'tbm': 'nws',  # Только новости
                'tbs': 'qdr:d'  # Только за последний день
            }
            
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_news_results(data)
                else:
                    logger.error(f"Ошибка SERP API (новости): {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Ошибка поиска новостей: {e}")
            return []
    
    def _filter_spam_news(self, title: str, snippet: str, source: str) -> bool:
        """Фильтровать спам и рекламные новости"""
        spam_keywords = [
            'букмекер', 'букмекер', 'ставки', 'промокод', 'фрибет', 'бонус',
            'казино', 'игровые автоматы', 'слоты', 'покер', 'рулетка',
            'заработок в интернете', 'быстрые деньги', 'инвестиции с гарантией',
            'форекс', 'бинарные опционы', 'криптовалюта заработок',
            'похудение за', 'диета чудо', 'увеличение', 'потенция'
        ]
        
        spam_sources = [
            'bookmaker-ratings.ru', 'legalbet.ru', 'vseprosport.ru',
            'stavka.tv', 'metaratings.ru', 'odds.ru'
        ]
        
        text_to_check = f"{title.lower()} {snippet.lower()}"
        
        # Проверяем спам-ключевые слова
        for keyword in spam_keywords:
            if keyword in text_to_check:
                return False
        
        # Проверяем спам-источники
        for spam_source in spam_sources:
            if spam_source.lower() in source.lower():
                return False
                
        return True
    
    def _parse_news_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Парсить результаты поиска новостей
        
        Args:
            data: Сырые данные от API
            
        Returns:
            Список новостей
        """
        results = []
        
        news_results = data.get('news_results', [])
        for result in news_results:
            title = result.get('title', '')
            snippet = result.get('snippet', '')
            source = result.get('source', '')
            
            # Фильтруем спам
            if not self._filter_spam_news(title, snippet, source):
                continue
                
            parsed_result = {
                'title': title,
                'link': result.get('link', ''),
                'snippet': snippet,
                'source': source,
                'date': result.get('date', ''),
                'thumbnail': result.get('thumbnail', ''),
                'position': result.get('position', 0)
            }
            results.append(parsed_result)
        
        return results
    
    def format_search_results(self, results: List[Dict[str, Any]], max_results: int = 5, max_length: int = 3500) -> str:
        """
        Форматировать результаты поиска для отображения
        
        Args:
            results: Результаты поиска
            max_results: Максимальное количество результатов
            
        Returns:
            Отформатированный текст
        """
        if not results:
            return "🔍 По вашему запросу ничего не найдено."
        
        formatted_text = "🌐 **Результаты веб-поиска:**\n\n"
        
        for i, result in enumerate(results[:max_results], 1):
            title = result.get('title', 'Без названия')[:80]
            snippet = result.get('snippet', '')[:200]
            link = result.get('link', '')
            source = result.get('source', 'web')
            
            # Эмодзи для разных типов результатов
            emoji_map = {
                'answer_box': '💡',
                'knowledge_graph': '📚',
                'news': '📰',
                'organic': '🔗'
            }
            emoji = emoji_map.get(source, '🔗')
            
            formatted_text += f"{emoji} **{i}. {title}**\n"
            
            if snippet:
                formatted_text += f"   {snippet}\n"
            
            if link and len(link) < 100:
                formatted_text += f"   🔗 [{link}]({link})\n"
            
            formatted_text += "\n"
        
        # Добавляем информацию о количестве результатов
        total_count = len(results)
        if total_count > max_results:
            formatted_text += f"_Показано {max_results} из {total_count} результатов_\n"
        
        # Обрезаем сообщение если оно слишком длинное
        if len(formatted_text) > max_length:
            formatted_text = formatted_text[:max_length-100] + "\n\n...\n\n📝 _Результаты сокращены из-за ограничений Telegram_"
        
        return formatted_text
    
    async def quick_search(self, query: str) -> str:
        """
        Быстрый поиск с форматированным ответом
        
        Args:
            query: Поисковый запрос
            
        Returns:
            Отформатированные результаты
        """
        async with self:
            results = await self.search(query, num_results=5)
            return self.format_search_results(results)
    
    async def search_and_summarize(self, query: str, context: str = "") -> str:
        """
        Поиск с AI-суммаризацией результатов
        
        Args:
            query: Поисковый запрос
            context: Дополнительный контекст
            
        Returns:
            Суммаризованный ответ
        """
        async with self:
            results = await self.search(query, num_results=3)
            
            if not results:
                return "Извините, по вашему запросу ничего не найдено."
            
            # Собираем информацию из результатов
            search_info = ""
            for result in results:
                title = result.get('title', '')
                snippet = result.get('snippet', '')
                search_info += f"Заголовок: {title}\nОписание: {snippet}\n\n"
            
            # Здесь можно добавить интеграцию с OpenAI для суммаризации
            # Пока возвращаем простой формат
            summary = f"🔍 **Поиск по запросу:** {query}\n\n"
            summary += "📋 **Краткая сводка:**\n"
            
            for i, result in enumerate(results[:3], 1):
                title = result.get('title', '')[:60]
                snippet = result.get('snippet', '')[:150]
                summary += f"\n**{i}. {title}**\n{snippet}...\n"
            
            return summary
    
    async def get_daily_news_summary(self, query: str = "новости России сегодня") -> str:
        """
        Получить краткую сводку новостей за день с AI-анализом
        
        Args:
            query: Поисковый запрос для новостей
            
        Returns:
            Краткая сводка новостей
        """
        try:
            async with self:
                # Получаем больше новостей для лучшего анализа
                news_results = await self.search_news(query, num_results=15)
                
                if not news_results:
                    return "📰 К сожалению, актуальных новостей за сегодня не найдено."
                
                # Берем только топ-5 качественных новостей
                top_news = news_results[:5]
                
                # Собираем краткую информацию о новостях
                news_summary = "📰 **Сводка новостей на сегодня:**\n\n"
                
                for i, news in enumerate(top_news, 1):
                    title = news.get('title', 'Без названия')[:100]
                    source = news.get('source', 'Источник не указан')
                    date = news.get('date', '')
                    
                    news_summary += f"**{i}. {title}**\n"
                    if source:
                        news_summary += f"   📡 {source}"
                    if date:
                        news_summary += f" | 📅 {date}"
                    news_summary += "\n\n"
                
                # Если AI доступен, добавляем краткий анализ
                try:
                    from utils.openai_client import openai_client
                    
                    # Создаем промпт для анализа новостей
                    prompt = f"""Проанализируй следующие новости и создай краткую сводку (2-3 предложения) основных событий дня:

{chr(10).join([f"- {news.get('title', '')}: {news.get('snippet', '')[:100]}" for news in top_news])}

Сводка должна быть на русском языке, краткой и информативной."""

                    ai_summary = await openai_client.get_response(prompt, system_message="Ты - новостной аналитик. Создавай краткие и точные сводки новостей.")
                    
                    news_summary += f"🤖 **AI-анализ дня:**\n{ai_summary}\n\n"
                    
                except Exception as ai_error:
                    logger.warning(f"AI-анализ недоступен: {ai_error}")
                
                news_summary += f"📊 _Показано {len(top_news)} из {len(news_results)} новостей_"
                
                return news_summary
                
        except Exception as e:
            logger.error(f"Ошибка получения сводки новостей: {e}")
            return "❌ Ошибка получения сводки новостей. Попробуйте позже."

# Создаем глобальный экземпляр
web_searcher = WebSearcher()