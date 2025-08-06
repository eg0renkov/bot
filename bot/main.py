import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config.settings import settings
from handlers import messages, vector_commands, menu_handlers, menu_handlers_ai, yandex_integration, quick_actions, drafts_handlers, email_setup, contacts, fallback_handlers, reminders, auth
from utils.reminder_scheduler import ReminderScheduler
from middleware.auth_middleware import AuthMiddleware

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """Основная функция запуска бота"""
    try:
        # Проверяем настройки
        settings.validate()
        logger.info("Настройки проверены успешно")
        
        # Создаем бота и диспетчер
        bot = Bot(
            token=settings.TELEGRAM_BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        
        dp = Dispatcher()
        
        # Регистрируем middleware авторизации
        dp.message.middleware(AuthMiddleware())
        dp.callback_query.middleware(AuthMiddleware())
        logger.info("Middleware авторизации подключен")
        
        # Регистрируем роутеры (порядок важен!)
        dp.include_router(auth.router)  # Авторизация - ПЕРВОЙ!
        dp.include_router(menu_handlers.router)
        dp.include_router(menu_handlers_ai.router)
        dp.include_router(reminders.router)  # Добавляем обработчик напоминаний
        dp.include_router(contacts.router)
        dp.include_router(email_setup.router)
        dp.include_router(yandex_integration.router)
        dp.include_router(drafts_handlers.router)
        dp.include_router(vector_commands.router)
        dp.include_router(quick_actions.router)
        dp.include_router(messages.router)
        dp.include_router(fallback_handlers.router)  # Последним!
        
        # Запускаем планировщик напоминаний
        reminder_scheduler = ReminderScheduler(bot)
        await reminder_scheduler.start()
        logger.info("Планировщик напоминаний запущен")
        
        # Удаляем webhook и запускаем polling
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Бот запущен и готов к работе!")
        
        try:
            await dp.start_polling(bot)
        finally:
            # Останавливаем планировщик при завершении
            await reminder_scheduler.stop()
        
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)