import smtplib
import ssl
import socket
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from typing import Dict, List, Optional, Tuple
import asyncio
import re
from datetime import datetime
from database.user_tokens import user_tokens

class RealEmailSender:
    """Реальная отправка и получение писем через SMTP/IMAP"""
    
    def __init__(self):
        self.smtp_server = "smtp.yandex.ru"
        self.smtp_port = 587
        self.imap_server = "imap.yandex.ru"
        self.imap_port = 993
    
    async def test_connection(self, email: str, password: str) -> Dict:
        """Тестировать подключение к почтовому серверу"""
        try:
            # Сначала проверяем сетевую связность
            loop = asyncio.get_event_loop()
            
            # Тестируем IMAP (часто работает даже если SMTP заблокирован)
            imap_result = await loop.run_in_executor(None, self._test_imap, email, password)
            
            # Тестируем SMTP
            smtp_result = await loop.run_in_executor(None, self._test_smtp, email, password)
            
            # Если SMTP не работает, но IMAP работает - это частичная работоспособность
            if imap_result['success'] and not smtp_result['success']:
                # Проверяем, связано ли это с блокировкой портов
                if 'timeout' in smtp_result.get('error', '').lower() or '10060' in smtp_result.get('error', ''):
                    return {
                        'success': False,
                        'smtp': smtp_result,
                        'imap': imap_result,
                        'message': 'SMTP заблокирован провайдером',
                        'error': 'SMTP порты заблокированы. Получение писем работает, отправка - нет.',
                        'suggestion': 'smtp_blocked'
                    }
            
            return {
                'success': smtp_result['success'] and imap_result['success'],
                'smtp': smtp_result,
                'imap': imap_result,
                'message': 'Подключение успешно' if smtp_result['success'] and imap_result['success'] else 'Ошибка подключения'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Ошибка тестирования: {str(e)}',
                'message': 'Техническая ошибка'
            }
    
    def _test_smtp(self, email: str, password: str) -> Dict:
        """Тестировать SMTP подключение"""
        server = None
        try:
            print(f"DEBUG: Тестируем SMTP для {email}")
            print(f"DEBUG: Подключаемся к {self.smtp_server}:{self.smtp_port}")
            
            # Создаем подключение с явным указанием параметров для Yandex
            server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=45)
            server.set_debuglevel(0)  # Отключаем debug для production
            
            print("DEBUG: Устанавливаем STARTTLS...")
            # Включаем TLS с принудительной проверкой сертификата
            context = ssl.create_default_context()
            server.starttls(context=context)
            
            print("DEBUG: Пытаемся авторизоваться...")
            # Авторизация
            server.login(email, password)
            
            print("DEBUG: SMTP подключение успешно!")
            server.quit()
            
            return {
                'success': True,
                'message': 'SMTP подключение успешно'
            }
            
        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"Неверный email или пароль приложения: {str(e)}"
            print(f"DEBUG: SMTP Auth Error: {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'message': 'Ошибка аутентификации'
            }
        except smtplib.SMTPConnectError as e:
            error_msg = f"Не удалось подключиться к серверу: {str(e)}"
            print(f"DEBUG: SMTP Connect Error: {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'message': 'Ошибка подключения к серверу'
            }
        except smtplib.SMTPServerDisconnected as e:
            error_msg = f"Сервер разорвал соединение: {str(e)}"
            print(f"DEBUG: SMTP Disconnect Error: {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'message': 'Соединение разорвано'
            }
        except smtplib.SMTPException as e:
            error_msg = f'SMTP ошибка: {str(e)}'
            print(f"DEBUG: SMTP Exception: {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'message': 'Ошибка SMTP сервера'
            }
        except socket.timeout:
            error_msg = 'Таймаут подключения к SMTP серверу'
            print(f"DEBUG: SMTP Timeout: {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'message': 'Таймаут подключения'
            }
        except socket.gaierror as e:
            error_msg = f'Ошибка DNS: {str(e)}'
            print(f"DEBUG: DNS Error: {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'message': 'Проблема с DNS'
            }
        except ConnectionRefusedError:
            error_msg = 'Подключение отклонено (порт заблокирован)'
            print(f"DEBUG: Connection Refused: {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'message': 'Порт заблокирован провайдером'
            }
        except Exception as e:
            error_msg = f'Неизвестная ошибка: {str(e)}'
            print(f"DEBUG: Unknown Error: {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'message': 'Техническая ошибка'
            }
        finally:
            # Закрываем соединение в любом случае
            try:
                if server:
                    server.quit()
            except:
                pass
    
    def _test_imap(self, email: str, password: str) -> Dict:
        """Тестировать IMAP подключение"""
        try:
            # Устанавливаем timeout для IMAP
            import socket
            socket.setdefaulttimeout(30)
            
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(email, password)
            mail.logout()
            
            return {
                'success': True,
                'message': 'IMAP подключение успешно'
            }
            
        except imaplib.IMAP4.error as e:
            return {
                'success': False,
                'error': f'IMAP ошибка: {str(e)}',
                'message': 'Ошибка IMAP сервера'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Ошибка подключения: {str(e)}',
                'message': 'Техническая ошибка'
            }
    
    async def send_email(self, user_id: int, to_email: str, subject: str, body: str) -> bool:
        """Отправить письмо"""
        try:
            # Получаем настройки пользователя
            email_data = await user_tokens.get_user_info(user_id, "email_smtp")
            if not email_data:
                print("❌ Email не настроен для пользователя")
                return False
            
            from_email = email_data.get('email')
            password = email_data.get('password')
            
            if not from_email or not password:
                print("❌ Нет данных для подключения")
                return False
            
            # Отправляем письмо в отдельном потоке
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                self._send_email_sync, 
                from_email, password, to_email, subject, body
            )
            
            if result:
                print(f"✅ Письмо отправлено: {from_email} -> {to_email}")
                print(f"📝 Тема: {subject}")
            
            return result
            
        except Exception as e:
            print(f"❌ Ошибка отправки письма: {e}")
            return False
    
    def _send_email_sync(self, from_email: str, password: str, to_email: str, subject: str, body: str) -> bool:
        """Синхронная отправка письма"""
        try:
            # Создаем сообщение
            msg = MIMEMultipart('alternative')
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Добавляем текст (и HTML если нужно)
            text_part = MIMEText(body, 'plain', 'utf-8')
            msg.attach(text_part)
            
            # HTML версия для красивого отображения
            html_body = body.replace('\n', '<br>')
            html_part = MIMEText(f'<div style="font-family: Arial; font-size: 14px;">{html_body}</div>', 'html', 'utf-8')
            msg.attach(html_part)
            
            # Подключаемся и отправляем
            server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30)
            server.starttls()
            server.login(from_email, password)
            
            text = msg.as_string()
            server.sendmail(from_email, to_email, text)
            server.quit()
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка синхронной отправки: {e}")
            return False
    
    async def get_inbox_emails(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Получить входящие письма"""
        try:
            # Получаем настройки пользователя
            email_data = await user_tokens.get_user_info(user_id, "email_smtp")
            if not email_data:
                return []
            
            email_addr = email_data.get('email')
            password = email_data.get('password')
            
            if not email_addr or not password:
                return []
            
            # Получаем письма в отдельном потоке
            loop = asyncio.get_event_loop()
            emails = await loop.run_in_executor(
                None, 
                self._get_emails_sync, 
                email_addr, password, limit
            )
            
            return emails
            
        except Exception as e:
            print(f"❌ Ошибка получения писем: {e}")
            return []
    
    def _get_emails_sync(self, email_addr: str, password: str, limit: int) -> List[Dict]:
        """Синхронное получение писем"""
        try:
            # Подключаемся к IMAP с timeout
            import socket
            socket.setdefaulttimeout(30)
            
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(email_addr, password)
            mail.select('INBOX')
            
            # Ищем письма
            status, messages = mail.search(None, 'ALL')
            if status != 'OK':
                return []
            
            email_ids = messages[0].split()
            emails = []
            
            # Берем последние письма
            for email_id in email_ids[-limit:]:
                try:
                    # Получаем письмо
                    status, msg_data = mail.fetch(email_id, '(RFC822)')
                    if status != 'OK':
                        continue
                    
                    # Парсим письмо
                    msg = email.message_from_bytes(msg_data[0][1])
                    
                    # Извлекаем информацию
                    subject = self._decode_header(msg.get('Subject', ''))
                    sender = self._decode_header(msg.get('From', ''))
                    date = msg.get('Date', '')
                    
                    # Получаем текст письма
                    body = self._get_email_body(msg)
                    
                    emails.append({
                        'id': email_id.decode(),
                        'subject': subject,
                        'sender': sender,
                        'date': date,
                        'body': body[:500] + '...' if len(body) > 500 else body,
                        'full_body': body
                    })
                    
                except Exception as e:
                    print(f"Ошибка обработки письма {email_id}: {e}")
                    continue
            
            mail.logout()
            
            # Возвращаем в обратном порядке (новые сначала)
            return list(reversed(emails))
            
        except Exception as e:
            print(f"❌ Ошибка синхронного получения писем: {e}")
            return []
    
    def _decode_header(self, header: str) -> str:
        """Декодировать заголовок письма"""
        if not header:
            return ''
        
        try:
            decoded_parts = decode_header(header)
            result = ''
            
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        result += part.decode(encoding)
                    else:
                        result += part.decode('utf-8', errors='ignore')
                else:
                    result += part
            
            return result
            
        except Exception:
            return str(header)
    
    def _get_email_body(self, msg) -> str:
        """Извлечь текст письма"""
        try:
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    
                    if content_type == "text/plain" and "attachment" not in content_disposition:
                        body = part.get_payload(decode=True)
                        if body:
                            charset = part.get_content_charset() or 'utf-8'
                            return body.decode(charset, errors='ignore')
            else:
                body = msg.get_payload(decode=True)
                if body:
                    charset = msg.get_content_charset() or 'utf-8'
                    return body.decode(charset, errors='ignore')
            
            return "Не удалось извлечь текст письма"
            
        except Exception as e:
            return f"Ошибка извлечения текста: {str(e)}"
    
    async def search_emails(self, user_id: int, query: str, limit: int = 20) -> List[Dict]:
        """Поиск писем по содержимому"""
        try:
            # Получаем все письма
            all_emails = await self.get_inbox_emails(user_id, limit=50)
            
            # Фильтруем по запросу
            filtered_emails = []
            query_lower = query.lower()
            
            for email_data in all_emails:
                # Ищем в теме, отправителе и тексте
                if (query_lower in email_data.get('subject', '').lower() or
                    query_lower in email_data.get('sender', '').lower() or
                    query_lower in email_data.get('full_body', '').lower()):
                    
                    filtered_emails.append(email_data)
                
                if len(filtered_emails) >= limit:
                    break
            
            return filtered_emails
            
        except Exception as e:
            print(f"❌ Ошибка поиска писем: {e}")
            return []
    
    async def can_send_email(self, user_id: int) -> bool:
        """Проверить, может ли пользователь отправлять письма"""
        try:
            email_data = await user_tokens.get_user_info(user_id, "email_smtp")
            return email_data is not None and email_data.get('email') and email_data.get('password')
        except:
            return False

# Глобальный экземпляр
real_email_sender = RealEmailSender()