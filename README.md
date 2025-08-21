### Устранение ошибок
Если в логах ошибка `MessageMethods.forward_messages() got an unexpected keyword argument 'message_thread_id'`:
1. Замените в `bot.py` функцию `handler` на:
   ```python
   @client.on(events.NewMessage(chats=source_channel))
   async def handler(event: events.NewMessage.Event) -> None:
       for target in targets:
           try:
               if check_filters(event.message, target.filters):
                   target_name, target_link = await get_entity_name_and_link(target.forum_chat_id)
                   await client.send_message(
                       entity=target.forum_chat_id,
                       message=event.message.message or "",
                       file=event.message.media,
                       message_thread_id=target.thread_id
                   )
                   logger.info(f"Репост {event.message.id} → {target_name} ({target_link})#{target.thread_id}")
           except Exception as e:
               logger.error(f"{e} → {target.forum_chat_id}")
   ```
2. Пересоберите контейнер:
   ```bash
   cd /mnt/configs_containers/tg-bot-channel-to-forum
   docker compose up -d --build
   ```
3. Проверьте логи:
   ```bash
   docker logs tg-forwarder
   ```
4. Проверьте `config.json`:
   ```bash
   python3 -c "import json; json.load(open('/mnt/configs_containers/tg-bot-channel-to-forum/volumes/config.json'))"
   ```
5. Проверьте SELinux:
   ```bash
   getenforce
   sudo setenforce 0
   ```

### Логирование
Логи теперь включают:
- Название и ссылку на канал (`source_channel`) при старте бота.
- Название и ID/ссылку на целевые группы (`forum_chat_id`) при старте и каждом репосте.

Пример логов:
```
2025-08-21 15:00:00,123 [INFO] ✅ Бот запущен и слушает канал: Your Channel Name (https://t.me/your_channel)
2025-08-21 15:00:00,124 [INFO] Цель: Your Forum Name (https://t.me/your_forum)#11
2025-08-21 15:01:10,456 [INFO] Репост 123 → Your Forum Name (https://t.me/your_forum)#11
```