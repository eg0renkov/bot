#!/bin/bash

# 🔄 Скрипт обновления бота на сервере
echo "🔄 Обновление Telegram AI Bot..."

# Останавливаем бота
echo "⏹️ Остановка бота..."
sudo systemctl stop telegram-ai-bot

# Активируем виртуальное окружение
echo "🐍 Активация виртуального окружения..."
source venv/bin/activate

# Обновляем зависимости если нужно
echo "📦 Проверка обновлений зависимостей..."
pip install -r requirements.txt --upgrade

# Создаем backup конфигурации
echo "💾 Создание backup конфигурации..."
if [ -f .env ]; then
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
fi

# Перезапускаем systemd (если изменился сервис)
sudo systemctl daemon-reload

# Запускаем бота
echo "▶️ Запуск бота..."
sudo systemctl start telegram-ai-bot

# Проверяем статус
sleep 2
echo "✅ Статус бота:"
sudo systemctl status telegram-ai-bot --no-pager

echo ""
echo "🔧 Полезные команды:"
echo "• Просмотр логов: sudo journalctl -u telegram-ai-bot -f"
echo "• Перезапуск: sudo systemctl restart telegram-ai-bot"
echo "• Остановка: sudo systemctl stop telegram-ai-bot"
echo ""
echo "✅ Обновление завершено!"