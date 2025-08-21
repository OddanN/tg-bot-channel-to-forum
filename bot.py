"""
Бот для репоста сообщений из Telegram-канала в форум-чат.
Поддерживает фильтрацию и логирование сообщений.
"""

import json
import os
from typing import Dict, Any, Optional, List
import logging
from logging.handlers import TimedRotatingFileHandler
from telethon import TelegramClient, events
from telethon.tl.custom.message import Message
from pydantic import BaseModel, ValidationError

VOLUME_DIR: str = "volumes"
LOG_DIR: str = os.path.join(VOLUME_DIR, "logs")
CONFIG_PATH: str = os.path.join(VOLUME_DIR, "config.json")

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

def check_filters(message: Message, filters: Optional[Filter]) -> bool:
    """
    Проверяет сообщение по заданным фильтрам.

    Аргументы:
    message: объект сообщения Telethon
    filters: объект фильтров Pydantic (has_photo, has_video, has_document, keywords)

    Возвращает True, если сообщение проходит фильтры, иначе False.
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
    Пересылает сообщения во все указанные цели с учетом фильтров.
    """
    for target in targets:
        try:
            if check_filters(event.message, target.filters):
                await client.forward_messages(
                    entity=target.forum_chat_id,
                    messages=event.message,
                    message_thread_id=target.thread_id
                )
                logger.info(f"Репост {event.message.id} → {target.forum_chat_id}#{target.thread_id}")
        except Exception as e:
            logger.error(f"{e} → {target.forum_chat_id}")

logger.info("✅ Бот запущен и слушает канал с фильтрацией...")
client.run_until_disconnected()
