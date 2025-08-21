<!-- ===================== BADGES ===================== -->

<!-- 1️⃣ GitHub Release и License в одну строку -->
![GitHub release](https://img.shields.io/github/v/release/OddanN/tg-bot-channel-to-forum.svg)
![GitHub license](https://img.shields.io/github/license/OddanN/tg-bot-channel-to-forum.svg)

<!-- 2️⃣ GitHub Actions -->
![Build Status](https://github.com/OddanN/tg-bot-channel-to-forum/actions/workflows/docker.yml/badge.svg)

<!-- 3️⃣ Docker -->
![Docker Pulls](https://img.shields.io/docker/pulls/oddann/tg-bot-channel-to-forum.svg)
![Docker Stars](https://img.shields.io/docker/stars/oddann/tg-bot-channel-to-forum.svg)

<!-- ================================================== -->

# Telegram Bot for Channel-to-Forum Forwarding

Бот для автоматической пересылки или копирования сообщений из Telegram-канала в указанные темы форума в группах. Поддерживает фильтрацию, логирование с названиями групп, тем и версиями модулей. Режим работы (пересылка или копирование) определяется параметром `forward_mode` в `config.json`. Контейнер автоматически собирается и публикуется в Docker Hub с помощью GitHub Actions.

## Требования
- Docker и Docker Compose
- Telegram API: `api_id`, `api_hash`, `bot_token`
- Права администратора для бота в канале и группах
- Утилита `@GetIDsBot` для проверки `chat_id` и `thread_id`

## Установка через Docker Hub
1. **Получите образ из Docker Hub**:
   ```bash
   docker pull oddann/tg-bot-channel-to-forum:latest
   ```

2. **Создайте директорию для конфигурации и логов**:
   ```bash
   mkdir -p /tg-bot-channel-to-forum/volumes
   ```

3. **Создайте `config.json`**:
   Создайте файл `/tg-bot-channel-to-forum/volumes/config.json`:
   ```json
    {
      "api_id": 12345678,
      "api_hash": "c6e41ad633d295c54089d2e606f93d65",
      "bot_token": "123456789:AABBSs7CunHH994ykXS6QQZHtV1C7oJCiWM",
      "source_channel": "https://t.me/<source_channel>",
      "invite_link_to_source_channel": "<invite_link_to_source_channel>",
      "forward_mode": true,
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
   - Параметр `forward_mode`:
     - `true`: Работает только в обычных группах (без топиков). Пересылка сообщений с помощью `forward_messages` (показывает источник как кликабельное название канала).
     - `false`: Копирование сообщений с добавлением строки `📢 <a href="link_to_use">source_name</a>` (HTML-разметка, без предпросмотра).
   Установите права:
   ```bash
   sudo chown root:root /volumes/config.json
   sudo chmod 644 /volumes/config.json
   ```

4. **Создайте `docker-compose.yml`**:
   ```yaml
    services:
      tg-forwarder:
        image: oddann/tg-bot-channel-to-forum:latest
        container_name: tg-forwarder
        restart: always
        volumes:
          - /volumes:/app/volumes
        environment:
          - PYTHONUNBUFFERED=1
   ```
   Сохраните в `docker-compose.yml`:
   ```bash
   sudo chown odan:users /tg-bot-channel-to-forum/docker-compose.yml
   sudo chmod 644 /tg-bot-channel-to-forum/docker-compose.yml
   ```

5. **Запустите контейнер**:
   ```bash
   cd /tg-bot-channel-to-forum
   docker compose up -d
   docker logs tg-forwarder
   ```

## Настройка бота в Telegram
### Создание и настройка бота в BotFather
1. Откройте Telegram, найдите `@BotFather`.
2. Создайте бота:
   - Отправьте `/newbot`.
   - Укажите имя (например, `MyForwarderBot`).
   - Укажите username (например, `@MyForwarderBot`).
   - Сохраните `bot_token` в `config.json`.
3. Настройте параметры:
   - **Group Privacy**: Отключите для получения всех сообщений:
     - `/mybots` → выберите бот → **Bot Settings** → **Group Privacy** → **Disable**.
   - **Allow Groups**: Включено (по умолчанию).
   - **Channel Admin Rights**: Включено (по умолчанию).
   - **Commands** (опционально):
     - `/setcommands` → задайте команды, например:
       ```
       start - Запустить бота
       help - Показать справку
       ```
   - **Inline Mode**: Выключено (не требуется).
4. Безопасность:
   - Храните `bot_token` в `config.json` с правами `chmod 600`.
   - При компрометации токена отзовите: `/mybots` → **Bot Settings** → **Revoke Token**.

### Права бота в группах
Бот должен быть администратором в целевых группах (например, `-1001111111111`, `-1002222222222`):
- **Обязательные права**:
  - **Отправка сообщений (Send Messages)**: Для пересылки или копирования сообщений в темы.
  - **Управление темами (Manage Topics)**: Для работы с темами форума.
- **Опциональные права**: Удаление сообщений, блокировка пользователей, добавление участников (не требуются).
- **Как настроить**:
  1. В группе: **Управление группой** → **Администраторы** → **Добавить администратора**.
  2. Найдите бота (`@YourBotName`), добавьте, включите **Отправка сообщений** и **Управление темами**.
  3. Сохраните.

### Права бота в канале
Бот должен быть администратором в канале (например, `https://t.me/<source_channel>`):
- **Обязательное право**:
  - **Чтение сообщений**: Для получения сообщений для пересылки или копирования.
- **Опциональное право**:
  - **Отправка сообщений (Post Messages)**: Не требуется для текущей функциональности.
- **Как настроить**:
  1. В канале: **Управление каналом** → **Администраторы** → **Добавить администратора**.
  2. Найдите бота (`@YourBotName`), добавьте, убедитесь, что чтение сообщений доступно.
  3. Сохраните.

### Проверка ID групп и тем
- Используйте `@GetIDsBot` для получения:
  - `forum_chat_id` (например, `-1001111111111`, `-1002222222222`).
  - `thread_id` (например, `11055`, `55`).
- Проверьте, что темы включены: **Управление группой** → **Темы** → включите.

## Формат сообщений
- Если `forward_mode: true`:
  - Сообщения **пересылаются** с помощью `forward_messages`.
  - Telegram отображает источник как кликабельное название канала (например, `source_channel_name`).
- Если `forward_mode: false`:
  - Сообщения **копируются** с помощью `send_message` с добавлением строки:
    ```
    📢 <a href="invite_link_to_source_channel">source_channel_name</a>
    ```
    где текст `source_channel_name` — кликабельная ссылка (HTML-разметка, без предпросмотра).

## Логирование
Логи включают:
- Версии модулей из `requirements.txt` при старте.
- Название и ссылку на канал (`source_channel`) при старте с указанием режима (`пересылки` или `копирования`).
- Название, ID/ссылку и название темы для целевых групп (`forum_chat_id`) при старте и каждом действии.
- Информацию о каждом входящем сообщении (пересылка или копирование).

## Устранение ошибок
1. **Сообщение "This chat is not linked to a channel"**:
   - Проверьте, включены ли темы в группе:
     - В Telegram: **Управление группой** → **Темы** → включите опцию "Темы".
   - Убедитесь, что бот добавлен как администратор с правами **Отправка сообщений** и **Управление темами**.
   - (Опционально) Привяжите группу к каналу:
     - **Управление группой** → **Связать канал** → выберите `https://t.me/<source_channel>`.
   - Подтвердите `forum_chat_id` и `thread_id` через `@GetIDsBot`.

2. **Ошибка `Failed to get entity ...: Could not find the input entity`**:
   - Убедитесь, что бот добавлен как администратор в канал и группы.
   - В канале: **Управление каналом** → **Администраторы** → добавьте `@YourBotName` с правом **Чтение сообщений**.
   - В группах: **Управление группой** → **Администраторы** → добавьте `@YourBotName` с правами **Отправка сообщений** и **Управление темами**.
   - Проверьте `forum_chat_id` и `thread_id` через `@GetIDsBot`.
   - Обновите `config.json`:
     ```bash
     sudo nano /tg-bot-channel-to-forum/volumes/config.json
     ```

3. **Проверка прав бота**:
   - Бот должен быть администратором в канале `https://t.me/<source_channel>` с правом **Чтение сообщений**.
   - Бот должен быть администратором в группах `-1001111111111`, `-1002222222222` с правами **Отправка сообщений** и **Управление темами**.
   - Подтвердите `thread_id` через `@GetIDsBot`.

4. **Проверка логов**:
   ```bash
   docker logs tg-forwarder
   ```

5. **Проверка сетевого подключения**:
    ```bash
    ping api.telegram.org
    ```
 
6. **Проверка SELinux**:
    ```bash
    getenforce
    sudo setenforce 0
    ```

## Тестирование
1. **Тест запуска из Docker Hub**:
   - Убедитесь, что `config.json` существует в `/mnt/configs_containers/tg-bot-channel-to-forum/volumes/config.json`.
   - Выполните:
     ```bash
     cd /mnt/configs_containers/tg-bot-channel-to-forum
     docker compose up -d
     docker logs tg-forwarder
     ```
   - Проверьте логи на наличие:
     ```
     2025-08-21 21:00:00,123 [INFO] ✅ Бот запущен и слушает канал: <source_channel_name> (<source_channel>) в режиме пересылки
     ```

2. **Тест функциональности бота**:
   - Убедитесь, что бот добавлен как администратор в канал и группы.
   - Проверьте настройки в `@BotFather`:
     - **Group Privacy**: Отключено.
     - **Allow Groups**: Включено.
     - **Channel Admin Rights**: Включено.
   - Настройте `forward_mode` в `config.json`:
     - Для пересылки: `"forward_mode": true`
     - Для копирования: `"forward_mode": false`
   - Опубликуйте тестовое сообщение в канал `https://t.me/<source_channel>`.
   - Проверьте результат в темах Группах:
   - Проверьте логи:
     ```bash
     docker logs tg-forwarder
     ```

## Развертывание в Portainer
1. **Удалите текущий стек**:
   - В Portainer: **Stacks** → `tg-bot-channel-to-forum` → **Remove**.
2. **Создайте новый стек**:
   - **Stacks** → **Add stack**.
   - Имя: `tg-bot-channel-to-forum`.
   - В **Web editor** вставьте `docker-compose.yml`
   - Нажмите **Deploy the stack**.
3. **Проверьте логи**:
   - **Containers** → `tg-forwarder` → **Logs**.