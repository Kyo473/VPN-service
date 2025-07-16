#!/bin/bash
# Запуск API и бота внутри контейнера

uvicorn app.api:app --host 0.0.0.0 --port 8000 &
python3 app/bot.py
