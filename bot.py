"""
Бот для репоста сообщений из Telegram-канала в форум-чат.
Поддерживает фильтрацию и логирование с названиями, ссылками и версиями модулей.
"""

import json
import os
import subprocess
from typing import Dict, Any, Optional, List
import logging
from logging.handlers import TimedRotatingFileHandler
from telethon import TelegramClient, events
from telethon.tl.custom.message import Message
from telethon.tl.types import Channel, Chat, User
from telethon.errors import ChannelInvalidError, ChannelPrivateError
from pydantic import BaseModel, ValidationError

VOLUME_DIR: str = "volumes"
LOG_DIR: str = os.path.join(VOLUME_DIR, "logs")
CONFIG_PATH: str = os.path.join(VOLUME_DIR, "config.json")
REQUIREMENTS_PATH: str = "requirements.txt"

os.makedirs(LOG_DIR, exist_ok=True)

# Настройка логирования с ротацией по дням, хранение 30 дней
log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
log_file_path = os.path.join(LOG_DIR, "bot.log")

logger = logging.getLogger()
logger.setLevel(logging.INFO)

file_handler = TimedRotatingFileHandler(
    log_file_path, when="midnight", interval=1, backupCount=30, encoding="utf-8"
)
file_handler.setFormatter(log_formatter)
file_handler.suffix = "%Y-%m-%d"

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Определение моделей для валидации конфигурации
class Filter(BaseModel):
    has_photo: Optional[bool] = None
    has_video: Optional[bool] = None
    has_document: Optional[bool] = None
    keywords: Optional[List[str]] = None

class Target(BaseModel):
    forum_chat_id: int
    thread_id: int
    filters: Optional[Filter] = None

class Config(BaseModel):
    api_id: int
    api_hash: str
    bot_token: str
    source_channel: str
    targets: List[Target]

# Загружаем и валидируем конфиг
try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as config_file:
        config_data: Dict[str, Any] = json.load(config_file)
    config: Config = Config.model_validate(config_data)
except FileNotFoundError:
    logger.error(f"Config file not found: {CONFIG_PATH}")
    raise
except ValidationError as e:
    logger.error(f"Invalid config format: {e}")
    raise
except json.JSONDecodeError as e:
    logger.error(f"Invalid JSON in config: {e}")
    raise

api_id: int = config.api_id
api_hash: str = config.api_hash
bot_token: str = config.bot_token
source_channel: str = config.source_channel
targets: List[Target] = config.targets

client: TelegramClient = TelegramClient("bot", api_id, api_hash).start(bot_token=bot_token)

async def get_entity_name_and_link(entity_id: str | int) -> tuple[str, str]:
    """
    Получает название и ссылку на канал, супергруппу или чат.
    """
    try:
        entity = await client.get_entity(entity_id)
        if isinstance(entity, (Channel, Chat)):
            name = entity.title
            link = f"https://t.me/{entity.username}" if hasattr(entity, "username") and entity.username else f"ID: {entity_id}"
        elif isinstance(entity, User):
            name = entity.first_name or "Unknown User"
            link = f"ID: {entity_id}"
        else:
            name = "Unknown"
            link = f"ID: {entity_id}"
        return name, link
    except (ChannelInvalidError, ChannelPrivateError) as e:
        logger.error(f"Cannot access entity {entity_id}: {e}")
        return "Inaccessible", f"ID: {entity_id}"
    except Exception as e:
        logger.error(f"Failed to get entity {entity_id}: {e}")
        return "Unknown", f"ID: {entity_id}"

def check_filters(message: Message, filters: Optional[Filter]) -> bool:
    """
    Проверяет сообщение по заданным фильтрам.
    """
    if not filters:
        return True
    if filters.has_photo and not message.photo:
        return False
    if filters.has_video and not message.video:
        return False
    if filters.has_document and not message.document:
        return False
    if filters.keywords:
        text: str = message.message or ""
        if not any(word.lower() in text.lower() for word in filters.keywords):
            return False
    return True

@client.on(events.NewMessage(chats=source_channel))
async def handler(event: events.NewMessage.Event) -> None:
    """
    Обработчик новых сообщений из источника (канала).
    Пересылает сообщения в темы форума с учетом фильтров.
    """
    logger.info(f"Получено сообщение {event.message.id} в канале {source_channel}")
    for target in targets:
        try:
            if check_filters(event.message, target.filters):
                target_name, target_link = await get_entity_name_and_link(target.forum_chat_id)
                await client.forward_messages(
                    entity=target.forum_chat_id,
                    messages=event.message,
                    message_thread_id=target.thread_id
                )
                logger.info(
                    f"Репост {event.message.id} → {target_name} ({target_link})#{target.thread_id}"
                )
            else:
                logger.info(
                    f"Сообщение {event.message.id} не прошло фильтры для {target.forum_chat_id}#{target.thread_id}"
                )
        except Exception as e:
            target_name, target_link = await get_entity_name_and_link(target.forum_chat_id)
            logger.error(f"{e} → {target_name} ({target_link})")

async def log_installed_modules() -> None:
    """
    Логирует версии установленных модулей из requirements.txt.
    """
    try:
        with open(REQUIREMENTS_PATH, "r", encoding="utf-8") as req_file:
            requirements = [line.strip() for line in req_file if line.strip() and not line.startswith("#")]
        logger.info("Установленные модули из requirements.txt:")
        for req in requirements:
            module_name = req.split("==")[0].split(">=")[0].split("<")[0].strip()
            try:
                result = subprocess.run(
                    ["pip", "show", module_name],
                    capture_output=True,
                    text=True,
                    check=True
                )
                for line in result.stdout.splitlines():
                    if line.startswith("Version:"):
                        version = line.split(": ")[1]
                        logger.info(f"{module_name}: {version}")
                        break
                else:
                    logger.warning(f"Версия для {module_name} не найдена")
            except subprocess.CalledProcessError as e:
                logger.error(f"Не удалось получить информацию о модуле {module_name}: {e}")
    except FileNotFoundError:
        logger.error(f"Файл requirements.txt не найден: {REQUIREMENTS_PATH}")
    except Exception as e:
        logger.error(f"Ошибка при чтении requirements.txt: {e}")

async def main():
    """
    Инициализация бота и логирование информации о канале, целях и модулях.
    """
    await log_installed_modules()
    source_name, source_link = await get_entity_name_and_link(source_channel)
    logger.info(f"✅ Бот запущен и слушает канал: {source_name} ({source_link})")

    for target in targets:
        target_name, target_link = await get_entity_name_and_link(target.forum_chat_id)
        logger.info(f"Цель: {target_name} ({target_link})#{target.thread_id}")

with client:
    client.loop.run_until_complete(main())
    client.run_until_disconnected()
