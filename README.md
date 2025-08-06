# 🤖 Telegram AI Bot на Python

Полнофункциональный AI-ассистент для Telegram на основе ChatGPT с поддержкой голосовых сообщений и памятью диалогов.

## ✨ Возможности

- 🤖 **ChatGPT интеграция** - умные ответы через OpenAI API
- 🎤 **Голосовые сообщения** - распознавание речи (Whisper) и синтез речи (TTS)
- 🧠 **Память диалогов** - запоминает контекст разговора
- 📝 **Команды управления** - /start, /help, /clear
- 📋 **Черновики писем** - создание, редактирование, AI генерация
- 🗄️ **Простое хранение** - файловая система или Supabase
- 🧠 **Векторная память** - семантический поиск и долгосрочное обучение
- 🔧 **Легкая настройка** - всего 2 обязательных API ключа

## 📁 Структура проекта

```
telegram_ai_bot_python/
├── bot/                    # Основной код бота
│   ├── main.py            # Точка входа
│   └── __init__.py        
├── handlers/              # Обработчики сообщений
│   ├── messages.py        # Логика обработки
│   └── __init__.py        
├── config/                # Конфигурация
│   ├── settings.py        # Настройки бота
│   └── __init__.py        
├── database/              # Система памяти
│   ├── memory.py          # Простое хранение диалогов
│   ├── vector_memory.py   # Векторная память (Supabase)
│   └── __init__.py        
├── utils/                 # Утилиты
│   ├── openai_client.py   # OpenAI клиент
│   └── __init__.py        
├── requirements.txt       # Зависимости Python
├── .env.example          # Пример переменных окружения
├── run.py                # Скрипт запуска
├── supabase_vector_setup.sql  # SQL для векторной памяти
├── SUPABASE_SETUP.md     # Настройка Supabase
└── README.md             # Этот файл
```

## 🚀 Быстрый запуск

### Шаг 1: Клонирование и установка

```bash
# Перейти в папку проекта
cd telegram_ai_bot_python

# Создать виртуальное окружение (рекомендуется)
python -m venv venv

# Активировать виртуальное окружение
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt
```

### Шаг 2: Получение API ключей

#### Telegram Bot Token
1. Найти в Telegram: `@BotFather`
2. Отправить команду: `/newbot`
3. Следовать инструкциям
4. Скопировать токен бота

#### OpenAI API Key
1. Зайти на [platform.openai.com](https://platform.openai.com)
2. Создать аккаунт или войти
3. Перейти в API Keys
4. Создать новый ключ
5. Пополнить баланс ($5+ рекомендуется)

### Шаг 3: Настройка переменных окружения

```bash
# Скопировать пример конфигурации
copy .env.example .env

# Отредактировать .env файл своими данными
```

Пример `.env`:
```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrSTUvwxyz
OPENAI_API_KEY=sk-abcd1234567890efghijklmnopqrstuv
OPENAI_MODEL=gpt-3.5-turbo
LOG_LEVEL=INFO
```

### Шаг 4: Запуск бота

```bash
# Запуск бота
python run.py
```

Если все настроено правильно, увидите:
```
🤖 Запуск Telegram AI бота...
2025-08-03 15:30:45 - INFO - Настройки проверены успешно
2025-08-03 15:30:46 - INFO - Бот запущен и готов к работе!
```

## 💬 Использование бота

### Команды
- `/start` - начать работу с ботом
- `/help` - показать справку
- `/clear` - очистить историю диалога

### Текстовые сообщения
Просто напишите любое сообщение боту - он ответит с помощью ChatGPT, используя контекст предыдущих сообщений.

### Голосовые сообщения
Отправьте голосовое сообщение - бот:
1. Распознает речь (Whisper)
2. Обработает через ChatGPT
3. Ответит текстом
4. Для коротких ответов также пришлет голосовой ответ

## ⚙️ Дополнительные настройки

### Векторная память (Supabase)
Для продвинутой памяти с семантическим поиском:

1. **Следовать инструкции в `SUPABASE_SETUP.md`**
2. **Выполнить SQL из `supabase_vector_setup.sql`**
3. **Добавить в `.env`:**
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
VECTOR_MEMORY_ENABLED=true
```

**Новые команды:**
- `/memory_stats` - статистика памяти
- `/search_memory <запрос>` - поиск в памяти  
- `/save_knowledge <тема> <инфо>` - сохранить знания
- `/clear_memory` - очистить всю память
- `/vector_help` - справка по векторной памяти

### Настройки в config/settings.py
```python
MAX_MESSAGE_LENGTH = 4000      # Максимальная длина сообщения
MAX_HISTORY_MESSAGES = 20      # Сколько сообщений помнить
VOICE_ENABLED = True           # Включить голосовые сообщения
MEMORY_ENABLED = True          # Включить память диалогов
```

## 🛠️ Разработка

### Добавление новых функций
1. Создать обработчик в `handlers/`
2. Зарегистрировать в `bot/main.py`
3. Добавить настройки в `config/settings.py`

### Структура обработчика
```python
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()

@router.message(Command("mycommand"))
async def my_handler(message: Message):
    await message.answer("Мой ответ")
```

## 🐛 Устранение проблем

### Бот не отвечает
1. Проверить токен бота в `.env`
2. Убедиться что бот запущен
3. Проверить логи в `bot.log`

### Ошибки OpenAI
1. Проверить API ключ
2. Убедиться что есть баланс на аккаунте
3. Проверить доступность API

### Проблемы с голосом
1. Убедиться что есть доступ к Whisper API
2. Проверить формат аудио файлов
3. Проверить баланс OpenAI

### Логи
Все логи сохраняются в файл `bot.log` и выводятся в консоль.

## 📦 Деплой

### На VPS/сервере
```bash
# Клонировать репозиторий
git clone <your-repo>
cd telegram_ai_bot_python

# Установить зависимости
pip install -r requirements.txt

# Настроить .env файл
nano .env

# Запустить через screen/tmux
screen -S telegram_bot
python run.py
# Ctrl+A, D для отключения от screen
```

### С помощью Docker (опционально)
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "run.py"]
```

## 🤝 Поддержка

Если возникли проблемы:
1. Проверьте логи в `bot.log`
2. Убедитесь что все API ключи корректны
3. Проверьте что установлены все зависимости
4. Убедитесь что Python версии 3.8+

## 📄 Лицензия

MIT License - можете использовать как угодно.