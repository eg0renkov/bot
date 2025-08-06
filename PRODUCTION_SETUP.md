# 🚀 Production Setup - Стабильный запуск бота

## 🎯 Рекомендуемый вариант: Systemd + мониторинг

### ✅ Преимущества:
- Автоматический перезапуск при падении
- Запуск при загрузке сервера
- Логирование через journald
- Управление через системные команды
- Мониторинг ресурсов

### 🔧 Настройка (уже сделано через deploy.sh):

```bash
# Проверим что сервис создался
sudo systemctl status telegram-ai-bot

# Если нет - создаем вручную
sudo tee /etc/systemd/system/telegram-ai-bot.service > /dev/null <<EOF
[Unit]
Description=Telegram AI Bot
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=5
User=root
WorkingDirectory=/root/telegram-ai-bot
Environment=PATH=/root/telegram-ai-bot/venv/bin
ExecStart=/root/telegram-ai-bot/venv/bin/python run_server.py
StandardOutput=journal
StandardError=journal
SyslogIdentifier=telegram-ai-bot

[Install]
WantedBy=multi-user.target
EOF

# Перезагружаем systemd
sudo systemctl daemon-reload
sudo systemctl enable telegram-ai-bot
```

---

## 🛡️ Дополнительная защита от падений

### 1. Улучшенный systemd сервис с автоперезапуском:

```bash
# Создаем улучшенный сервис
sudo tee /etc/systemd/system/telegram-ai-bot.service > /dev/null <<EOF
[Unit]
Description=Telegram AI Bot Production
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=300
StartLimitBurst=5

[Service]
Type=simple
Restart=always
RestartSec=10
RestartPolicy=always
User=root
WorkingDirectory=/root/telegram-ai-bot
Environment=PATH=/root/telegram-ai-bot/venv/bin
Environment=PYTHONUNBUFFERED=1
ExecStart=/root/telegram-ai-bot/venv/bin/python run_server.py
ExecReload=/bin/kill -HUP $MAINPID
KillMode=mixed
TimeoutStopSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=telegram-ai-bot

# Ограничения ресурсов
MemoryMax=1G
CPUQuota=80%

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable telegram-ai-bot
```

### 2. Скрипт мониторинга:

```bash
# Создаем скрипт мониторинга
sudo tee /root/telegram-ai-bot/monitor_bot.sh > /dev/null <<'EOF'
#!/bin/bash

LOG_FILE="/var/log/telegram-bot-monitor.log"
SERVICE_NAME="telegram-ai-bot"

while true; do
    if ! systemctl is-active --quiet $SERVICE_NAME; then
        echo "[$(date)] Bot is down, restarting..." >> $LOG_FILE
        systemctl start $SERVICE_NAME
        sleep 30
    fi
    
    # Проверяем использование памяти
    MEM_USAGE=$(ps -o pid,ppid,cmd,%mem --sort=-%mem | grep python | grep -v grep | head -1 | awk '{print $4}')
    if (( $(echo "$MEM_USAGE > 80" | bc -l) )); then
        echo "[$(date)] High memory usage: $MEM_USAGE%, restarting..." >> $LOG_FILE
        systemctl restart $SERVICE_NAME
    fi
    
    sleep 60
done
EOF

chmod +x /root/telegram-ai-bot/monitor_bot.sh
```

---

## 🐳 Альтернатива: Docker (если хотите изоляцию)

### Создаем Dockerfile:

```bash
# В папке с ботом создаем Dockerfile
cat > Dockerfile <<'EOF'
FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию
WORKDIR /app

# Копируем requirements.txt
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Создаем необходимые директории
RUN mkdir -p data logs

# Запускаем бота
CMD ["python", "run_server.py"]
EOF

# Создаем docker-compose.yml
cat > docker-compose.yml <<'EOF'
version: '3.8'

services:
  telegram-bot:
    build: .
    container_name: telegram-ai-bot
    restart: unless-stopped
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./.env:/app/.env
    environment:
      - PYTHONUNBUFFERED=1
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe').raise_for_status()"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
EOF
```

### Запуск через Docker:
```bash
# Сборка и запуск
docker-compose up -d

# Просмотр логов
docker-compose logs -f telegram-bot

# Управление
docker-compose restart telegram-bot
docker-compose stop telegram-bot
```

