# tg-bot-channel-to-forum

Бот на Python для автоматического репоста сообщений из **Telegram-канала** в **форум-чат (топик)**.  
Поддерживает пересылку текста и медиа (фото, видео, документы), фильтры по типу сообщений и ключевым словам, а также **профессиональное логирование** с ротацией файлов.

---

## ⚡ Возможности
- 📩 Слушает выбранный канал в режиме реального времени  
- 🔄 Репостит новые публикации в указанный форум-чат  
- 🖼 Поддержка текста, фото, видео и документов  
- 🎯 Фильтрация по типу сообщений и ключевым словам  
- 📝 Логирование всех репостов с **ежедневной ротацией** и хранением последних 30 дней  
- 🐳 Запуск через Docker и Portainer с томом для конфигов и логов  

---

## 📦 Структура проекта

```
tg-bot-channel-to-forum/
│── bot.py                # Основной скрипт бота
│── requirements.txt      # Зависимости проекта
│── Dockerfile            # Инструкции для сборки Docker-образа
│── .dockerignore         # Исключения для Docker-образа
│── docker-compose.yml    # Конфигурация Docker Compose
│── update_bot.sh         # Скрипт для автоматического обновления
│── README.md             # Документация
│── volumes/              # Хранится на хосте
    ├── config.json       # Настройки бота
    └── logs/            # Лог-файлы с ротацией (30 дней)
```

---

## 📋 Настройка

### 1. Получение данных для `config.json`

Для работы бота необходим файл `config.json`, содержащий параметры Telegram API, источник сообщений и цели для репоста.

