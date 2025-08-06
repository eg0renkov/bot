# 🔐 Настройка SSH для удаленного редактирования

## 🚀 Быстрая настройка SSH ключей

### На локальной машине (Windows):

**1. Генерируем SSH ключ (если еще нет):**
```bash
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
# Просто нажимайте Enter для значений по умолчанию
```

**2. Копируем публичный ключ на сервер:**
```bash
# Замените YOUR_SERVER_IP и username на ваши данные
ssh-copy-id username@YOUR_SERVER_IP

# Или вручную:
cat ~/.ssh/id_rsa.pub | ssh username@YOUR_SERVER_IP "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

**3. Тестируем подключение:**
```bash
ssh username@YOUR_SERVER_IP
# Теперь должно подключаться без пароля
```

### Настройка VS Code Remote SSH:

**1. Установите расширение "Remote - SSH" в VS Code**

**2. Откройте VS Code и нажмите `Ctrl+Shift+P`**

**3. Введите "Remote-SSH: Open SSH Configuration File"**

**4. Добавьте конфигурацию:**
```
Host telegram-bot
    HostName YOUR_SERVER_IP
    User username
    IdentityFile ~/.ssh/id_rsa
    Port 22
```

**5. Подключитесь:**
- `Ctrl+Shift+P` → "Remote-SSH: Connect to Host"
- Выберите "telegram-bot"
- Откройте папку с ботом: `/home/username/telegram-ai-bot`

## 🎯 Готово! Теперь вы можете редактировать код прямо на сервере через VS Code!