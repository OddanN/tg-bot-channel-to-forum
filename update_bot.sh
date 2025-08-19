#!/bin/bash

# Путь к проекту
PROJECT_DIR="/path/to/tg-bot-channel-to-forum"
LOG_FILE="$PROJECT_DIR/update.log"

echo "========== $(date) ==========" >> "$LOG_FILE"
echo "Проверка обновлений..." >> "$LOG_FILE"

cd "$PROJECT_DIR" || { echo "Каталог не найден!"; exit 1; }

git fetch origin main >> "$LOG_FILE" 2>&1

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" != "$REMOTE" ]; then
    echo "Найдены обновления. Обновляем проект..." >> "$LOG_FILE"
    git pull origin main >> "$LOG_FILE" 2>&1
    docker-compose build >> "$LOG_FILE" 2>&1
    docker-compose up -d >> "$LOG_FILE" 2>&1
    echo "✅ Бот обновлён и перезапущен." >> "$LOG_FILE"
else
    echo "Нет обновлений." >> "$LOG_FILE"
fi
