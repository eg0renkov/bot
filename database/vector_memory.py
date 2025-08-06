import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from config.settings import settings
from utils.openai_client import openai_client

class VectorMemory:
    """Векторная память для семантического поиска и долгосрочного запоминания"""
    
    def __init__(self):
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise ValueError("Supabase не настроен для векторной памяти")
        
        try:
            from supabase import create_client
            self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        except ImportError:
            raise ImportError("Установите supabase: pip install supabase")
    
    async def get_embedding(self, text: str) -> List[float]:
        """Получить векторное представление текста через OpenAI"""
        try:
            response = openai_client.client.embeddings.create(
                model="text-embedding-ada-002",
                input=text.replace("\n", " ")
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Ошибка получения embedding: {e}")
            return None
    
    async def save_conversation(self, user_id: int, user_message: str, ai_response: str):
        """Сохранить диалог с векторным представлением"""
        try:
            # Создаем текст для embedding (комбинируем вопрос и ответ)
            combined_text = f"Пользователь: {user_message}\nАссистент: {ai_response}"
            embedding = await self.get_embedding(combined_text)
            
            if not embedding:
                print("Не удалось создать embedding, сохраняем без вектора")
                embedding = None
            
            data = {
                'user_id': user_id,
                'user_message': user_message,
                'ai_response': ai_response,
                'embedding': embedding,
                'created_at': datetime.now().isoformat()
            }
            
            result = self.client.table('conversations').insert(data).execute()
            
            # Обновляем профиль пользователя
            await self.update_user_profile(user_id, user_message)
            
            return result
            
        except Exception as e:
            print(f"Ошибка сохранения разговора: {e}")
    
    async def search_similar_conversations(self, user_id: int, query: str, limit: int = 5) -> List[Dict]:
        """Найти похожие разговоры для контекста"""
        try:
            query_embedding = await self.get_embedding(query)
            if not query_embedding:
                return []
            
            # Используем RPC функцию для векторного поиска
            result = self.client.rpc(
                'search_similar_conversations',
                {
                    'query_embedding': query_embedding,
                    'user_id_param': user_id,
                    'match_threshold': 0.7,
                    'match_count': limit
                }
            ).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Ошибка поиска похожих разговоров: {e}")
            return []
    
    async def save_to_knowledge_base(self, user_id: int, topic: str, content: str, importance: float = 1.0):
        """Сохранить важную информацию в базу знаний"""
        try:
            embedding = await self.get_embedding(f"{topic}: {content}")
            
            data = {
                'user_id': user_id,
                'topic': topic,
                'content': content,
                'embedding': embedding,
                'importance_score': importance,
                'created_at': datetime.now().isoformat()
            }
            
            result = self.client.table('knowledge_base').insert(data).execute()
            return result
            
        except Exception as e:
            print(f"Ошибка сохранения в базу знаний: {e}")
    
    async def search_knowledge_base(self, user_id: int, query: str, limit: int = 3) -> List[Dict]:
        """Поиск в базе знаний пользователя"""
        try:
            query_embedding = await self.get_embedding(query)
            if not query_embedding:
                return []
            
            result = self.client.rpc(
                'search_knowledge_base',
                {
                    'query_embedding': query_embedding,
                    'user_id_param': user_id,
                    'match_threshold': 0.8,
                    'match_count': limit
                }
            ).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Ошибка поиска в базе знаний: {e}")
            return []
    
    async def update_user_profile(self, user_id: int, message: str):
        """Обновить профиль пользователя"""
        try:
            # Проверяем существует ли профиль
            existing = self.client.table('user_profiles').select('*').eq('user_id', user_id).execute()
            
            if existing.data:
                # Обновляем существующий профиль
                self.client.table('user_profiles').update({
                    'total_messages': existing.data[0]['total_messages'] + 1,
                    'updated_at': datetime.now().isoformat()
                }).eq('user_id', user_id).execute()
            else:
                # Создаем новый профиль
                self.client.table('user_profiles').insert({
                    'user_id': user_id,
                    'total_messages': 1,
                    'preferences': {},
                    'created_at': datetime.now().isoformat()
                }).execute()
                
        except Exception as e:
            print(f"Ошибка обновления профиля: {e}")
    
    async def get_user_stats(self, user_id: int) -> Dict:
        """Получить статистику пользователя"""
        try:
            # Пробуем использовать RPC функцию
            result = self.client.rpc('get_user_stats', {'user_id_param': user_id}).execute()
            
            if result.data:
                return result.data[0]
            return {
                'total_conversations': 0,
                'knowledge_entries': 0,
                'avg_conversation_length': 0,
                'first_interaction': None,
                'last_interaction': None
            }
            
        except Exception as e:
            print(f"Ошибка получения статистики через RPC: {e}")
            # Fallback: получаем статистику через прямые запросы
            try:
                # Получаем количество разговоров
                conversations_result = self.client.table('conversations')\
                    .select('*', count='exact')\
                    .eq('user_id', user_id)\
                    .execute()
                total_conversations = conversations_result.count or 0
                
                # Получаем количество записей знаний
                knowledge_result = self.client.table('knowledge_base')\
                    .select('*', count='exact')\
                    .eq('user_id', user_id)\
                    .execute()
                knowledge_entries = knowledge_result.count or 0
                
                # Получаем даты
                dates_result = self.client.table('conversations')\
                    .select('created_at')\
                    .eq('user_id', user_id)\
                    .order('created_at', desc=False)\
                    .execute()
                
                first_interaction = None
                last_interaction = None
                if dates_result.data:
                    first_interaction = dates_result.data[0]['created_at']
                    last_interaction = dates_result.data[-1]['created_at']
                
                return {
                    'total_conversations': total_conversations,
                    'knowledge_entries': knowledge_entries,
                    'avg_conversation_length': 50,  # Примерное значение
                    'first_interaction': first_interaction,
                    'last_interaction': last_interaction
                }
                
            except Exception as fallback_error:
                print(f"Ошибка получения статистики через fallback: {fallback_error}")
                return {
                    'total_conversations': 0,
                    'knowledge_entries': 0,
                    'avg_conversation_length': 0,
                    'first_interaction': None,
                    'last_interaction': None
                }
    
    async def get_enhanced_context(self, user_id: int, current_message: str, history_limit: int = 5) -> Dict:
        """Получить расширенный контекст для AI"""
        try:
            # Получаем недавнюю историю
            recent_history = self.client.table('conversations')\
                .select('user_message, ai_response, created_at')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .limit(history_limit)\
                .execute()
            
            # Ищем похожие разговоры
            similar_conversations = await self.search_similar_conversations(user_id, current_message, 3)
            
            # Ищем релевантную информацию в базе знаний
            knowledge = await self.search_knowledge_base(user_id, current_message, 2)
            
            return {
                'recent_history': recent_history.data[::-1] if recent_history.data else [],
                'similar_conversations': similar_conversations,
                'knowledge_base': knowledge,
                'has_context': bool(recent_history.data or similar_conversations or knowledge)
            }
            
        except Exception as e:
            print(f"Ошибка получения контекста: {e}")
            return {
                'recent_history': [],
                'similar_conversations': [],
                'knowledge_base': [],
                'has_context': False
            }
    
    async def analyze_and_extract_knowledge(self, user_id: int, conversation_text: str):
        """Анализировать разговор и извлекать важную информацию"""
        try:
            # Простая эвристика для определения важности
            keywords_important = ['помню', 'важно', 'запомни', 'всегда', 'никогда', 'люблю', 'ненавижу', 'предпочитаю']
            keywords_personal = ['меня зовут', 'я работаю', 'мой', 'моя', 'мне нравится', 'я живу']
            
            text_lower = conversation_text.lower()
            
            importance_score = 1.0
            if any(keyword in text_lower for keyword in keywords_important):
                importance_score += 0.5
            if any(keyword in text_lower for keyword in keywords_personal):
                importance_score += 0.3
            
            # Если важность высокая, сохраняем в базу знаний
            if importance_score > 1.3:
                topic = "Личная информация" if any(keyword in text_lower for keyword in keywords_personal) else "Важная информация"
                await self.save_to_knowledge_base(user_id, topic, conversation_text, importance_score)
                
        except Exception as e:
            print(f"Ошибка анализа разговора: {e}")
    
    async def cleanup_old_data(self, days_to_keep: int = 90):
        """Очистить старые данные"""
        try:
            result = self.client.rpc('cleanup_old_data', {'days_to_keep': days_to_keep}).execute()
            return result.data
        except Exception as e:
            print(f"Ошибка очистки данных: {e}")
    
    async def clear_user_memory(self, user_id: int):
        """Очистить всю память пользователя"""
        try:
            # Удаляем разговоры
            self.client.table('conversations').delete().eq('user_id', user_id).execute()
            
            # Удаляем базу знаний
            self.client.table('knowledge_base').delete().eq('user_id', user_id).execute()
            
            # Сбрасываем счетчики в профиле
            self.client.table('user_profiles').update({
                'total_messages': 0,
                'updated_at': datetime.now().isoformat()
            }).eq('user_id', user_id).execute()
            
            return True
            
        except Exception as e:
            print(f"Ошибка очистки памяти: {e}")
            return False


# Фабрика для создания векторной памяти
def create_vector_memory():
    """Создать объект векторной памяти если настроена"""
    if (settings.SUPABASE_URL and 
        settings.SUPABASE_KEY and 
        getattr(settings, 'VECTOR_MEMORY_ENABLED', False)):
        try:
            return VectorMemory()
        except (ValueError, ImportError) as e:
            print(f"Векторная память недоступна: {e}")
            return None
    return None

vector_memory = create_vector_memory()