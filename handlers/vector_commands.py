from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from database.vector_memory import vector_memory
from config.settings import settings

router = Router()

@router.message(Command("memory_stats"))
async def memory_stats_command(message: Message):
    """Показать статистику памяти пользователя"""
    if not vector_memory:
        await message.answer("❌ Векторная память не настроена")
        return
    
    try:
        user_id = message.from_user.id
        stats = await vector_memory.get_user_stats(user_id)
        
        if not stats:
            await message.answer("📊 Статистика недоступна")
            return
        
        stats_text = f"""
📊 **Статистика вашей памяти:**

💬 Всего разговоров: {stats.get('total_conversations', 0)}
🧠 Записей в базе знаний: {stats.get('knowledge_entries', 0)}
📏 Средняя длина сообщения: {stats.get('avg_conversation_length', 0):.0f} символов

📅 Первое взаимодействие: {stats.get('first_interaction', 'Нет данных')}
🕒 Последнее взаимодействие: {stats.get('last_interaction', 'Нет данных')}

💡 Чем больше мы общаемся, тем лучше я понимаю ваши предпочтения!
        """
        
        await message.answer(stats_text)
        
    except Exception as e:
        print(f"Ошибка получения статистики: {e}")
        await message.answer("❌ Ошибка получения статистики памяти")

@router.message(Command("clear_memory"))
async def clear_memory_command(message: Message):
    """Очистить всю память пользователя"""
    if not vector_memory:
        await message.answer("❌ Векторная память не настроена")
        return
    
    try:
        user_id = message.from_user.id
        success = await vector_memory.clear_user_memory(user_id)
        
        if success:
            await message.answer("✅ Ваша память полностью очищена!\n\n🔄 Начнем знакомство заново.")
        else:
            await message.answer("❌ Ошибка при очистке памяти")
            
    except Exception as e:
        print(f"Ошибка очистки памяти: {e}")
        await message.answer("❌ Ошибка при очистке памяти")

@router.message(Command("search_memory"))
async def search_memory_command(message: Message):
    """Поиск в памяти по запросу"""
    if not vector_memory:
        await message.answer("❌ Векторная память не настроена")
        return
    
    try:
        # Извлекаем поисковый запрос из команды
        command_parts = message.text.split(" ", 1)
        if len(command_parts) < 2:
            await message.answer("🔍 Использование: /search_memory <ваш запрос>\n\nПример: /search_memory музыка")
            return
        
        query = command_parts[1]
        user_id = message.from_user.id
        
        # Ищем в разговорах
        similar_conversations = await vector_memory.search_similar_conversations(user_id, query, 3)
        
        # Ищем в базе знаний
        knowledge_results = await vector_memory.search_knowledge_base(user_id, query, 2)
        
        if not similar_conversations and not knowledge_results:
            await message.answer(f"🔍 По запросу '{query}' ничего не найдено в памяти")
            return
        
        response = f"🔍 **Результаты поиска по запросу:** '{query}'\n\n"
        
        if similar_conversations:
            response += "💬 **Похожие разговоры:**\n"
            for i, conv in enumerate(similar_conversations, 1):
                similarity = conv.get('similarity', 0) * 100
                response += f"{i}. (совпадение: {similarity:.0f}%)\n"
                response += f"   Вы: {conv['user_message'][:100]}...\n"
                response += f"   Я: {conv['ai_response'][:100]}...\n\n"
        
        if knowledge_results:
            response += "🧠 **База знаний:**\n"
            for i, knowledge in enumerate(knowledge_results, 1):
                similarity = knowledge.get('similarity', 0) * 100
                response += f"{i}. {knowledge['topic']} (совпадение: {similarity:.0f}%)\n"
                response += f"   {knowledge['content'][:150]}...\n\n"
        
        # Разбиваем длинное сообщение
        if len(response) > settings.MAX_MESSAGE_LENGTH:
            parts = [response[i:i+settings.MAX_MESSAGE_LENGTH] 
                    for i in range(0, len(response), settings.MAX_MESSAGE_LENGTH)]
            
            for part in parts:
                await message.answer(part)
        else:
            await message.answer(response)
            
    except Exception as e:
        print(f"Ошибка поиска в памяти: {e}")
        await message.answer("❌ Ошибка при поиске в памяти")

@router.message(Command("save_knowledge"))
async def save_knowledge_command(message: Message):
    """Сохранить важную информацию в базу знаний"""
    if not vector_memory:
        await message.answer("❌ Векторная память не настроена")
        return
    
    try:
        # Извлекаем информацию из команды
        command_parts = message.text.split(" ", 2)
        if len(command_parts) < 3:
            await message.answer("""
💾 **Сохранение в базу знаний**

Использование: /save_knowledge <тема> <информация>

Примеры:
• /save_knowledge музыка Люблю рок и джаз
• /save_knowledge работа Программист Python
• /save_knowledge хобби Играю на гитаре
            """)
            return
        
        topic = command_parts[1]
        content = command_parts[2]
        user_id = message.from_user.id
        
        await vector_memory.save_to_knowledge_base(user_id, topic, content, importance=2.0)
        
        await message.answer(f"✅ Сохранено в базу знаний!\n\n📝 Тема: {topic}\n💭 Информация: {content}")
        
    except Exception as e:
        print(f"Ошибка сохранения знаний: {e}")
        await message.answer("❌ Ошибка при сохранении в базу знаний")

@router.message(Command("vector_help"))
async def vector_help_command(message: Message):
    """Справка по векторной памяти"""
    help_text = """
🧠 **Векторная память бота**

Я использую продвинутую векторную память для лучшего понимания контекста!

📋 **Команды памяти:**
• `/memory_stats` - статистика вашей памяти
• `/search_memory <запрос>` - поиск в памяти
• `/save_knowledge <тема> <инфо>` - сохранить важную информацию
• `/clear_memory` - очистить всю память
• `/vector_help` - эта справка

🤖 **Автоматические функции:**
• Запоминаю контекст всех разговоров
• Нахожу похожие темы из прошлого
• Извлекаю важную информацию автоматически
• Становлюсь умнее с каждым разговором

🎯 **Преимущества:**
• Помню детали месячной давности
• Понимаю связи между разными темами
• Персонализированные ответы
• Не повторяю одинаковые вопросы
    """
    
    if vector_memory:
        help_text += "\n✅ Векторная память активна и работает!"
    else:
        help_text += "\n❌ Векторная память не настроена"
    
    await message.answer(help_text)