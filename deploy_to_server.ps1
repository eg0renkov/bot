# PowerShell скрипт для автоматического развертывания на сервер
param(
    [Parameter(Mandatory=$true)]
    [string]$ServerIP,
    
    [Parameter(Mandatory=$true)]
    [string]$Username,
    
    [string]$Password
)

Write-Host "🚀 Автоматическое развертывание Telegram AI Bot на сервер" -ForegroundColor Green
Write-Host "Сервер: $ServerIP" -ForegroundColor Yellow
Write-Host "Пользователь: $Username" -ForegroundColor Yellow

# 1. Создание архива
Write-Host "📦 Создание архива..." -ForegroundColor Cyan
$excludeItems = @("venv", "data", "*.log", "__pycache__", "*.pyc", ".git")
tar -czf telegram-ai-bot.tar.gz --exclude=venv --exclude=data --exclude="*.log" --exclude=__pycache__ .

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ошибка создания архива" -ForegroundColor Red
    exit 1
}

# 2. Копирование на сервер
Write-Host "📤 Копирование на сервер..." -ForegroundColor Cyan
scp telegram-ai-bot.tar.gz "$Username@$ServerIP`:~"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ошибка копирования на сервер" -ForegroundColor Red
    exit 1
}

# 3. Развертывание на сервере
Write-Host "🔧 Развертывание на сервере..." -ForegroundColor Cyan
$commands = @"
mkdir -p telegram-ai-bot
cd telegram-ai-bot
tar -xzf ../telegram-ai-bot.tar.gz
chmod +x deploy.sh
./deploy.sh
"@

ssh "$Username@$ServerIP" $commands

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ошибка развертывания" -ForegroundColor Red
    exit 1
}

# 4. Очистка локального архива
Remove-Item telegram-ai-bot.tar.gz -Force

Write-Host "✅ Развертывание завершено успешно!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Следующие шаги:" -ForegroundColor Yellow
Write-Host "1. ssh $Username@$ServerIP" -ForegroundColor White
Write-Host "2. cd telegram-ai-bot" -ForegroundColor White
Write-Host "3. nano .env  # Настройте токены" -ForegroundColor White
Write-Host "4. sudo systemctl start telegram-ai-bot" -ForegroundColor White
Write-Host "5. sudo systemctl status telegram-ai-bot" -ForegroundColor White