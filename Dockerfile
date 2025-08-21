# Базовый образ Python
FROM python:3.12-slim

# Установка рабочей директории
WORKDIR /app

# Установка tzdata для поддержки таймзон
RUN apt-get update && apt-get install -y tzdata && \
    ln -sf /usr/share/zoneinfo/Europe/Moscow /etc/localtime && \
    echo "Europe/Moscow" > /etc/timezone && \
    apt-get clean

# Копируем requirements.txt и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY bot.py .

# Проверка и создание директории для базы данных
RUN mkdir -p /volumes && chmod 777 /volumes

# Команда для запуска бота
CMD ["python", "bot.py"]