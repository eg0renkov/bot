import html
from typing import Optional

def escape_html(text: Optional[str]) -> str:
    """
    Экранирует специальные HTML символы для безопасного отображения в Telegram
    
    Args:
        text: Текст для экранирования
        
    Returns:
        Экранированный текст
    """
    if not text:
        return ""
    
    # Используем стандартную функцию html.escape
    # quote=False означает, что кавычки не будут экранированы
    return html.escape(str(text), quote=False)


def escape_email(email: Optional[str]) -> str:
    """
    Экранирует email адрес для безопасного отображения в HTML
    Особенно важно для адресов типа no-reply@example.com
    
    Args:
        email: Email адрес
        
    Returns:
        Экранированный email
    """
    if not email:
        return ""
    
    # Экранируем email, особенно символ @
    return escape_html(email)


def truncate_and_escape(text: Optional[str], max_length: int = 50) -> str:
    """
    Обрезает и экранирует текст для безопасного отображения
    
    Args:
        text: Исходный текст
        max_length: Максимальная длина
        
    Returns:
        Обрезанный и экранированный текст
    """
    if not text:
        return ""
    
    text = str(text)
    if len(text) > max_length:
        text = text[:max_length-3] + "..."
    
    return escape_html(text)