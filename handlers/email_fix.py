"""
Исправления для обработки email команд - устранение всех возможных багов
"""
import re
from typing import Optional, Dict, Any

async def extract_email_info_fixed(text: str, user_name: str = None) -> Optional[Dict[str, Any]]:
    """
    Улучшенная функция извлечения информации о письме с защитой от всех багов
    """
    print(f"EXTRACT_EMAIL_INFO_FIXED: Starting with text: '{text}'")
    
    if not text or not text.strip():
        print("EXTRACT_EMAIL_INFO_FIXED: Empty text")
        return None
    
    text = text.strip()
    
    # Расширенные паттерны с лучшей обработкой
    patterns = [
        # НОВЫЕ ПАТТЕРНЫ ДЛЯ ИМЕН (БЕЗ EMAIL)
        r"напиш[иь].*письмо\s+([а-яёА-ЯЁa-zA-Z]+(?:у)?)\s+с\s+(.+)",
        r"отправ[ьи].*письмо\s+([а-яёА-ЯЁa-zA-Z]+(?:у)?)\s+с\s+(.+)",
        r"письмо\s+([а-яёА-ЯЁa-zA-Z]+(?:у)?)\s+с\s+(.+)",
        
        # Основные паттерны с "об" и "о" - ИСПРАВЛЕНЫ для лучшего захвата
        r"отправ[ьи].*письмо\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s+об?\s+(.+)",
        r"отправ[ьи]\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s+об?\s+(.+)",
        r"письмо\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s+об?\s+(.+)",
        
        # Паттерны с "напиши письмо"
        r"напиш[иь].*письмо\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s*[-–—]\s*об?\s+(.+)",
        r"напиш[иь].*письмо\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s+об?\s+(.+)",
        
        # Паттерны с "тема"
        r"отправ[ьи].*письмо.*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}).*тема[:\s]+(.+)",
        r"письмо.*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}).*тема[:\s]+(.+)",
        
        # Простые паттерны email + тема (fallback)
        r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s+(.+)",
    ]
    
    for i, pattern in enumerate(patterns):
        print(f"Testing pattern {i+1}: {pattern}")
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            print(f"Pattern {i+1} MATCHED!")
            recipient = match.group(1).strip()
            raw_subject = match.group(2).strip()
            
            # Проверяем, является ли получатель email-адресом или именем
            if _is_valid_email(recipient):
                # Это email-адрес
                email = recipient
                print(f"Found email address: {email}")
            else:
                # Это имя - нужно искать в контактах
                print(f"Found name: {recipient}, searching in contacts...")
                try:
                    email = await _find_email_by_name(recipient)
                    print(f"Search result for {recipient}: {email}")
                    if not email:
                        print(f"Email not found for name: {recipient}")
                        continue
                    print(f"Found email for {recipient}: {email}")
                except Exception as e:
                    print(f"Error searching for {recipient}: {e}")
                    continue
            
            # Валидация темы - не должна быть пустой или слишком короткой
            if not raw_subject or len(raw_subject.strip()) < 2:
                print(f"Invalid subject: '{raw_subject}'")
                continue
            
            # Используем AI форматирование темы письма
            subject = await format_email_subject_safe(raw_subject)
            
            # Ищем дополнительный текст после темы
            additional_text = _extract_additional_text(text, raw_subject)
            
            # Генерируем тело письма с защитой от пустоты
            body = _generate_email_body(subject, additional_text, user_name)
            
            result = {
                "email": email,
                "subject": subject,
                "body": body,
                "original_text": text
            }
            
            print(f"EXTRACT_EMAIL_INFO_FIXED: Success!")
            print(f"   Email: {email}")
            print(f"   Subject: {subject}")
            print(f"   Body length: {len(body)}")
            
            return result
    
    print(f"EXTRACT_EMAIL_INFO_FIXED: No patterns matched")
    return None

