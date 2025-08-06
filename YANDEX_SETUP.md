# 🔗 Настройка интеграции с Яндекс сервисами

## 📋 Обзор интеграций

Ваш бот теперь поддерживает интеграцию с:
- 📧 **Яндекс.Почта** - чтение, отправка, анализ писем
- 📅 **Яндекс.Календарь** - создание событий, просмотр расписания

## 🔐 Настройка OAuth приложения

### Шаг 1: Создание приложения в Яндексе

1. Перейти на [oauth.yandex.ru](https://oauth.yandex.ru)
2. Войти в Яндекс аккаунт
3. Нажать "Зарегистрировать приложение"
4. Заполнить данные:
   - **Название**: AI Telegram Bot
   - **Описание**: Умный ассистент для работы с почтой и календарем
   - **Платформы**: Веб-сервисы
   - **Callback URL**: `https://ваш-домен.com/yandex/callback`

### Шаг 2: Настройка разрешений

Выбрать необходимые права доступа:

**Для почты:**
- `mail:read` - чтение писем
- `mail:write` - отправка писем

**Для календаря:**
- `calendar:read` - чтение событий
- `calendar:write` - создание событий

### Шаг 3: Получение ключей

После создания приложения получите:
- **Client ID** (идентификатор приложения)
- **Client Secret** (секретный ключ)

## ⚙️ Настройка бота

### Добавить в .env файл:

```env
# Яндекс OAuth (получить на oauth.yandex.ru)
YANDEX_CLIENT_ID=ваш_client_id
YANDEX_CLIENT_SECRET=ваш_client_secret

# URL для OAuth callback (настроить webhook)
YANDEX_REDIRECT_URI=https://ваш-домен.com/yandex/callback
```

## 🌐 Настройка Webhook сервера

Для полной работы OAuth нужен веб-сервер для обработки callback'ов:

### Простой Flask сервер:

```python
from flask import Flask, request, redirect
import requests

app = Flask(__name__)

@app.route('/yandex/callback')
def yandex_callback():
    code = request.args.get('code')
    state = request.args.get('state')
    
    # Обменять код на токен
    token_data = exchange_code_for_token(code)
    
    # Сохранить токен в базу данных
    # save_user_token(user_id, service, token_data)
    
    return "✅ Авторизация успешна! Вернитесь в Telegram бота."

def exchange_code_for_token(code):
    url = "https://oauth.yandex.ru/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": "ваш_client_id",
        "client_secret": "ваш_client_secret",
        "redirect_uri": "https://ваш-домен.com/yandex/callback"
    }
    response = requests.post(url, data=data)
    return response.json()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
```

## 🚀 Альтернативные способы

### 1. Использование ngrok (для тестирования)

```bash
# Установить ngrok
pip install pyngrok

# Запустить туннель
ngrok http 5000

# Использовать полученный URL в настройках OAuth
```

### 2. Деплой на облачные платформы

- **Heroku**: простой деплой Flask приложения
- **Vercel**: serverless функции
- **Railway**: контейнерный деплой
- **VPS**: собственный сервер

## 📱 Использование интеграций

### После настройки OAuth:

1. **В боте нажать "📧 Почта"**
2. **Выбрать "🔗 Подключить почту"**
3. **Пройти авторизацию в браузере**
4. **Вернуться в бота**

### Возможности после подключения:

**Почта:**
- 📨 "Покажи входящие письма"
- ✍️ "Напиши письмо Ивану про встречу"
- 🔍 "Найди письма от банка"
- 📋 "Сохрани письмо в черновики"

**Календарь:**
- 📅 "Что у меня сегодня?"
- ➕ "Создай встречу завтра в 15:00"
- 🔔 "Напомни за час до встречи"
- 👥 "Пригласи команду на созвон"

## 🔒 Безопасность

- ✅ Используется официальный Yandex OAuth 2.0
- ✅ Токены хранятся зашифрованно
- ✅ Доступ только к разрешенным функциям
- ✅ Токены автоматически обновляются
- ✅ Возможность отозвать доступ

## 🛠️ Разработка и тестирование

### Режим разработки (без реального OAuth):

В `.env` файле:
```env
# Отключить реальные интеграции для тестирования
YANDEX_CLIENT_ID=
YANDEX_CLIENT_SECRET=
```

В этом случае бот покажет заглушки с описанием возможностей.

### Тестирование с моками:

```python
# Добавить в settings.py
DEVELOPMENT_MODE = True

# В коде проверять режим:
if settings.DEVELOPMENT_MODE:
    return mock_yandex_data()
else:
    return real_yandex_api_call()
```

## 📞 Поддержка

### Частые проблемы:

**"Redirect URI mismatch"**
- Проверьте что URL в настройках OAuth точно совпадает

**"Invalid client"**
- Проверьте Client ID и Secret в .env файле

**"Access denied"**
- Пользователь отклонил авторизацию
- Попробуйте заново

**"Token expired"**
- Реализовать автоматическое обновление токенов

### Логи для отладки:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Проверяйте логи на ошибки API запросов.

## 🎯 Следующие шаги

1. ✅ Настроить OAuth приложение
2. ✅ Развернуть webhook сервер  
3. ✅ Протестировать авторизацию
4. ✅ Добавить обработку ошибок
5. ✅ Реализовать refresh токенов
6. ✅ Добавить больше функций API

Готовы к современному AI-ассистенту! 🚀