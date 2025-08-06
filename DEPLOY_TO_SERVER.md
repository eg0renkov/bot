# 🚀 Развертывание бота на Ubuntu 22 сервере

## 📋 План развертывания

1. **Подготовка локального проекта** ✅
2. **Настройка сервера** 
3. **Перенос проекта**
4. **Установка зависимостей**
5. **Настройка автозапуска**
6. **Настройка удаленного редактирования**

---

## ✅ Шаг 1: Подготовка локального проекта (завершен)

Все необходимые файлы созданы:
- `requirements.txt` - зависимости Python
- `deploy.sh` - скрипт автоматического развертывания
- `update_bot.sh` - скрипт обновления бота
- `run_server.py` - точка входа для сервера
- `.env.example` - пример конфигурации
- `.gitignore` - исключения для Git

---

## 🖥️ Шаг 2: Настройка сервера Ubuntu 22

### Подключение к серверу:
```bash
ssh root@YOUR_SERVER_IP
# или
ssh username@YOUR_SERVER_IP
```

### Создание пользователя для бота (рекомендуется):
```bash
# Создаем пользователя
sudo adduser telegram-bot

# Добавляем в группу sudo (если нужно)
sudo usermod -aG sudo telegram-bot

# Переходим на пользователя
su - telegram-bot
```

---

## 📁 Шаг 3: Перенос проекта на сервер

### Вариант 1: Через Git (рекомендуется)

**На локальной машине:**
```bash
# Создаем Git репозиторий (если еще не создан)
git init
git add .
git commit -m "Initial commit"

# Добавляем remote репозиторий (GitHub/GitLab)
git remote add origin https://github.com/YOUR_USERNAME/telegram-ai-bot.git
git push -u origin main
```

**На сервере:**
```bash
# Переходим в домашнюю папку
cd ~

# Клонируем репозиторий
git clone https://github.com/YOUR_USERNAME/telegram-ai-bot.git
cd telegram-ai-bot
```

### Вариант 2: Через SCP

**На локальной машине (из папки с ботом):**
```bash
# Архивируем проект
tar -czf telegram-ai-bot.tar.gz --exclude='venv' --exclude='data' --exclude='*.log' .

# Копируем на сервер
scp telegram-ai-bot.tar.gz username@YOUR_SERVER_IP:~

# Подключаемся к серверу
ssh username@YOUR_SERVER_IP

# Распаковываем
tar -xzf telegram-ai-bot.tar.gz
mkdir telegram-ai-bot
tar -xzf telegram-ai-bot.tar.gz -C telegram-ai-bot
cd telegram-ai-bot
```

---

## 🔧 Шаг 4: Автоматическая установка

**На сервере выполните:**
```bash
# Делаем скрипт исполняемым
chmod +x deploy.sh

# Запускаем автоматическое развертывание
./deploy.sh
```

### Что делает скрипт deploy.sh:
1. ✅ Устанавливает системные пакеты (Python, pip, git)
2. ✅ Создает виртуальное окружение
3. ✅ Устанавливает Python зависимости
4. ✅ Создает необходимые папки
5. ✅ Копирует .env.example в .env
6. ✅ Создает systemd сервис для автозапуска
7. ✅ Настраивает автозапуск при перезагрузке

---

## ⚙️ Шаг 5: Настройка конфигурации

### Редактируем .env файл:
```bash
nano .env
```

**Обязательные настройки:**
```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11

# OpenAI Configuration  
OPENAI_API_KEY=sk-...your_openai_key_here

# Остальные настройки можно оставить по умолчанию
```

---

## 🚀 Шаг 6: Запуск и проверка

### Запуск бота:
```bash
sudo systemctl start telegram-ai-bot
```

### Проверка статуса:
```bash
sudo systemctl status telegram-ai-bot
```

### Просмотр логов:
```bash
# Просмотр логов в реальном времени
sudo journalctl -u telegram-ai-bot -f

# Последние логи
sudo journalctl -u telegram-ai-bot --no-pager
```

