from typing import List, Dict, Optional
from utils.openai_client import openai_client


class EmailAnalyzer:
    """Анализатор писем с помощью AI"""
    
    async def analyze_emails_summary(self, emails: List[Dict], user_name: str = "Пользователь") -> str:
        """
        Анализирует список писем и создает краткое саммари
        
        Args:
            emails: Список писем с полями sender, subject, body, date
            user_name: Имя пользователя для персонализации
            
        Returns:
            Краткое саммари писем
        """
        if not emails:
            return "📭 Нет писем для анализа"
        
        # Подготавливаем данные писем для анализа
        emails_text = self._prepare_emails_for_analysis(emails)
        
        # Создаем промпт для AI
        analysis_prompt = f"""
Проанализируй последние входящие письма пользователя {user_name} и создай краткое саммари.

ПИСЬМА:
{emails_text}

ЗАДАЧА:
Создай краткое саммари (максимум 200 слов) с такой структурой:

📊 **КРАТКИЙ АНАЛИЗ ВХОДЯЩИХ**

🔢 **Общая статистика:**
- Количество писем
- Период (от самого старого до самого нового)

📈 **Основные темы:**
- Перечисли 2-3 основные темы/категории писем

👥 **Активные отправители:**
- Назови самых активных отправителей

⚡ **Важные моменты:**
- Выдели самые важные или срочные письма
- Укажи на что стоит обратить внимание

💡 **Рекомендации:**
- Дай 1-2 совета по работе с этими письмами

Отвечай на русском языке, будь лаконичен и полезен.
"""

        try:
            # Отправляем запрос к AI
            messages = [
                {"role": "system", "content": "Ты эксперт по анализу деловой переписки. Анализируешь письма и даешь полезные выводы."},
                {"role": "user", "content": analysis_prompt}
            ]
            
            analysis = await openai_client.chat_completion(messages)
            return analysis
            
        except Exception as e:
            return f"❌ Ошибка анализа: {str(e)[:100]}..."
    
    def _prepare_emails_for_analysis(self, emails: List[Dict]) -> str:
        """Подготавливает письма для анализа AI"""
        emails_text = ""
        
        for i, email in enumerate(emails, 1):
            sender = email.get('sender', 'Неизвестный отправитель')
            subject = email.get('subject', 'Без темы')
            body = email.get('body', email.get('preview', ''))
            date = email.get('date', '')
            
            # Обрезаем тело письма для экономии токенов
            if body and len(body) > 300:
                body = body[:300] + "..."
            
            emails_text += f"""
ПИСЬМО {i}:
От: {sender}
Тема: {subject}
Дата: {date}
Содержание: {body or 'Содержимое недоступно'}

---
"""
        
        return emails_text
    
    async def get_email_insights(self, emails: List[Dict]) -> Dict:
        """
        Получает дополнительную аналитику по письмам
        
        Returns:
            Dict с инсайтами: urgent_count, spam_likelihood, sentiment, etc.
        """
        if not emails:
            return {
                'urgent_count': 0,
                'spam_likelihood': 'low',
                'sentiment': 'neutral',
                'total_emails': 0
            }
        
        urgent_keywords = ['срочно', 'важно', 'urgent', 'asap', 'немедленно', 'критично']
        spam_keywords = ['скидка', 'бесплатно', 'выигрыш', 'акция', 'промо']
        
        urgent_count = 0
        spam_count = 0
        
        for email in emails:
            subject = email.get('subject', '').lower()
            body = email.get('body', '').lower()
            content = subject + ' ' + body
            
            # Подсчет срочных писем
            if any(keyword in content for keyword in urgent_keywords):
                urgent_count += 1
            
            # Подсчет потенциального спама
            if any(keyword in content for keyword in spam_keywords):
                spam_count += 1
        
        # Определяем уровень спама
        spam_ratio = spam_count / len(emails) if emails else 0
        if spam_ratio > 0.3:
            spam_likelihood = 'high'
        elif spam_ratio > 0.1:
            spam_likelihood = 'medium'
        else:
            spam_likelihood = 'low'
        
        return {
            'urgent_count': urgent_count,
            'spam_likelihood': spam_likelihood,
            'spam_count': spam_count,
            'total_emails': len(emails),
            'unique_senders': len(set(email.get('sender', '') for email in emails))
        }


# Глобальный экземпляр
email_analyzer = EmailAnalyzer()