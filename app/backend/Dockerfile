# Backend image — Daphne ASGI server.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# ffmpeg нужен для ffprobe — определения длительности загруженного видео.
# deb.debian.org (Fastly CDN) недоступен с сервера развёртывания — apt берёт
# пакеты с зеркала Яндекса.
RUN { grep -rlZ 'deb.debian.org' /etc/apt/ || true; } \
        | xargs -0 -r sed -i 's|deb.debian.org/debian|mirror.yandex.ru/debian|g' \
    && apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x entrypoint.sh

EXPOSE 8000
CMD ["./entrypoint.sh"]
