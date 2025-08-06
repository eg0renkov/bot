# Скрипт быстрой синхронизации изменений с сервером
param(
    [string]$CommitMessage = "Quick update"
)

Write-Host "🔄 Синхронизация изменений с сервером..." -ForegroundColor Green

# 1. Коммитим локальные изменения
Write-Host "📝 Коммит локальных изменений..." -ForegroundColor Cyan
git add .
git commit -m $CommitMessage
git push origin main

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ошибка отправки в Git" -ForegroundColor Red
    exit 1
}

# 2. Обновляем на сервере
Write-Host "📤 Обновление на сервере..." -ForegroundColor Cyan
$updateCommands = @"
cd /root/telegram-ai-bot
git pull origin main
sudo systemctl restart telegram-ai-bot
sudo systemctl status telegram-ai-bot --no-pager
"@

ssh root@109.120.142.202 $updateCommands

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Синхронизация завершена!" -ForegroundColor Green
} else {
    Write-Host "❌ Ошибка обновления на сервере" -ForegroundColor Red
}