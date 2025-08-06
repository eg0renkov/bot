from aiogram import Router, F
from aiogram.types import CallbackQuery
from utils.openai_client import openai_client
from database.vector_memory import vector_memory
import os

router = Router()

@router.callback_query(F.data == "quick_voice")
async def quick_voice_handler(callback: CallbackQuery):
    """Озвучить последний ответ"""
    try:
        # Получаем текст из сообщения, очищаем от HTML тегов и эмодзи
        message_text = callback.message.text or callback.message.caption or ""
        
        # Убираем HTML теги и служебные символы
        import re
        clean_text = re.sub(r'<[^>]+>', '', message_text)
        clean_text = re.sub(r'[🤖📝💭✨🎯📊🔍💡⚡🚀🎨🌟💫🎭🎪🎨🎯]', '', clean_text)
        clean_text = clean_text.replace('Мой ответ:', '').replace('Ваше сообщение:', '').strip()
        
        if not clean_text or len(clean_text) < 10:
            await callback.answer("❌ Недостаточно текста для озвучивания", show_alert=True)
            return
        
        if len(clean_text) > 800:
            clean_text = clean_text[:800] + "..."
        
        await callback.answer("🎤 Генерирую голосовой ответ...")
        
        # Генерируем голосовой ответ
        voice_response = await openai_client.text_to_speech(clean_text)
        
        if voice_response:
            # Сохраняем во временный файл
            voice_file_path = f"temp_voice_{callback.from_user.id}.mp3"
            with open(voice_file_path, 'wb') as f:
                f.write(voice_response)
            
            # Отправляем голосовое сообщение
            from aiogram.types import FSInputFile
            voice_file = FSInputFile(voice_file_path)
            await callback.message.answer_voice(voice_file, caption="🎤 Озвученный ответ")
            
            # Удаляем временный файл
            if os.path.exists(voice_file_path):
                os.remove(voice_file_path)
        else:
            await callback.message.answer("❌ Не удалось создать голосовой ответ. Возможно, TTS не настроен.")
            
    except Exception as e:
        print(f"Ошибка озвучивания: {e}")
        await callback.answer("❌ Ошибка при озвучивании", show_alert=True)