def _is_valid_email(email: str) -> bool:
    """Проверка валидности email"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email.strip()))

def _clean_subject(raw_subject: str) -> str:
    """Очистка и форматирование темы письма"""
    subject = raw_subject.strip()
    
    # Убираем лишние знаки в начале и конце
    subject = re.sub(r'^[.,;:\s\-–—]+', '', subject)
    subject = re.sub(r'[.,;:\s\-–—]+$', '', subject)
    
    # Убираем предлоги из начала
    subject = re.sub(r'^(об?|про|касательно|касающиеся?|относительно)\s+', '', subject, flags=re.IGNORECASE)
    
    # Делаем первую букву заглавной
    if subject:
        subject = subject[0].upper() + subject[1:] if len(subject) > 1 else subject.upper()
    
    return subject if subject else "Важное сообщение"

def _extract_additional_text(original_text: str, subject_part: str) -> str:
    """Извлечение дополнительного текста после темы"""
    try:
        # Ищем позицию темы в тексте
        subject_pos = original_text.lower().find(subject_part.lower())
        if subject_pos >= 0:
            subject_end = subject_pos + len(subject_part)
            remaining_text = original_text[subject_end:].strip()
            
            # Убираем знаки препинания в начале
            remaining_text = re.sub(r'^[.,;:\s\-–—]+', '', remaining_text).strip()
            
            # Фильтруем мусорный текст
            if remaining_text and len(remaining_text) > 5 and not _is_garbage_text(remaining_text):
                return remaining_text
    except Exception as e:
        print(f"Warning: Failed to extract additional text: {e}")
    
    return ""

def _is_garbage_text(text: str) -> bool:
    """Проверка является ли текст мусорным"""
    garbage_patterns = [
        r'^\s*[.,;:\-–—]+\s*$',  # Только знаки препинания
        r'^\s*\w{1,2}\s*$',      # Слишком короткие слова
        r'^(и|а|но|да|нет|ок|ok)$'  # Стоп-слова
    ]
    
    text_lower = text.lower().strip()
    for pattern in garbage_patterns:
        if re.match(pattern, text_lower):
            return True
    
    return False

def _generate_email_body(subject: str, additional_text: str, user_name: str = None) -> str:
    """Генерация тела письма с гарантированным непустым результатом"""
    
    # Если есть дополнительный текст, используем его как основу
    if additional_text and len(additional_text.strip()) > 10:
        body_parts = ["Добрый день!", "", additional_text]
    else:
        # Генерируем стандартное тело на основе темы
        body_parts = [
            "Добрый день!",
            "",
            f"Пишу вам по поводу {subject.lower()}.",
            ""
        ]
    
    # Добавляем подпись
    if user_name and user_name.strip():
        body_parts.extend(["С уважением,", user_name])
    else:
        body_parts.append("С уважением")
    
    # Собираем тело письма
    body = "\n".join(body_parts)
    
    # КРИТИЧЕСКИ ВАЖНО: Проверяем что тело не пустое
    if not body or len(body.strip()) < 10:
        # Аварийный fallback БЕЗ async вызова
        body = f"Добрый день!\n\nОбращаюсь к вам с вопросом.\n\nС уважением"
    
    return body

# Улучшенная функция для форматирования темы с AI
async def format_email_subject_safe(raw_subject: str) -> str:
    """Безопасное AI-форматирование темы письма с fallback"""
    subject = raw_subject.strip()
    
    if not subject:
        return "Важное сообщение"
    
    # Быстрые исправления для частых случаев
    subject = _clean_subject(subject)
    
    # Если тема уже хорошая, не трогаем
    if len(subject.split()) <= 3 and not any(word in subject.lower() for word in ['об', 'про', 'касательно']):
        return subject
    
    # Попытка AI улучшения (с fallback)
    try:
        from utils.openai_client import openai_client
        
        prompt = f"""Преобразуй тему письма в правильную форму:

ПРАВИЛА:
1. Убери предлоги: об, о, про, касательно, по поводу
2. Поставь все слова в именительный падеж (кто? что?)
3. Первая буква заглавная, остальные строчные
4. Максимум 6-8 слов
5. Никаких лишних слов

ПРИМЕРЫ ПРЕОБРАЗОВАНИЙ:
"об успешной сдаче контракта" → "Успешная сдача контракта"
"о важной встрече" → "Важная встреча"
"про новый проект" → "Новый проект"
"касательно отчета" → "Отчет"
"по поводу работы" → "Работа"
"об успешной сдаче проекта" → "Успешная сдача проекта"

Исходная тема: "{subject}"
Преобразованная тема:"""

        messages = [{"role": "user", "content": prompt}]
        ai_response = await openai_client.chat_completion(messages, temperature=0.1)
        
        if ai_response and ai_response.strip():
            formatted = ai_response.strip().strip('"').strip("'")
            # Проверяем что ответ разумный
            if 2 <= len(formatted) <= len(subject) * 2:
                return formatted
    
    except Exception as e:
        print(f"AI форматирование темы не удалось: {e}")
    
    # Fallback - возвращаем очищенную тему
    return subject

async def _find_email_by_name(name: str) -> str:
    """Поиск email-адреса по имени в контактах"""
    try:
        # ВРЕМЕННАЯ ЗАГЛУШКА - добавим простой список контактов
        # TODO: заменить на реальную базу данных контактов
        test_contacts = {
            'леонид': 'egrn0103@yandex.ru',
            'леониду': 'egrn0103@yandex.ru',
            'leonid': 'egrn0103@yandex.ru',
        }
        
        name_lower = name.lower().strip()
        print(f"Searching for name: '{name_lower}' in contacts: {list(test_contacts.keys())}")
        
        if name_lower in test_contacts:
            email = test_contacts[name_lower]
            print(f"Found email in test contacts: {email}")
            return email
        
        # Поиск частичного совпадения
        for contact_name, email in test_contacts.items():
            if contact_name in name_lower or name_lower in contact_name:
                print(f"Found partial match: {contact_name} -> {email}")
                return email
                
        print(f"No contacts found for: {name_lower}")
        return None
                    
    except Exception as e:
        print(f"Error searching contacts: {e}")
        return None

async def _generate_ai_email_body(subject: str, user_name: str = None) -> str:
    """Генерация грамматически правильного тела письма с помощью AI"""
    try:
        from utils.openai_client import openai_client
        
        signature = f"С уважением,\n{user_name}" if user_name else "С уважением"
        
        prompt = f"""Создай краткое и вежливое деловое письмо на русском языке по теме: "{subject}"

ТРЕБОВАНИЯ:
1. Начни с приветствия "Добрый день!"
2. Используй правильную грамматику и падежи
3. Письмо должно быть вежливым и деловым
4. Длина 2-4 предложения
5. НЕ добавляй подпись - она будет добавлена отдельно

Пример структуры:
Добрый день!

[1-2 предложения по теме с правильной грамматикой]

[Опционально: просьба или предложение]"""

        messages = [
            {"role": "system", "content": "Ты - помощник для создания деловых писем. Создавай грамматически правильные и вежливые письма."},
            {"role": "user", "content": prompt}
        ]
        
        ai_body = await openai_client.chat_completion(messages)
        
        if ai_body and len(ai_body.strip()) > 10:
            return f"{ai_body.strip()}\n\n{signature}"
            
    except Exception as e:
        print(f"AI generation failed: {e}")
    
    return None