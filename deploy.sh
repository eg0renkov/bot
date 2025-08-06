#!/bin/bash

# 🚀 Скрипт развертывания Telegram AI Bot на Ubuntu 22
echo "🚀 Начинаем развертывание Telegram AI Bot..."

# Установка системных пакетов
echo "📦 Установка системных пакетов..."
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git htop screen nano vim curl wget

# Создание виртуального окружения
echo "🐍 Создание виртуального окружения..."
python3 -m venv venv

# Активация виртуального окружения
echo "✅ Активация виртуального окружения..."
source venv/bin/activate

# Обновление pip
pip install --upgrade pip

# Установка зависимостей
echo "📦 Установка Python зависимостей..."
pip install -r requirements.txt

# Создание директорий
echo "📁 Создание необходимых директорий..."
mkdir -p data
mkdir -p data/contacts
mkdir -p data/drafts  
mkdir -p data/search_cache
mkdir -p data/sent_emails
mkdir -p data/temp_emails
mkdir -p data/user_settings
mkdir -p data/user_tokens
mkdir -p logs

# Копирование конфигурации
if [ ! -f .env ]; then
    echo "⚙️ Создание файла конфигурации..."
    cp .env.example .env
    echo "❗ ВАЖНО: Отредактируйте файл .env с вашими настройками!"
fi

# Создание systemd сервиса
echo "🔧 Создание systemd сервиса..."
sudo tee /etc/systemd/system/telegram-ai-bot.service > /dev/null <<EOF
[Unit]
Description=Telegram AI Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python run_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Перезагрузка systemd
sudo systemctl daemon-reload

# Включение автозапуска
sudo systemctl enable telegram-ai-bot

echo "✅ Развертывание завершено!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Отредактируйте файл .env с вашими настройками"
echo "2. Запустите бота: sudo systemctl start telegram-ai-bot"
echo "3. Проверьте статус: sudo systemctl status telegram-ai-bot"
echo "4. Просмотр логов: sudo journalctl -u telegram-ai-bot -f"
echo ""
echo "🎉 Бот готов к запуску!"