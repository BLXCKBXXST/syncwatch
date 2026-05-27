"""Чтение конфигурации источников каталога с in-memory кешем.

Источники меняются через /admin/ → SourceConfig. Парсер обращается через эту
обёртку и подхватывает изменения в течение 30 секунд без редеплоя.
Если в БД записи нет — используется значение из settings (стартовая конфигурация).
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from threading import Lock
from typing import Optional

from django.conf import settings

_CACHE_TTL_SECONDS = 30


@dataclass(frozen=True)
class SourceSettings:
    base_url: str
    username: str
    password: str
    is_active: bool


_cache: dict[str, tuple[float, SourceSettings]] = {}
_lock = Lock()


def _defaults(source_id: str) -> SourceSettings:
    if source_id == 'kinopoiskdev':
        return SourceSettings(
            base_url=getattr(settings, 'KINOPOISKDEV_BASE', 'https://api.poiskkino.dev').rstrip('/'),
            username='',
            password=getattr(settings, 'KINOPOISKDEV_API_KEY', '') or '',
            is_active=True,
        )
    return SourceSettings(base_url='', username='', password='', is_active=False)


def get(source_id: str) -> SourceSettings:
    """Возвращает текущую настройку источника (с кешем 30 с)."""
    with _lock:
        entry = _cache.get(source_id)
        if entry is not None and entry[0] > time.time():
            return entry[1]

    # SELECT без блокировки кеша.
    config: Optional[SourceSettings] = None
    try:
        from .models import SourceConfig

        row = SourceConfig.objects.filter(source_id=source_id).first()
        if row is not None:
            config = SourceSettings(
                base_url=(row.base_url or '').rstrip('/'),
                username=row.username or '',
                password=row.password or '',
                is_active=row.is_active,
            )
    except Exception:
        # БД ещё не накатилась (тесты до миграций) — отдаём дефолты.
        config = None

    if config is None or not config.base_url:
        config = _defaults(source_id)

    with _lock:
        _cache[source_id] = (time.time() + _CACHE_TTL_SECONDS, config)
    return config


def invalidate(source_id: Optional[str] = None) -> None:
    """Сбрасывает кеш (для тестов и для post_save-сигналов)."""
    with _lock:
        if source_id is None:
            _cache.clear()
        else:
            _cache.pop(source_id, None)
