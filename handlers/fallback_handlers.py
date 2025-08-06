from aiogram import Router
from aiogram.types import CallbackQuery

router = Router()

from aiogram import F

# Перехватываем только callback'и, которые точно не должны обрабатываться
@router.callback_query(
    F.data.startswith("unknown_") | 
    F.data.startswith("legacy_") |
    F.data.startswith("temp_")
)
async def unhandled_callback(callback: CallbackQuery):
    """Обработчик определенных необработанных callback'ов"""
    print(f"Unhandled callback: {callback.data}")
    await callback.answer("🚧 Функция в разработке", show_alert=True)