@router.callback_query(F.data == "quick_save")
async def quick_save_handler(callback: CallbackQuery):
    """Сохранить ответ в знания"""
    try:
        message_text = callback.message.text or callback.message.caption or ""
        user_id = callback.from_user.id
        
        if not message_text or len(message_text.strip()) < 10:
            await callback.answer("❌ Недостаточно текста для сохранения", show_alert=True)
            return
        
        # Очищаем текст от служебных символов
        import re
        clean_text = re.sub(r'<[^>]+>', '', message_text)
        clean_text = clean_text.replace('Мой ответ:', '').replace('Ваше сообщение:', '').strip()
        
        if vector_memory:
            # Сохраняем в векторную память
            await vector_memory.save_to_knowledge_base(
                user_id, 
                "Важный ответ AI", 
                clean_text, 
                importance=2.0
            )
            await callback.answer("✅ Ответ сохранен в векторную память!")
        else:
            # Альтернативное сохранение в файл
            import json
            import os
            from datetime import datetime
            
            # Создаем директорию если её нет
            save_dir = f"data/saved_responses"
            os.makedirs(save_dir, exist_ok=True)
            
            # Сохраняем в файл
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{save_dir}/user_{user_id}_{timestamp}.json"
            
            save_data = {
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "content": clean_text,
                "type": "ai_response"
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            await callback.answer("✅ Ответ сохранен в файл!")
            
    except Exception as e:
        print(f"Ошибка сохранения: {e}")
        await callback.answer("❌ Ошибка при сохранении", show_alert=True)

@router.callback_query(F.data == "quick_retry")
async def quick_retry_handler(callback: CallbackQuery):
    """Переспросить AI"""
    try:
        # Отправляем подсказку пользователю
        await callback.message.answer(
            "🔄 <b>Переспросить AI</b>\n\n"
            "💡 <b>Способы получить новый ответ:</b>\n\n"
            "1️⃣ <b>Отправьте тот же вопрос заново</b>\n"
            "2️⃣ <b>Уточните запрос:</b>\n"
            "   • \"Объясни по-другому\"\n"
            "   • \"Дай другой вариант\"\n"
            "   • \"Перефразируй ответ\"\n\n"
            "3️⃣ <b>Задайте более конкретный вопрос</b>\n\n"
            "🤖 Я дам новый ответ!",
            parse_mode="HTML"
        )
        await callback.answer("Жду ваш новый вопрос!")
    except Exception as e:
        print(f"Ошибка retry: {e}")
        await callback.answer("🔄 Отправьте сообщение заново для нового ответа")

@router.callback_query(F.data == "quick_more")
async def quick_more_handler(callback: CallbackQuery):
    """Запросить подробности"""
    try:
        # Показываем подробное меню действий
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        from aiogram.types import InlineKeyboardButton
        
        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(text="📚 Расскажи подробнее", callback_data="more_detailed"),
            InlineKeyboardButton(text="💡 Приведи примеры", callback_data="more_examples")
        )
        builder.add(
            InlineKeyboardButton(text="🎯 Объясни простыми словами", callback_data="more_simple"),
            InlineKeyboardButton(text="🔀 Покажи альтернативы", callback_data="more_alternatives")
        )
        builder.add(
            InlineKeyboardButton(text="📖 Дай ссылки на источники", callback_data="more_sources"),
            InlineKeyboardButton(text="🧩 Разбери по шагам", callback_data="more_steps")
        )
        builder.adjust(2, 2, 2)
        
        await callback.message.answer(
            "➕ <b>Что именно вас интересует?</b>\n\n"
            "🎯 Выберите, как углубить ответ:",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        await callback.answer()
    except Exception as e:
        print(f"Ошибка more: {e}")
        await callback.answer("➕ Напишите что хотите узнать подробнее")

# Дополнительные обработчики для подробных действий
@router.callback_query(F.data == "more_detailed")
async def more_detailed_handler(callback: CallbackQuery):
    """Запрос подробного объяснения"""
    await callback.message.answer(
        "📚 Напишите: <b>\"Расскажи подробнее\"</b> или <b>\"Дай больше деталей\"</b>\n\n"
        "🤖 Я предоставлю развернутое объяснение!",
        parse_mode="HTML"
    )
    await callback.answer("Жду запрос на подробности")

@router.callback_query(F.data == "more_examples")
async def more_examples_handler(callback: CallbackQuery):
    """Запрос примеров"""
    await callback.message.answer(
        "💡 Напишите: <b>\"Приведи примеры\"</b> или <b>\"Покажи на примерах\"</b>\n\n"
        "🤖 Я дам конкретные примеры!",
        parse_mode="HTML"
    )
    await callback.answer("Жду запрос примеров")

@router.callback_query(F.data == "more_simple")
async def more_simple_handler(callback: CallbackQuery):
    """Запрос простого объяснения"""
    await callback.message.answer(
        "🎯 Напишите: <b>\"Объясни простыми словами\"</b> или <b>\"Упрости объяснение\"</b>\n\n"
        "🤖 Я объясню проще и понятнее!",
        parse_mode="HTML"
    )
    await callback.answer("Жду запрос на упрощение")

@router.callback_query(F.data == "more_alternatives")
async def more_alternatives_handler(callback: CallbackQuery):
    """Запрос альтернативных решений"""
    await callback.message.answer(
        "🔀 Напишите: <b>\"Покажи альтернативы\"</b> или <b>\"Есть ли другие варианты?\"</b>\n\n"
        "🤖 Я предложу другие решения!",
        parse_mode="HTML"
    )
    await callback.answer("Жду запрос альтернатив")

@router.callback_query(F.data == "more_sources")
async def more_sources_handler(callback: CallbackQuery):
    """Запрос источников"""
    await callback.message.answer(
        "📖 Напишите: <b>\"Дай ссылки на источники\"</b> или <b>\"Где можно почитать подробнее?\"</b>\n\n"
        "🤖 Я поищу полезные ссылки!",
        parse_mode="HTML"
    )
    await callback.answer("Жду запрос источников")

@router.callback_query(F.data == "more_steps")
async def more_steps_handler(callback: CallbackQuery):
    """Запрос пошагового разбора"""
    await callback.message.answer(
        "🧩 Напишите: <b>\"Разбери по шагам\"</b> или <b>\"Покажи пошагово\"</b>\n\n"
        "🤖 Я распишу всё поэтапно!",
        parse_mode="HTML"
    )
    await callback.answer("Жду запрос на пошаговый разбор")