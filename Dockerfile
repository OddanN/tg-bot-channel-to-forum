FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY bot.py requirements.txt .
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
CMD ["python", "bot.py"]