import re
from typing import List, Dict, Optional, Tuple
from database.contacts import contacts_manager
from utils.openai_client import openai_client


class ContactFinder:
    """Поиск и анализ получателей для писем"""
    
    async def find_recipient(self, user_input: str, user_id: int) -> Dict:
        """
        Анализирует ввод пользователя и определяет получателя
        
        Returns:
            Dict с ключами: type, recipient_email, recipient_name, confidence, suggestions
        """
        user_input = user_input.strip()
        
        # 1. Проверяем на прямой email
        email_match = self._extract_email(user_input)
        if email_match:
            return {
                'type': 'direct_email',
                'recipient_email': email_match,
                'recipient_name': email_match,
                'confidence': 'high',
                'suggestions': []
            }
        
        # 2. Ищем по контактам
        contact_results = await self._search_contacts(user_input, user_id)
        if contact_results['found']:
            return contact_results
        
        # 3. Анализируем с помощью AI
        ai_analysis = await self._analyze_with_ai(user_input, user_id)
        return ai_analysis
    
    def _extract_email(self, text: str) -> Optional[str]:
        """Извлекает email адрес из текста"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, text)
        return match.group(0) if match else None
    
    async def _search_contacts(self, query: str, user_id: int) -> Dict:
        """Поиск в контактах пользователя"""
        try:
            # Получаем все контакты пользователя
            all_contacts = await contacts_manager.get_user_contacts(user_id)
            
            if not all_contacts:
                return {
                    'type': 'no_contacts',
                    'found': False,
                    'suggestions': [],
                    'message': 'У вас пока нет сохраненных контактов'
                }
            
            # Поиск по имени (нечеткий поиск)
            matches = []
            query_lower = query.lower()
            
            for contact in all_contacts:
                # Проверяем совпадение по имени
                name_score = self._calculate_similarity(query_lower, contact.name.lower())
                
                # Проверяем совпадение по email
                email_score = 0
                if contact.email and query_lower in contact.email.lower():
                    email_score = 0.8
                
                # Проверяем совпадение по компании
                company_score = 0
                if contact.company and query_lower in contact.company.lower():
                    company_score = 0.6
                
                # Общий скор
                total_score = max(name_score, email_score, company_score)
                
                if total_score > 0.3:  # Порог совпадения
                    matches.append({
                        'contact': contact,
                        'score': total_score,
                        'match_type': 'name' if name_score == total_score else 'email' if email_score == total_score else 'company'
                    })
            
            # Сортируем по релевантности
            matches.sort(key=lambda x: x['score'], reverse=True)
            
            if not matches:
                return {
                    'type': 'no_matches',
                    'found': False,
                    'suggestions': [contact.name for contact in all_contacts[:5]],
                    'message': f'Контакт "{query}" не найден'
                }
            
            # Если одно точное совпадение
            if len(matches) == 1 and matches[0]['score'] > 0.8:
                contact = matches[0]['contact']
                if contact.email:
                    return {
                        'type': 'contact_found',
                        'found': True,
                        'recipient_email': contact.email,
                        'recipient_name': contact.name,
                        'confidence': 'high',
                        'contact_id': contact.id
                    }
            
            # Несколько вариантов - нужно уточнение
            return {
                'type': 'multiple_matches',
                'found': False,
                'matches': matches[:5],  # Топ 5 совпадений
                'message': f'Найдено несколько контактов для "{query}"'
            }
            
        except Exception as e:
            return {
                'type': 'error',
                'found': False,
                'message': f'Ошибка поиска: {str(e)[:50]}...'
            }
    
    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """Простой алгоритм вычисления схожести строк"""
        if s1 == s2:
            return 1.0
        
        if s1 in s2 or s2 in s1:
            return 0.8
        
        # Проверяем общие слова
        words1 = set(s1.split())
        words2 = set(s2.split())
        
        if words1 & words2:  # Есть общие слова
            return len(words1 & words2) / len(words1 | words2)
        
        return 0.0
    
    async def _analyze_with_ai(self, user_input: str, user_id: int) -> Dict:
        """Анализ ввода с помощью AI"""
        try:
            # Получаем контакты для контекста
            contacts = await contacts_manager.get_user_contacts(user_id)
            contacts_context = ""
            
            if contacts:
                contacts_context = "Доступные контакты:\n"
                for contact in contacts[:10]:  # Топ 10 контактов
                    contacts_context += f"- {contact.name}"
                    if contact.email:
                        contacts_context += f" ({contact.email})"
                    if contact.company:
                        contacts_context += f" - {contact.company}"
                    contacts_context += "\n"
            
            prompt = f"""
Пользователь хочет отправить письмо и написал: "{user_input}"

{contacts_context}

Проанализируй запрос и определи:
1. Кому предположительно нужно отправить письмо
2. Есть ли упоминание конкретного контакта
3. Можно ли определить тему письма

Ответь в формате JSON:
{{
    "recipient_type": "contact_name|role_description|unclear",
    "recipient_info": "найденное имя или описание роли",
    "suggested_subject": "предполагаемая тема письма",
    "confidence": "high|medium|low",
    "clarification_needed": "что нужно уточнить у пользователя"
}}

Примеры:
- "письмо боссу о отпуске" → recipient_type: "role_description", recipient_info: "босс"
- "напиши Алексею" → recipient_type: "contact_name", recipient_info: "Алексей"
"""

            messages = [
                {"role": "system", "content": "Ты помощник по анализу намерений для отправки писем. Отвечай только в формате JSON."},
                {"role": "user", "content": prompt}
            ]
            
            ai_response = await openai_client.chat_completion(messages)
            
            # Парсим JSON ответ
            import json
            try:
                analysis = json.loads(ai_response)
                
                return {
                    'type': 'ai_analysis',
                    'found': False,
                    'analysis': analysis,
                    'message': 'AI анализ завершен'
                }
            except json.JSONDecodeError:
                return {
                    'type': 'ai_analysis_text',
                    'found': False,
                    'analysis_text': ai_response,
                    'message': 'AI дал текстовый ответ'
                }
                
        except Exception as e:
            return {
                'type': 'ai_error',
                'found': False,
                'message': f'Ошибка AI анализа: {str(e)[:50]}...'
            }


# Глобальный экземпляр
contact_finder = ContactFinder()