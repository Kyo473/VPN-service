FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    jq curl qrencode systemctl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

ENV PYTHONPATH=/app

RUN pip install --no-cache-dir -r requirements.txt
RUN chmod +x start.sh

CMD ["./start.sh"]
