from utils.openai_client import openai_client
from typing import Dict, Tuple

class EmailImprover:
    """AI улучшение и генерация писем"""
    
    def __init__(self):
        self.improvement_prompt = """Улучши письмо, соблюдая СТРОГИЕ правила:

ИСПРАВЛЯЙ ТОЛЬКО:
- Грамматические ошибки
- Пунктуацию  
- Орфографические ошибки

СТРОГО ЗАПРЕЩЕНО:
- Добавлять новые обращения ("Добрый день", "Уважаемый", и т.д.)
- Изменять существующие обращения
- Добавлять имена, должности, контакты
- Менять структуру письма
- Добавлять новые предложения или абзацы
- Изменять смысл текста

ВАЖНО: Если в письме уже есть обращение "Добрый день!" - оставь его ТОЧНО как есть.

Верни ТОЛЬКО исправленный текст с теми же обращениями и структурой."""

        self.generation_prompt = """Ты профессиональный помощник по написанию деловых писем.
Твоя задача - создать качественное письмо на основе темы.

ПРАВИЛА СОЗДАНИЯ:
1. Создай структурированное и профессиональное письмо
2. Используй корректные обращения и формулы вежливости
3. Делай письмо содержательным и по существу
4. Добавь подходящее вступление и заключение
5. Используй деловой стиль письма
6. Письмо должно быть емким, но информативным
7. НЕ добавляй шаблонные поля типа [Ваше Имя], [Ваша Должность], [Контактная информация]
8. Используй простую подпись "С уважением" без дополнительных полей

ФОРМАТ ОТВЕТА:
Верни только текст готового письма без дополнительных комментариев."""
    
    async def improve_email(self, subject: str, body: str) -> Tuple[str, str]:
        """Улучшить существующее письмо"""
        try:
            # Улучшаем тему письма
            improved_subject = await self._improve_subject(subject)
            
            # Улучшаем текст письма
            improved_body = await self._improve_body(subject, body)
            
            return improved_subject, improved_body
            
        except Exception as e:
            print(f"Ошибка улучшения письма: {e}")
            return subject, body
    
    async def generate_email_from_topic(self, subject: str) -> str:
        """Сгенерировать письмо по теме"""
        try:
            messages = [
                {"role": "system", "content": self.generation_prompt},
                {"role": "user", "content": f"Создай письмо на тему: {subject}"}
            ]
            
            generated_body = await openai_client.chat_completion(messages)
            return generated_body
            
        except Exception as e:
            print(f"Ошибка генерации письма: {e}")
            return f"Письмо на тему: {subject}\n\nУважаемый получатель,\n\nПишу вам по поводу {subject.lower()}.\n\nС уважением"
    
    async def _improve_subject(self, subject: str) -> str:
        """Улучшить тему письма"""
        if len(subject) > 50 or self._is_well_formatted(subject):
            return subject
        
        try:
            messages = [
                {"role": "system", "content": "Улучши тему письма, сделав её более профессиональной и информативной. Верни только улучшенную тему без кавычек и дополнительного текста."},
                {"role": "user", "content": f"Тема: {subject}"}
            ]
            
            improved = await openai_client.chat_completion(messages)
            return improved.strip('"\'')
            
        except:
            return subject
    
    async def _improve_body(self, subject: str, body: str) -> str:
        """Улучшить текст письма"""
        try:
            messages = [
                {"role": "system", "content": self.improvement_prompt},
                {"role": "user", "content": f"Тема письма: {subject}\n\nТекст для улучшения:\n{body}"}
            ]
            
            improved = await openai_client.chat_completion(messages)
            return improved
            
        except:
            return body
    
    def _is_well_formatted(self, text: str) -> bool:
        """Проверить, хорошо ли отформатирован текст"""
        # Простая проверка на наличие заглавных букв и знаков препинания
        has_capitals = any(c.isupper() for c in text)
        has_punctuation = any(c in '.,!?;:' for c in text)
        return has_capitals and has_punctuation
    
    async def auto_improve_email_if_needed(self, subject: str, body: str) -> Tuple[str, str]:
        """Автоматически улучшить письмо если оно нуждается в улучшении"""
        needs_improvement = (
            len(body) < 50 or  # Очень короткое
            not self._is_well_formatted(body) or  # Плохо отформатировано
            body.count('.') == 0 or  # Нет точек
            body.islower() or  # Только строчные буквы
            len(body.split()) < 5  # Меньше 5 слов
        )
        
        if needs_improvement:
            return await self.improve_email(subject, body)
        
        return subject, body

# Глобальный экземпляр
email_improver = EmailImprover()