### Управление ботом:
```bash
# Перезапуск
sudo systemctl restart telegram-ai-bot

# Остановка  
sudo systemctl stop telegram-ai-bot

# Включить автозапуск
sudo systemctl enable telegram-ai-bot

# Отключить автозапуск
sudo systemctl disable telegram-ai-bot
```

---

## 🔄 Шаг 7: Настройка удаленного редактирования

### Вариант 1: VS Code Remote SSH (рекомендуется)

**1. Установите VS Code и расширение "Remote - SSH"**

**2. Настройте SSH подключение:**
```
Host telegram-bot-server
    HostName YOUR_SERVER_IP  
    User telegram-bot
    IdentityFile ~/.ssh/id_rsa
```

**3. Подключитесь через VS Code:**
- `Ctrl+Shift+P` → "Remote-SSH: Connect to Host"
- Выберите `telegram-bot-server`
- Откройте папку `/home/telegram-bot/telegram-ai-bot`

### Вариант 2: Через Git (для быстрых изменений)

**Рабочий процесс:**
```bash
# На локальной машине - делаем изменения
git add .
git commit -m "Update bot features"
git push

# На сервере - получаем изменения  
git pull
./update_bot.sh
```

### Вариант 3: Прямое редактирование на сервере
```bash
# Подключаемся к серверу
ssh username@YOUR_SERVER_IP
cd telegram-ai-bot

# Редактируем файлы через nano/vim
nano handlers/messages.py

# Перезапускаем бота
sudo systemctl restart telegram-ai-bot
```

---

## 📋 Полезные команды для мониторинга

### Системные ресурсы:
```bash
# Использование CPU и RAM
htop

# Использование диска
df -h

# Процессы Python
ps aux | grep python

# Сетевые соединения
netstat -tlnp | grep python
```

### Логи системы:
```bash
# Системные логи
sudo journalctl -f

# Логи только бота
sudo journalctl -u telegram-ai-bot -f

# Логи за последний час
sudo journalctl -u telegram-ai-bot --since "1 hour ago"
```

### Обновление бота:
```bash
# Автоматическое обновление (останавливает, обновляет, запускает)
./update_bot.sh

# Или ручное обновление
sudo systemctl stop telegram-ai-bot
git pull  # если используется Git
sudo systemctl start telegram-ai-bot
```

---

## 🛡️ Безопасность

### Настройка firewall:
```bash
# Включаем UFW
sudo ufw enable

# Разрешаем SSH
sudo ufw allow ssh

# Разрешаем только необходимые порты
sudo ufw allow 22/tcp

# Проверяем статус
sudo ufw status
```

### Регулярные обновления:
```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Автоматическое обновление зависимостей Python
pip install --upgrade -r requirements.txt
```

---

## 🎯 Финальная проверка

### ✅ Чек-лист успешного развертывания:

1. **Сервис запущен:** `sudo systemctl status telegram-ai-bot` показывает "active (running)"
2. **Логи без ошибок:** `sudo journalctl -u telegram-ai-bot --no-pager` без критических ошибок
3. **Бот отвечает:** Отправьте `/start` в Telegram
4. **Авторизация работает:** Токен `SECURE_BOT_ACCESS_2024` принимается
5. **Функции работают:** Меню, AI ответы, создание контактов
6. **Автозапуск настроен:** После `sudo reboot` бот запускается автоматически

### 🎉 Поздравляем! Ваш AI-бот успешно развернут на сервере!

---

## 📞 Поддержка

### При проблемах проверьте:
1. **Логи бота:** `sudo journalctl -u telegram-ai-bot -f`
2. **Конфигурацию:** Правильность .env файла
3. **Сеть:** Доступ к Telegram API и OpenAI
4. **Права доступа:** Права на папки data/
5. **Системные ресурсы:** Достаточно RAM и CPU

### Команды диагностики:
```bash
# Проверка статуса
sudo systemctl status telegram-ai-bot

# Тест Python окружения
source venv/bin/activate && python -c "import aiogram, openai; print('OK')"

# Проверка файлов конфигурации
ls -la .env data/

# Проверка портов
netstat -tlnp | grep python
```