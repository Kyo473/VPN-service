#!/bin/bash

# Запуск FastAPI API на фоне
uvicorn app.api:app --host 0.0.0.0 --port 8000 &

# Запуск Telegram бота
python -m app.bot
