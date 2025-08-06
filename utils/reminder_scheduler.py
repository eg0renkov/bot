"""
Планировщик для проверки и отправки напоминаний
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional
from aiogram import Bot
from database.reminders import ReminderDB

logger = logging.getLogger(__name__)

class ReminderScheduler:
    """Класс для управления расписанием напоминаний"""
    
    def __init__(self, bot: Bot):
        """
        Инициализация планировщика
        
        Args:
            bot: Экземпляр бота для отправки сообщений
        """
        self.bot = bot
        self.reminder_db = ReminderDB()
        self.is_running = False
        self.check_interval = 60  # Проверка каждую минуту
        
    async def start(self):
        """Запуск планировщика"""
        if self.is_running:
            logger.warning("Планировщик напоминаний уже запущен")
            return
        
        self.is_running = True
        logger.info("Планировщик напоминаний запущен")
        
        # Запускаем фоновую задачу
        asyncio.create_task(self._run_scheduler())
    
    async def stop(self):
        """Остановка планировщика"""
        self.is_running = False
        logger.info("Планировщик напоминаний остановлен")
    
    async def _run_scheduler(self):
        """Основной цикл планировщика"""
        while self.is_running:
            try:
                # Проверяем напоминания
                await self._check_reminders()
                
                # Ждем до следующей проверки
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Ошибка в планировщике напоминаний: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _check_reminders(self):
        """Проверка и отправка напоминаний"""
        try:
            # Получаем активные напоминания
            reminders = await self.reminder_db.get_active_reminders(time_window_minutes=5)
            
            if not reminders:
                return
            
            logger.info(f"Найдено {len(reminders)} активных напоминаний")
            
            # Отправляем каждое напоминание
            for reminder in reminders:
                await self._send_reminder(reminder)
                
        except Exception as e:
            logger.error(f"Ошибка проверки напоминаний: {e}")
    
    async def _send_reminder(self, reminder: dict):
        """
        Отправка напоминания пользователю
        
        Args:
            reminder: Словарь с данными напоминания
        """
        try:
            user_id = reminder['user_id']
            title = reminder['title']
            description = reminder.get('description', '')
            
            # Формируем текст напоминания
            text = f"⏰ <b>Напоминание!</b>\n\n"
            text += f"📌 <b>{title}</b>\n"
            
            if description:
                text += f"\n📝 {description}\n"
            
            # Добавляем информацию о повторении
            if reminder.get('repeat_type') and reminder['repeat_type'] != 'none':
                repeat_types = {
                    'daily': 'Ежедневное напоминание',
                    'weekly': 'Еженедельное напоминание',
                    'monthly': 'Ежемесячное напоминание',
                    'yearly': 'Ежегодное напоминание'
                }
                text += f"\n🔁 <i>{repeat_types.get(reminder['repeat_type'], '')}</i>"
            
            # Создаем клавиатуру с действиями
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            from aiogram.types import InlineKeyboardButton
            
            builder = InlineKeyboardBuilder()
            builder.add(
                InlineKeyboardButton(
                    text="✅ Выполнено",
                    callback_data=f"reminder_complete_{reminder['id']}"
                ),
                InlineKeyboardButton(
                    text="⏱️ Отложить на 10 мин",
                    callback_data=f"reminder_snooze_{reminder['id']}_10"
                )
            )
            builder.add(
                InlineKeyboardButton(
                    text="📋 Все напоминания",
                    callback_data="reminder_list"
                )
            )
            builder.adjust(2, 1)
            
            # Отправляем напоминание
            await self.bot.send_message(
                chat_id=user_id,
                text=text,
                parse_mode="HTML",
                reply_markup=builder.as_markup()
            )
            
            # Отмечаем напоминание как отправленное
            await self.reminder_db.mark_reminder_sent(reminder['id'])
            
            logger.info(f"Напоминание {reminder['id']} отправлено пользователю {user_id}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки напоминания {reminder.get('id')}: {e}")
    
    async def send_test_reminder(self, user_id: int):
        """
        Отправка тестового напоминания
        
        Args:
            user_id: ID пользователя
        """
        test_reminder = {
            'id': 0,
            'user_id': user_id,
            'title': 'Тестовое напоминание',
            'description': 'Это тестовое напоминание для проверки работы системы',
            'repeat_type': 'none'
        }
        
        await self._send_reminder(test_reminder)