---

## 📊 Мониторинг и алерты

### 1. Простой скрипт проверки здоровья:

```bash
# Создаем healthcheck скрипт
cat > /root/telegram-ai-bot/healthcheck.sh <<'EOF'
#!/bin/bash

# Проверяем что процесс запущен
if ! pgrep -f "python run_server.py" > /dev/null; then
    echo "ERROR: Bot process not running"
    systemctl restart telegram-ai-bot
    exit 1
fi

# Проверяем что бот отвечает на Telegram API
if [ ! -z "$TELEGRAM_BOT_TOKEN" ]; then
    response=$(curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe")
    if [[ $response != *'"ok":true'* ]]; then
        echo "ERROR: Bot not responding to Telegram API"
        systemctl restart telegram-ai-bot
        exit 1
    fi
fi

echo "OK: Bot is healthy"
EOF

chmod +x /root/telegram-ai-bot/healthcheck.sh

# Добавляем в crontab для проверки каждые 5 минут
(crontab -l 2>/dev/null; echo "*/5 * * * * /root/telegram-ai-bot/healthcheck.sh >> /var/log/bot-health.log 2>&1") | crontab -
```

### 2. Telegram уведомления о падениях:

```bash
# Скрипт отправки уведомлений в Telegram
cat > /root/telegram-ai-bot/notify_admin.sh <<'EOF'
#!/bin/bash

ADMIN_CHAT_ID="YOUR_ADMIN_CHAT_ID"  # Ваш Telegram ID
BOT_TOKEN="$TELEGRAM_BOT_TOKEN"

MESSAGE="🚨 ALERT: Telegram AI Bot перезапущен на сервере $(hostname) в $(date)"

curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
    -d chat_id="$ADMIN_CHAT_ID" \
    -d text="$MESSAGE"
EOF

chmod +x /root/telegram-ai-bot/notify_admin.sh
```

---

## 🎯 Рекомендации для вашего случая:

### **Лучший вариант - улучшенный systemd:**

```bash
# 1. Обновляем systemd сервис для максимальной стабильности
sudo systemctl stop telegram-ai-bot

# Копируем улучшенную конфигурацию (из блока выше)
sudo tee /etc/systemd/system/telegram-ai-bot.service > /dev/null <<EOF
[Unit]
Description=Telegram AI Bot Production
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=300
StartLimitBurst=5

[Service]
Type=simple
Restart=always
RestartSec=10
User=root
WorkingDirectory=/root/telegram-ai-bot
Environment=PATH=/root/telegram-ai-bot/venv/bin
Environment=PYTHONUNBUFFERED=1
ExecStart=/root/telegram-ai-bot/venv/bin/python run_server.py
StandardOutput=journal
StandardError=journal
SyslogIdentifier=telegram-ai-bot
MemoryMax=1G
CPUQuota=80%

[Install]
WantedBy=multi-user.target
EOF

# 2. Перезагружаем и запускаем
sudo systemctl daemon-reload
sudo systemctl enable telegram-ai-bot
sudo systemctl start telegram-ai-bot

# 3. Проверяем статус
sudo systemctl status telegram-ai-bot

# 4. Мониторинг логов
sudo journalctl -u telegram-ai-bot -f
```

### **Команды управления:**
```bash
# Запуск
sudo systemctl start telegram-ai-bot

# Остановка
sudo systemctl stop telegram-ai-bot

# Перезапуск
sudo systemctl restart telegram-ai-bot

# Статус
sudo systemctl status telegram-ai-bot

# Логи в реальном времени
sudo journalctl -u telegram-ai-bot -f

# Логи за последний час
sudo journalctl -u telegram-ai-bot --since "1 hour ago"
```

---

## ✅ Что получите:

1. **Автоматический перезапуск** при любых падениях
2. **Запуск при загрузке** сервера
3. **Ограничение ресурсов** (1GB RAM, 80% CPU)
4. **Централизованное логирование**
5. **Система мониторинга**
6. **Простое управление** через systemctl

**Этот подход гарантирует максимальную стабильность без лишней сложности Docker!** 🚀