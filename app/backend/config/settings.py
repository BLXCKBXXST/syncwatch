"""Настройки Django-проекта.

Конфигурация управляется переменными окружения (django-environ): локально без
переменных используются SQLite и in-memory channel layer, на сервере через .env
подключаются PostgreSQL и Redis. Один и тот же код работает в обоих режимах.
"""

from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Чтение окружения --------------------------------------------------------
env = environ.Env(
    DJANGO_DEBUG=(bool, True),
    DJANGO_ALLOWED_HOSTS=(list, ['*']),
    CORS_ALLOWED_ORIGINS=(list, ['http://localhost:5173', 'http://127.0.0.1:5173']),
    CSRF_TRUSTED_ORIGINS=(list, []),
)
# .env читается, если присутствует рядом с manage.py (на сервере). Локально не обязателен.
_env_file = BASE_DIR / '.env'
if _env_file.exists():
    env.read_env(_env_file)

SECRET_KEY = env('DJANGO_SECRET_KEY', default='django-insecure-dev-key-not-for-production')
DEBUG = env('DJANGO_DEBUG')
ALLOWED_HOSTS = env('DJANGO_ALLOWED_HOSTS')

# --- Приложения --------------------------------------------------------------
INSTALLED_APPS = [
    'daphne',  # ASGI-сервер; должен идти до staticfiles, чтобы runserver работал по ASGI
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Сторонние
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'channels',
    # Приложения проекта
    'common',
    'accounts',
    'videos',
    'rooms',
    'chat',
    'catalog',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Трекинг активности для отсчёта простоя гостевых аккаунтов.
    'accounts.middleware.LastSeenMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# --- База данных -------------------------------------------------------------
# Локально (без DATABASE_URL) — SQLite. На сервере — PostgreSQL через DATABASE_URL.
DATABASES = {
    'default': env.db_url(
        'DATABASE_URL',
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}',
    ),
}

# --- Channels: слой обмена сообщениями ---------------------------------------
# Локально (без REDIS_URL) — in-memory (хватает для одного процесса daphne).
# На сервере — Redis, чтобы несколько процессов видели общие группы комнат.
REDIS_URL = env('REDIS_URL', default='')
if REDIS_URL:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {'hosts': [REDIS_URL]},
        },
    }
else:
    CHANNEL_LAYERS = {
        'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'},
    }

# --- Аутентификация ----------------------------------------------------------
AUTH_USER_MODEL = 'accounts.User'

# Вход по имени пользователя и паролю — проверки пароля при регистрации.
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- DRF и JWT ---------------------------------------------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    'DEFAULT_PAGINATION_CLASS': 'common.pagination.DefaultPagination',
    'PAGE_SIZE': 12,
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# --- CORS --------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env('CORS_ALLOWED_ORIGINS')

# --- CSRF и проксирование за nginx/Caddy -------------------------------------
# При работе за обратным прокси Django должен знать, что снаружи https —
# иначе админка отвергает POST-запросы из-за несовпадения Origin.
CSRF_TRUSTED_ORIGINS = env('CSRF_TRUSTED_ORIGINS')
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

# --- Интернационализация -----------------------------------------------------
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Asia/Novosibirsk'
USE_I18N = True
USE_TZ = True

# --- Статика и медиа ---------------------------------------------------------
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = 'media/'
MEDIA_ROOT = env('MEDIA_ROOT', default=str(BASE_DIR / 'media'))

# Лимит размера загружаемого видео (200 МБ).
MAX_UPLOAD_SIZE = env.int('MAX_UPLOAD_SIZE', default=200 * 1024 * 1024)
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_SIZE
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # выше — во временный файл на диске

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Каталог (poiskkino.dev справочник) --------------------------------------
# Ключ можно задать через env (fallback), но боевая конфигурация — через
# /admin/ → Источники каталога. Получить токен: @poiskkinodev_bot в Telegram.
KINOPOISKDEV_BASE = env('KINOPOISKDEV_BASE', default='https://api.poiskkino.dev')
KINOPOISKDEV_API_KEY = env('KINOPOISKDEV_API_KEY', default='')

# TTL для разных типов запросов к каталогу (секунды).
CATALOG_CACHE_FEED_TTL = env.int('CATALOG_CACHE_FEED_TTL', default=15 * 60)
CATALOG_CACHE_SEARCH_TTL = env.int('CATALOG_CACHE_SEARCH_TTL', default=10 * 60)
CATALOG_CACHE_TITLE_TTL = env.int('CATALOG_CACHE_TITLE_TTL', default=2 * 60 * 60)
CATALOG_CACHE_STREAM_TTL = env.int('CATALOG_CACHE_STREAM_TTL', default=20 * 60)
