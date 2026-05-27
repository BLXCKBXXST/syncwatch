"""Кеш каталога. На сервере — Redis (тот же, что для Channels), локально —
in-memory словарь с TTL.

Хранятся pickle-сериализованные DTO; ключи строкой `cat:{source}:{kind}:{params}`.
"""

from __future__ import annotations

import logging
import pickle
import time
from threading import Lock
from typing import Any, Optional

from django.conf import settings

logger = logging.getLogger(__name__)


class _MemoryCache:
    def __init__(self):
        self._data: dict[str, tuple[float, bytes]] = {}
        self._lock = Lock()

    def get(self, key: str) -> Optional[bytes]:
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            expires_at, payload = entry
            if expires_at < time.time():
                del self._data[key]
                return None
            return payload

    def set(self, key: str, value: bytes, ttl: int) -> None:
        with self._lock:
            self._data[key] = (time.time() + ttl, value)


_memory_cache = _MemoryCache()
_redis_client = None
_redis_inited = False


def _get_redis():
    """Лениво подключается к Redis по REDIS_URL. None — если не настроен/недоступен."""
    global _redis_client, _redis_inited
    if _redis_inited:
        return _redis_client
    _redis_inited = True
    url = getattr(settings, 'REDIS_URL', '') or ''
    if not url:
        return None
    try:
        import redis as redis_lib

        client = redis_lib.Redis.from_url(url, socket_connect_timeout=2, socket_timeout=2)
        client.ping()
        _redis_client = client
    except Exception as exc:
        logger.warning('Кеш каталога: Redis недоступен (%s), переключаюсь на in-memory.', exc)
        _redis_client = None
    return _redis_client


def get(key: str) -> Optional[Any]:
    """Возвращает закешированное значение или None."""
    raw = None
    client = _get_redis()
    if client is not None:
        try:
            raw = client.get(key)
        except Exception as exc:
            logger.warning('Redis get %s упал: %s', key, exc)
    if raw is None:
        raw = _memory_cache.get(key)
    if raw is None:
        return None
    try:
        return pickle.loads(raw)
    except Exception:
        return None


def set(key: str, value: Any, ttl: int) -> None:
    """Кладёт значение в кеш на ttl секунд."""
    try:
        payload = pickle.dumps(value)
    except Exception as exc:
        logger.warning('Не сериализуется в кеш %s: %s', key, exc)
        return
    client = _get_redis()
    if client is not None:
        try:
            client.setex(key, ttl, payload)
            return
        except Exception as exc:
            logger.warning('Redis setex %s упал: %s', key, exc)
    _memory_cache.set(key, payload, ttl)


def make_key(*parts: Any) -> str:
    """Собирает ключ кеша: 'cat:kinogo:feed:1:movie'."""
    return 'cat:' + ':'.join(str(p) for p in parts)
