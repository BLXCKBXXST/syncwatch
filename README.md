# Syncwatch

[English](README.en.md)

Self-hosted видеоплатформа с **синхронными комнатами совместного просмотра** —
загружайте ролики, листайте общую ленту, смотрите в одиночку или зовите друзей
в комнату, где плееры всех участников идут в одну секунду.

![License](https://img.shields.io/badge/License-MIT-yellow)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5-092E20?logo=django&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-8-646CFF?logo=vite&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)

## Скриншоты

| Лента | Просмотр | Комната |
|-------|----------|---------|
| ![Лента](docs/screenshots/home.png) | ![Просмотр](docs/screenshots/watch.png) | ![Комната](docs/screenshots/room.png) |

## Возможности

- Загрузка видео, общая лента с пагинацией.
- Страница видео с плеером (поддерживает HLS) и потоковой отдачей с HTTP Range
  (перемотка и быстрый seek).
- **Синхронные комнаты совместного просмотра**: ведущий управляет плеером,
  плееры зрителей подстраиваются по серверным часам с коррекцией дрейфа,
  ссылка-приглашение, гостевой доступ.
- Живой чат с лайками на сообщениях, вкладка «Вопрос/ответ» с голосами.
- Регистрация и вход по логину/паролю, JWT-сессии; гостевой режим в один клик
  (гостевой аккаунт автоматически удаляется после 24 ч простоя).
- Три встроенные темы (тёмная по умолчанию, ретро СЕАНС, светлая Sonar);
  администратор задаёт дефолтную тему сайта, пользовательский выбор сохраняется
  в `localStorage`.

## Стек

| Слой           | Технологии                                                              |
|----------------|--------------------------------------------------------------------------|
| Бэкенд         | Django 5, Django REST Framework, Channels (WebSocket), Daphne (ASGI)     |
| Реал-тайм      | Redis (channel layer)                                                    |
| База данных    | PostgreSQL (продакшен), SQLite (локальная разработка)                    |
| Авторизация    | JWT (djangorestframework-simplejwt), логин/пароль + гостевой режим       |
| Фронтенд       | React 19, React Router, Vite, axios, hls.js                              |
| Инфраструктура | Docker Compose, nginx (фронтенд), Caddy (TLS на периметре)               |

## Быстрый старт

```bash
docker compose up --build
# → http://localhost:8080
```

Подняв стек, получите PostgreSQL, Redis, Django-бэкенд и React-фронтенд за
nginx — приложение доступно на порту `8080`.

## Локальная разработка

Нативно, без Docker — удобно для итераций по фронтенду и запуска тестов.

```bash
# Бэкенд (SQLite + in-memory channel layer)
cd app/backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/daphne -b 127.0.0.1 -p 8000 config.asgi:application
```

```bash
# Фронтенд (в отдельном терминале)
cd app/frontend
npm install
npm run dev
# → http://localhost:5173
```

## Структура

```
syncwatch/
├── app/
│   ├── backend/        # Django-приложения: accounts, videos, rooms, chat, catalog, common
│   └── frontend/       # React + Vite
├── docker-compose.yml  # Самодостаточный стек
├── deploy.sh           # Идемпотентный деплой на сервер (за Caddy)
├── .env.example        # Шаблон переменных окружения
└── API.md              # Справочник REST + WebSocket API
```

## Конфигурация

Скопируйте `.env.example` в `.env` и заполните. Без `.env` стек запускается
на SQLite и in-memory channel layer — для локальной разработки внешних сервисов
не требуется.

## Тесты

```bash
# Бэкенд
cd app/backend && .venv/bin/python -m pytest

# Фронтенд
cd app/frontend && npm run test
```

## Лицензия

[MIT](LICENSE).
