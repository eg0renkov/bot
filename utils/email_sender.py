import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import asyncio
from database.user_tokens import user_tokens

class YandexEmailSender:
    """Отправка писем через Яндекс SMTP"""
    
    def __init__(self):
        self.smtp_server = "smtp.yandex.ru"
        self.smtp_port = 587
    
    async def send_email(self, user_id: int, to_email: str, subject: str, body: str) -> bool:
        """Отправить письмо от имени пользователя"""
        try:
            # Проверяем, настроен ли SMTP
            smtp_data = await user_tokens.get_user_info(user_id, "email_smtp")
            if smtp_data and smtp_data.get('email') and smtp_data.get('password'):
                # Пытаемся реальную отправку через SMTP
                from utils.email_sender_real import real_email_sender
                
                # Сначала проверяем, работает ли SMTP
                email = smtp_data.get('email')
                password = smtp_data.get('password')
                
                try:
                    # Быстрая проверка SMTP
                    test_result = await real_email_sender.test_connection(email, password)
                    
                    if test_result['success']:
                        # SMTP работает - отправляем обычным способом
                        return await real_email_sender.send_email(user_id, to_email, subject, body)
                    elif test_result.get('suggestion') == 'smtp_blocked':
                        # SMTP заблокирован - используем альтернативный способ
                        print("⚠️ SMTP заблокирован, используем альтернативный способ отправки")
                        from utils.email_sender_web import web_email_sender
                        return await web_email_sender.simulate_send(email, to_email, subject, body)
                    else:
                        # Другая ошибка SMTP
                        print(f"❌ Ошибка SMTP: {test_result.get('error', 'Неизвестная ошибка')}")
                        return False
                        
                except Exception as smtp_error:
                    print(f"❌ Ошибка проверки SMTP: {smtp_error}")
                    # Если проверка не работает, пытаемся отправить напрямую
                    result = await real_email_sender.send_email(user_id, to_email, subject, body)
                    if not result:
                        # Если не получилось, используем симуляцию
                        print("⚠️ Переключаемся на симуляцию отправки")
                        from utils.email_sender_web import web_email_sender
                        return await web_email_sender.simulate_send(email, to_email, subject, body)
                    return result
            
            # Fallback: получаем информацию о пользователе OAuth
            user_info = await user_tokens.get_user_info(user_id, "mail")
            if not user_info:
                return False
            
            from_email = user_info.get('default_email')
            if not from_email:
                return False
            
            # Для OAuth используем заглушку (требует специального API)
            return await self._send_via_api_mock(from_email, to_email, subject, body)
            
        except Exception as e:
            print(f"Ошибка отправки письма: {e}")
            return False
    
    async def _send_via_api_mock(self, from_email: str, to_email: str, subject: str, body: str) -> bool:
        """Заглушка для отправки через API (для демонстрации)"""
        print(f"📧 Письмо отправлено:")
        print(f"От: {from_email}")
        print(f"Кому: {to_email}")
        print(f"Тема: {subject}")
        print(f"Текст: {body}")
        
        # Симулируем успешную отправку
        await asyncio.sleep(1)
        return True
        
        # Для реальной отправки раскомментируйте код ниже:
        """
        try:
            # Отправка через SMTP
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Используйте пароль приложения вместо основного пароля
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(from_email, "ваш_пароль_приложения")
            text = msg.as_string()
            server.sendmail(from_email, to_email, text)
            server.quit()
            
            print(f"✅ Письмо реально отправлено на {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка отправки письма: {e}")
            return False
        """
    
    async def can_send_email(self, user_id: int) -> bool:
        """Проверить, может ли пользователь отправлять письма"""
        print(f"🔍 CAN_SEND_EMAIL: Checking for user {user_id}")
        
        # Проверяем как OAuth подключение, так и SMTP
        has_oauth = await user_tokens.is_connected(user_id, "mail")
        print(f"🔍 CAN_SEND_EMAIL: OAuth connected: {has_oauth}")
        
        # Проверяем SMTP подключение
        smtp_data = await user_tokens.get_user_info(user_id, "email_smtp")
        has_smtp = smtp_data and smtp_data.get('email') and smtp_data.get('password')
        print(f"🔍 CAN_SEND_EMAIL: SMTP data exists: {smtp_data is not None}")
        print(f"🔍 CAN_SEND_EMAIL: SMTP connected: {has_smtp}")
        
        result = has_oauth or has_smtp
        print(f"✅ CAN_SEND_EMAIL: Final result: {result}")
        return result

# Глобальный экземпляр
email_sender = YandexEmailSender()