#### Получение `api_id` и `api_hash`
1. Перейдите на [my.telegram.org](https://my.telegram.org) и авторизуйтесь с помощью номера телефона.
2. Выберите **API development tools** → **Create application**.
3. Заполните поля:
   - **App title**: Например, `TgBotChannelToForum`.
   - **Short name**: Например, `TgBot`.
   - **Platform**: `Other` или `Desktop`.
   - **URL** и **Description**: Можно оставить пустыми.
4. Сохраните полученные `api_id` (число, например, `123456`) и `api_hash` (строка, например, `abc123def4567890`).

#### Получение `bot_token`
1. Откройте Telegram и найдите [@BotFather](https://t.me/BotFather).
2. Напишите `/start`, затем `/newbot`.
3. Укажите имя бота (например, `MyChannelToForumBot`) и username (например, `@MyChannelToForumBot`).
4. Сохраните полученный токен (например, `123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890`).

#### Настройка `source_channel`
1. Укажите URL канала, из которого бот будет брать сообщения (например, `https://t.me/your_channel` для публичного канала или `https://t.me/+abc123def456` для приватного).
2. Добавьте бота в канал как администратора с правом чтения сообщений.

#### Настройка `targets`
1. **Получение `forum_chat_id`**:
   - Добавьте бота в целевую группу (супергруппу с темами) как администратора с правом отправки сообщений.
   - Используйте [@GetIDsBot](https://t.me/GetIDsBot):
     - Перешлите сообщение из группы в чат с ботом.
     - Получите ID группы (например, `-1001111111111`).
2. **Получение `thread_id`**:
   - Перейдите в нужную тему в группе.
   - Перешлите сообщение из темы в `@GetIDsBot`.
   - Получите ID темы (например, `11`).
3. **Настройка `filters`** (опционально):
   - Укажите фильтры для сообщений:
     - `has_photo`: `true` или `false` (только сообщения с фото).
     - `has_video`: `true` или `false` (только сообщения с видео).
     - `has_document`: `true` или `false` (только сообщения с документами).
     - `keywords`: Список слов для фильтрации текста (например, `["важно", "обновление"]`).

#### Создание `config.json`
Создайте файл `config.json` в директории `volumes/` на хосте (например, `/path/to/tg-bot-channel-to-forum/volumes/config.json`).

**Пример**:
```json
{
  "api_id": 123456,
  "api_hash": "abc123def4567890",
  "bot_token": "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890",
  "source_channel": "https://t.me/your_channel",
  "targets": [
    {
      "forum_chat_id": -1001111111111,
      "thread_id": 11,
      "filters": {
        "has_photo": true,
        "keywords": ["важно", "обновление"]
      }
    },
    {
      "forum_chat_id": -1002222222222,
      "thread_id": 22,
      "filters": {
        "has_video": true
      }
    },
    {
      "forum_chat_id": -1003333333333,
      "thread_id": 33
    }
  ]
}
```

- Убедитесь, что файл имеет корректный JSON-формат.
- Защитите файл: `chmod 600 volumes/config.json`.

### 2. Подготовка окружения
1. Создайте директорию проекта на хосте:
   ```bash
   mkdir -p /path/to/tg-bot-channel-to-forum/volumes/logs
   ```
2. Скопируйте файлы проекта (`bot.py`, `Dockerfile`, `.dockerignore`, `requirements.txt`, `docker-compose.yml`) в `/path/to/tg-bot-channel-to-forum`.
3. Создайте `config.json` в `volumes/` с вашими данными.
4. Убедитесь, что Docker и Portainer установлены:
   ```bash
   docker --version
   docker-compose --version
   ```
   Portainer должен быть доступен через веб-интерфейс (например, `http://<host>:9000`).

### 3. Развертывание через Portainer
1. **Войдите в Portainer** через веб-интерфейс.
2. **Выберите окружение** (локальный Docker или кластер).
3. **Создайте стек (stack)**:
   - Перейдите в **Stacks** → **Add stack**.
   - Задайте имя, например, `tg-bot-channel-to-forum`.
4. **Загрузите `docker-compose.yml`**:
   - В **Web editor** вставьте содержимое `docker-compose.yml`:
     ```yaml
     version: "3.9"
     services:
       tg-forwarder:
         build: .
         container_name: tg-forwarder
         restart: always
         volumes:
           - /path/to/tg-bot-channel-to-forum/volumes:/app/volumes
         environment:
           - PYTHONUNBUFFERED=1
     ```
   - Замените `/path/to/tg-bot-channel-to-forum/volumes` на фактический путь к директории `volumes/` на хосте.
   - Альтернативно, если проект в Git-репозитории:
     - Выберите **Git Repository**.
     - Укажите URL репозитория, путь к `docker-compose.yml` и ветку (`main`).
5. **Разверните стек**:
   - Нажмите **Deploy the stack**.
   - Portainer построит образ и запустит контейнер `tg-forwarder`.

### 4. Проверка работы
1. **Проверьте статус контейнера**:
   - В Portainer перейдите в **Containers** и убедитесь, что `tg-forwarder` в состоянии **Running**.
2. **Просмотрите логи**:
   - В Portainer выберите контейнер → **Logs** или используйте:
     ```bash
     docker logs tg-forwarder
     ```
   - Логи также сохраняются в `/path/to/tg-bot-channel-to-forum/volumes/logs/YYYY-MM-DD.log`.
3. **Проверьте репост**:
   - Опубликуйте сообщение в канале, указанном в `source_channel`.
   - Убедитесь, что оно появляется в целевых форум-чатах (`targets`).

### 5. Автоматическое обновление
Для автоматического обновления используйте `update_bot.sh`:
1. Настройте cron-задачу на хосте:
   ```bash
   crontab -e
   ```
   Добавьте:
   ```bash
   0 3 * * * /bin/bash /path/to/tg-bot-channel-to-forum/update_bot.sh
   ```
2. В Portainer включите **Webhook** для стека:
   - В **Stacks** → `tg-bot-channel-to-forum` включите вебхук.
   - Добавьте в `update_bot.sh` вызов вебхука после `docker-compose up -d`:
     ```bash
     curl -X POST <WEBHOOK_URL> >> "$LOG_FILE" 2>&1
     ```

---

## 🛠 Используемые технологии
- [Python 3.12](https://www.python.org/)
- [Telethon 1.36.0](https://github.com/LonamiWebs/Telethon) — работа с Telegram API
- [Pydantic 2.9.2](https://pypi.org/project/pydantic/) — валидация конфигурации
- Docker & Docker Compose
- Portainer — управление контейнерами

---

## 📜 Лицензия
MIT