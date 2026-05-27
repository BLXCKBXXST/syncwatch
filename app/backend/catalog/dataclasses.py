"""DTO каталога: парсеры возвращают эти объекты, сериализаторы их преобразуют."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


KIND_MOVIE = 'movie'
KIND_SERIES = 'series'
STREAM_HLS = 'hls'
STREAM_MP4 = 'mp4'


@dataclass
class Title:
    """Карточка фильма/сериала в ленте или поиске."""

    id: str            # внешний ID источника (например, '61813' у kinogo)
    title: str
    year: Optional[int] = None
    kind: str = KIND_MOVIE          # 'movie' | 'series'
    poster: str = ''                # абсолютный URL постера
    rating: Optional[float] = None  # 0..10 / 0..5 в зависимости от источника
    url: str = ''                   # ссылка на страницу источника (debug/«открыть в источнике»)


@dataclass
class Episode:
    number: int
    title: str = ''


@dataclass
class Season:
    number: int
    episodes: list[Episode] = field(default_factory=list)


@dataclass
class TitleDetails(Title):
    """Полная информация о тайтле, нужна на странице просмотра."""

    description: str = ''
    genres: list[str] = field(default_factory=list)
    duration_minutes: Optional[int] = None
    seasons: list[Season] = field(default_factory=list)  # пусто для фильма


@dataclass
class Stream:
    """Готовый URL потока, который проигрывается в <video>."""

    url: str
    kind: str = STREAM_HLS          # 'hls' (m3u8) | 'mp4'
    title: str = ''                 # отображаемое название (фильм или «S1E2 — name»)
    thumbnail: str = ''
    duration: Optional[float] = None


@dataclass
class Page:
    """Страница ленты или поиска."""

    items: list[Title] = field(default_factory=list)
    page: int = 1
    has_next: bool = False
