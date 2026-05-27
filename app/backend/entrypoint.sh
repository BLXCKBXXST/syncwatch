#!/usr/bin/env sh
# Точка входа контейнера бэкенда: миграции, сбор статики, запуск ASGI-сервера.
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Фоновая уборка неактивных гостевых аккаунтов: раз в час. Цикл живёт вместе
# с контейнером; команда идемпотентна, пропуск часа некритичен (окно 24 ч).
python manage.py cleanup_guests || true
(
    while true; do
        sleep 3600
        python manage.py cleanup_guests || true
    done
) &

exec daphne -b 0.0.0.0 -p 8000 config.asgi:application
