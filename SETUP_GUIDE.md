# 📋 Пошаговая инструкция запуска

Подробное руководство по настройке и запуску Telegram AI бота.

## 🎯 Что вам понадобится

- ✅ Компьютер с Python 3.8+
- ✅ Telegram аккаунт
- ✅ OpenAI аккаунт с API доступом
- ✅ 10-15 минут времени

## 📥 Шаг 1: Подготовка

### 1.1 Проверка Python
```bash
python --version
```
Должно показать Python 3.8 или выше. Если нет - [скачать Python](https://python.org).

### 1.2 Скачивание бота
```bash
# Если есть git
git clone <ваш-репозиторий>

# Или просто скачать папку telegram_ai_bot_python
```

### 1.3 Переход в папку
```bash
cd telegram_ai_bot_python
```

## 🤖 Шаг 2: Создание Telegram бота

### 2.1 Найти BotFather
1. Открыть Telegram
2. Найти: `@BotFather`
3. Нажать "Start"

### 2.2 Создать бота
1. Отправить: `/newbot`
2. Придумать имя бота (например: "Мой AI Помощник")
3. Придумать username (например: "my_ai_helper_bot")
4. Скопировать токен (выглядит как: `1234567890:ABCdef...`)

⚠️ **Важно:** Сохраните токен - он понадобится!

## 🧠 Шаг 3: Получение OpenAI API ключа

### 3.1 Регистрация
1. Перейти на [platform.openai.com](https://platform.openai.com)
2. Зарегистрироваться или войти
3. Подтвердить телефон (обязательно)

### 3.2 Создание API ключа
1. Перейти в: API Keys
2. Нажать: "Create new secret key"
3. Скопировать ключ (выглядит как: `sk-abcd1234...`)

⚠️ **Важно:** Ключ показывается только один раз!

### 3.3 Пополнение баланса
1. Перейти в: Billing
2. Add payment method
3. Пополнить на $5-10 (хватит надолго)

## 💻 Шаг 4: Установка зависимостей

### 4.1 Создание виртуального окружения (рекомендуется)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 4.2 Установка библиотек
```bash
pip install -r requirements.txt
```

Если ошибка, попробуйте:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## ⚙️ Шаг 5: Настройка конфигурации

### 5.1 Создание .env файла
```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

### 5.2 Редактирование .env
Открыть файл `.env` в любом текстовом редакторе и заполнить:

```env
# Ваш токен от BotFather
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrSTUvwxyz

# Ваш ключ от OpenAI
OPENAI_API_KEY=sk-abcd1234567890efghijklmnopqrstuv

# Модель (можно оставить как есть)
OPENAI_MODEL=gpt-3.5-turbo

# Уровень логирования
LOG_LEVEL=INFO
```

⚠️ **Важно:** Замените примеры на ваши реальные ключи!

## 🚀 Шаг 6: Запуск бота

### 6.1 Первый запуск
```bash
python run.py
```

### 6.2 Проверка запуска
Если все правильно, увидите:
```
🤖 Запуск Telegram AI бота...
2025-08-03 15:30:45 - INFO - Настройки проверены успешно
2025-08-03 15:30:46 - INFO - Бот запущен и готов к работе!
```

### 6.3 Тестирование
1. Найти своего бота в Telegram
2. Нажать "Start"
3. Отправить `/start`
4. Должно прийти приветствие
5. Написать любое сообщение
6. Бот должен ответить

## 🎤 Шаг 7: Тестирование голосовых сообщений

1. Записать голосовое сообщение
2. Отправить боту
3. Бот должен:
   - Написать "🎤 Обрабатываю голосовое сообщение..."
   - Показать распознанный текст
   - Дать ответ

## ❗ Возможные проблемы и решения

### Проблема: Бот не запускается
**Решение:**
1. Проверить Python версию: `python --version`
2. Проверить .env файл
3. Проверить что все зависимости установлены

### Проблема: "Token validation failed"
**Решение:**
1. Проверить токен в .env файле
2. Убедиться что нет лишних пробелов
3. Получить новый токен от @BotFather

### Проблема: "OpenAI API error"
**Решение:**
1. Проверить API ключ
2. Проверить баланс на platform.openai.com
3. Попробовать другую модель (gpt-4o-mini)

### Проблема: Бот не отвечает
**Решение:**
1. Проверить что бот запущен
2. Посмотреть логи в файле bot.log
3. Перезапустить бота

### Проблема: Голосовые сообщения не работают
**Решение:**
1. Проверить баланс OpenAI
2. Убедиться что есть доступ к Whisper API
3. Попробовать более короткое сообщение

## 🔄 Шаг 8: Постоянная работа (для продвинутых)

### На Windows (простой способ)
Создать bat-файл `start_bot.bat`:
```batch
@echo off
cd /d "C:\path\to\telegram_ai_bot_python"
call venv\Scripts\activate
python run.py
pause
```

### На Linux/Mac (через systemd)
Создать `/etc/systemd/system/telegram-bot.service`:
```ini
[Unit]
Description=Telegram AI Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/telegram_ai_bot_python
ExecStart=/path/to/venv/bin/python run.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Запустить:
```bash
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
```

## 🎉 Готово!

Ваш AI бот готов к работе! Теперь вы можете:

- 💬 Общаться с ботом текстом
- 🎤 Отправлять голосовые сообщения
- 🧠 Бот запомнит контекст разговора
- 🔧 Настраивать бота под свои нужды

## 📞 Поддержка

Если что-то не работает:
1. Проверьте логи в `bot.log`
2. Убедитесь что все API ключи правильные
3. Попробуйте перезапустить бота
4. Проверьте интернет соединение

**Удачи с вашим AI ботом! 🚀**