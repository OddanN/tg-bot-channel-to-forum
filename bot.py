"""
Бот для репоста сообщений из Telegram-канала в форум-чат.
Поддерживает фильтрацию, логирование с названиями, ссылками, версиями модулей и названиями тем.
Добавляет кликабельную ссылку в формате "📢 <a href='link_to_use'>source_name</a>" без предпросмотра.
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
from telethon.errors import ChannelInvalidError, ChannelPrivateError, MessageIdInvalidError
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
    invite_link_to_source_channel: Optional[str] = None
    targets: List[Target]

# Загружаем и валидируем конфиг
try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as config_file:
        config_data: Dict[str, Any] = json.load(config_file)
    config: Config = Config.model_validate(config_data)
except FileNotFoundError as exc_config:
    logger.error(f"Config file not found: {CONFIG_PATH}")
    raise
except ValidationError as exc_validation:
    logger.error(f"Invalid config format: {exc_validation}")
    raise
except json.JSONDecodeError as exc_json:
    logger.error(f"Invalid JSON in config: {exc_json}")
    raise

api_id: int = config.api_id
api_hash: str = config.api_hash
bot_token: str = config.bot_token
source_channel: str = config.source_channel
invite_link: Optional[str] = config.invite_link_to_source_channel
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
    except (ChannelInvalidError, ChannelPrivateError) as exc_entity_access:
        logger.error(f"Cannot access entity {entity_id}: {exc_entity_access}")
        return "Inaccessible", f"ID: {entity_id}"
    except Exception as exc_entity:
        logger.error(f"Failed to get entity {entity_id}: {exc_entity}")
        return "Unknown", f"ID: {entity_id}"

async def get_topic_name(forum_chat_id: int, thread_id: int) -> str:
    """
    Получает название темы форума по forum_chat_id и thread_id.
    """
    try:
        message = await client.get_messages(forum_chat_id, ids=thread_id)
        if message and message.message:
            return message.message[:50] + ("..." if len(message.message) > 50 else "")
        return f"Topic #{thread_id}"
    except MessageIdInvalidError as exc_topic_invalid:
        logger.error(f"Invalid thread_id {thread_id} for forum_chat_id {forum_chat_id}: {exc_topic_invalid}")
        return f"Topic #{thread_id}"
    except Exception as exc_topic:
        logger.error(f"Failed to get topic name for thread_id {thread_id} in {forum_chat_id}: {exc_topic}")
        return f"Topic #{thread_id}"

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
    Отправляет сообщения в темы форума с учетом фильтров и добавляет "📢 <a href='link_to_use'>source_name</a>" без предпросмотра.
    """
    logger.info(f"Получено сообщение {event.message.id} в канале {source_channel}")
    source_name, source_link = await get_entity_name_and_link(source_channel)
    link_to_use = invite_link if invite_link else source_link
    message_text = event.message.message or ""
    message_text = f'{message_text}\n\n📢 <a href="{link_to_use}">{source_name}</a>' if message_text else f'📢 <a href="{link_to_use}">{source_name}</a>'

    for target in targets:
        try:
            if check_filters(event.message, target.filters):
                target_name, target_link = await get_entity_name_and_link(target.forum_chat_id)
                topic_name = await get_topic_name(target.forum_chat_id, target.thread_id)
                await client.send_message(
                    entity=target.forum_chat_id,
                    message=message_text,
                    file=event.message.media,
                    reply_to=target.thread_id,
                    link_preview=False,
                    parse_mode="HTML"
                )
                logger.info(
                    f"Репост {event.message.id} → {target_name} ({target_link}, {topic_name})"
                )
            else:
                topic_name = await get_topic_name(target.forum_chat_id, target.thread_id)
                logger.info(
                    f"Сообщение {event.message.id} не прошло фильтры для {target.forum_chat_id} ({topic_name})"
                )
        except Exception as exc_handler:
            target_name, target_link = await get_entity_name_and_link(target.forum_chat_id)
            topic_name = await get_topic_name(target.forum_chat_id, target.thread_id)
            logger.error(f"{exc_handler} → {target_name} ({target_link}, {topic_name})")

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
            except subprocess.CalledProcessError as exc_module:
                logger.error(f"Не удалось получить информацию о модуле {module_name}: {exc_module}")
    except FileNotFoundError:
        logger.error(f"Файл requirements.txt не найден: {REQUIREMENTS_PATH}")
    except Exception as exc_modules:
        logger.error(f"Ошибка при чтении requirements.txt: {exc_modules}")

async def main():
    """
    Инициализация бота и логирование информации о канале, целях, модулях и темах.
    """
    await log_installed_modules()
    source_name, source_link = await get_entity_name_and_link(source_channel)
    logger.info(f"✅ Бот запущен и слушает канал: {source_name} ({source_link})")

    for target in targets:
        target_name, target_link = await get_entity_name_and_link(target.forum_chat_id)
        topic_name = await get_topic_name(target.forum_chat_id, target.thread_id)
        logger.info(f"Цель: {target_name} ({target_link}, {topic_name})")

with client:
    client.loop.run_until_complete(main())
    client.run_until_disconnected()
