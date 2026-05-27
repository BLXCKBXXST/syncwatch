"""Парсер kinopoisk.dev — каталог-справочник по poiskkino.devу без потоков.

Неофициальный, но активно поддерживаемый REST API:
https://kinopoiskdev.readme.io/. Аутентификация — заголовок
`X-API-KEY` (бесплатный токен через Telegram-бот @poiskkinodev_bot).

Потоки kinopoisk.dev не отдаёт — `stream()` бросает понятную ошибку,
фронт показывает действия «скопировать название» и «создать сеанс
по ссылке».
"""

from __future__ import annotations

import logging
import threading
from typing import Optional

import httpx

from .. import config_loader
from ..dataclasses import (
    KIND_MOVIE,
    KIND_SERIES,
    Episode,
    Page,
    Season,
    Stream,
    Title,
    TitleDetails,
)
from ..errors import (
    ParserUnavailableError,
    StreamUnavailableError,
    TitleNotFoundError,
)
from .base import CatalogParser

logger = logging.getLogger(__name__)

DEFAULT_BASE = 'https://api.poiskkino.dev'

# poiskkino.dev различает много типов; всё нерекламное мапим в movie/series.
TYPE_MOVIE = {'movie', 'cartoon', 'anime'}
TYPE_SERIES = {'tv-series', 'animated-series', 'tv-show'}


def _kind(kp_type: Optional[str]) -> str:
    if kp_type in TYPE_SERIES:
        return KIND_SERIES
    return KIND_MOVIE


def _poster(item: dict) -> str:
    poster = (item.get('poster') or {}).get('url') or ''
    if not poster:
        poster = (item.get('poster') or {}).get('previewUrl') or ''
    return poster


def _rating(item: dict) -> Optional[float]:
    rating = (item.get('rating') or {}).get('kp')
    if not rating:
        return None
    try:
        v = float(rating)
    except (TypeError, ValueError):
        return None
    return round(v, 1) if v > 0 else None


def _kp_url(item: dict) -> str:
    # У источника теперь нет своей публичной страницы тайтла — оставляем
    # пустую ссылку, чтобы UI не рисовал кнопку «Открыть на …».
    return ''


def _doc_to_title(item: dict) -> Title:
    return Title(
        id=str(item.get('id') or ''),
        title=item.get('name') or item.get('alternativeName') or item.get('enName') or '',
        year=item.get('year'),
        kind=_kind(item.get('type')),
        poster=_poster(item),
        rating=_rating(item),
        url=_kp_url(item),
    )


class KinopoiskDevParser(CatalogParser):
    id = 'kinopoiskdev'
    label = 'poiskkino.dev'

    def __init__(self):
        self._client: Optional[httpx.Client] = None
        self._client_lock = threading.Lock()

    @property
    def available(self) -> bool:
        cfg = config_loader.get(self.id)
        return cfg.is_active and bool(cfg.password)

    @property
    def base(self) -> str:
        cfg = config_loader.get(self.id)
        return (cfg.base_url or DEFAULT_BASE).rstrip('/')

    @property
    def api_key(self) -> str:
        return config_loader.get(self.id).password

    def _get_client(self) -> httpx.Client:
        with self._client_lock:
            if self._client is None:
                self._client = httpx.Client(
                    timeout=10.0,
                    follow_redirects=True,
                    headers={'Accept': 'application/json'},
                )
            return self._client

    def _get(self, path: str, params: Optional[dict] = None) -> dict:
        if not self.api_key:
            raise ParserUnavailableError(
                'poiskkino.dev API-ключ не задан. Возьмите его у @poiskkinodev_bot '
                'в Telegram и добавьте в /admin/ → Источники каталога.'
            )
        url = f'{self.base}{path}'
        try:
            r = self._get_client().get(
                url, params=params or {}, headers={'X-API-KEY': self.api_key}
            )
        except Exception as exc:
            raise ParserUnavailableError(f'poiskkino.dev не отвечает: {exc}') from exc
        if r.status_code == 401 or r.status_code == 403:
            raise ParserUnavailableError(
                f'poiskkino.dev отверг ключ ({r.status_code}) — проверьте API-токен'
            )
        if r.status_code == 404:
            raise TitleNotFoundError('Тайтл не найден в poiskkino.devе')
        if r.status_code == 429:
            raise ParserUnavailableError(
                'Лимит запросов poiskkino.devа исчерпан. Попробуйте позже.'
            )
        if r.status_code >= 400:
            raise ParserUnavailableError(f'poiskkino.dev вернул {r.status_code}')
        return r.json()

    # -- Публичные методы --------------------------------------------------

    def feed(self, page: int = 1, kind: Optional[str] = None) -> Page:
        page = max(1, page)
        kp_type = 'tv-series' if kind == KIND_SERIES else 'movie'
        data = self._get('/v1.4/movie', {
            'type': kp_type,
            'sortField': 'votes.kp',
            'sortType': '-1',
            'page': page,
            'limit': 30,
        })
        items = [_doc_to_title(x) for x in (data.get('docs') or [])]
        return Page(
            items=items,
            page=page,
            has_next=page < int(data.get('pages') or 1),
        )

    def search(self, query: str, page: int = 1) -> Page:
        page = max(1, page)
        data = self._get('/v1.4/movie/search', {
            'query': query,
            'page': page,
            'limit': 30,
        })
        items = [_doc_to_title(x) for x in (data.get('docs') or [])]
        return Page(
            items=items,
            page=page,
            has_next=page < int(data.get('pages') or 1),
        )

    def title(self, external_id: str) -> TitleDetails:
        if not external_id or not external_id.isdigit():
            raise TitleNotFoundError('Неверный идентификатор тайтла')
        data = self._get(f'/v1.4/movie/{external_id}')
        kind = _kind(data.get('type'))
        details = TitleDetails(
            id=external_id,
            title=data.get('name') or data.get('alternativeName') or data.get('enName') or '',
            year=data.get('year'),
            kind=kind,
            poster=_poster(data),
            rating=_rating(data),
            url=_kp_url(data),
            description=data.get('description') or data.get('shortDescription') or '',
            genres=[g.get('name', '') for g in (data.get('genres') or []) if g.get('name')],
            duration_minutes=data.get('movieLength') or None,
            seasons=[],
        )
        if kind == KIND_SERIES:
            details.seasons = self._fetch_seasons(external_id)
        return details

    def _fetch_seasons(self, movie_id: str) -> list[Season]:
        try:
            data = self._get('/v1.4/season', {
                'movieId': movie_id,
                'limit': 50,
                'sortField': 'number',
                'sortType': '1',
            })
        except ParserUnavailableError:
            return []
        seasons: list[Season] = []
        for s in (data.get('docs') or []):
            sn = s.get('number')
            if not isinstance(sn, int) or sn < 1:
                continue
            episodes = []
            for ep in (s.get('episodes') or []):
                en = ep.get('number')
                if not isinstance(en, int) or en < 1:
                    continue
                episodes.append(Episode(number=en, title=ep.get('name') or ''))
            seasons.append(Season(number=sn, episodes=episodes))
        return seasons

    def stream(self, external_id, season=None, episode=None) -> Stream:
        raise StreamUnavailableError(
            'poiskkino.dev — справочник без потоков. Скопируйте название и '
            'создайте «Сеанс по ссылке» с нужного источника.'
        )
