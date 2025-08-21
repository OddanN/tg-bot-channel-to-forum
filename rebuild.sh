#!/bin/bash
# Скрипт для управления ботом через Docker
#
# Использование:
#   ./rebuild.sh update   - остановка контейнера, git pull, пересборка и запуск
#   ./rebuild.sh rebuild  - пересборка и запуск без git pull
#   ./rebuild.sh logs     - просмотр логов контейнера в реальном времени

ACTION=$1  # первый аргумент скрипта

if [ -z "$ACTION" ]; then
    echo "Использование: $0 {update|rebuild|logs}"
    exit 1
fi

case $ACTION in
    update)
        echo "Останавливаем контейнер..."
        docker compose down

        echo "Подтягиваем последние изменения из Git..."
        git pull

        echo "Собираем образ..."
        docker compose build

        echo "Запускаем контейнер..."
        docker compose up -d

        echo "Готово ✅"
        ;;
    rebuild)
        echo "Пересобираем и перезапускаем контейнер..."
        docker compose build
        docker compose up -d
        ;;
    logs)
        echo "Показываем логи контейнера..."
        docker compose logs -f
        ;;
    *)
        echo "Неизвестная команда. Используйте: update | rebuild | logs"
        exit 1
        ;;
esac
