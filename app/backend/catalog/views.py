"""HTTP-эндпоинты каталога: список источников, лента, поиск, тайтл, поток."""

from dataclasses import asdict

from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from . import cache as ccache
from . import config_loader
from .errors import (
    ParserUnavailableError,
    StreamUnavailableError,
    TitleNotFoundError,
    UnknownSourceError,
)
from .parsers import all_parsers, get_parser


def _ttl(name: str) -> int:
    return getattr(settings, f'CATALOG_CACHE_{name}_TTL')


def _err(exc: Exception, status: int):
    return Response({'detail': str(exc)}, status=status)


def _safe_call(fn, *, cache_key=None, cache_ttl=None):
    """Обёртка: ловит парсерские ошибки и кеширует успешные результаты."""
    if cache_key is not None:
        cached = ccache.get(cache_key)
        if cached is not None:
            return Response(cached)
    try:
        result = fn()
    except UnknownSourceError as exc:
        return _err(exc, 404)
    except TitleNotFoundError as exc:
        return _err(exc, 404)
    except ParserUnavailableError as exc:
        return _err(exc, 503)
    except StreamUnavailableError as exc:
        return _err(exc, 502)
    except Exception as exc:
        return _err(exc, 500)
    payload = asdict(result) if hasattr(result, '__dataclass_fields__') else result
    if cache_key is not None:
        ccache.set(cache_key, payload, cache_ttl or 60)
    return Response(payload)


@api_view(['GET'])
@permission_classes([AllowAny])
def sources(_request):
    """Список доступных источников каталога."""
    data = []
    for p in all_parsers():
        cfg = config_loader.get(p.id)
        data.append({
            'id': p.id,
            'label': p.label,
            'available': p.available and bool(cfg.base_url) and cfg.is_active,
            'base_url': cfg.base_url,
        })
    return Response({'sources': data})


@api_view(['GET'])
@permission_classes([AllowAny])
def feed(request, source):
    page = max(int(request.query_params.get('page') or 1), 1)
    kind = request.query_params.get('kind') or None
    key = ccache.make_key(source, 'feed', page, kind or 'all')
    return _safe_call(lambda: get_parser(source).feed(page=page, kind=kind),
                      cache_key=key, cache_ttl=_ttl('FEED'))


@api_view(['GET'])
@permission_classes([AllowAny])
def search(request, source):
    query = (request.query_params.get('q') or '').strip()
    page = max(int(request.query_params.get('page') or 1), 1)
    if not query:
        return Response({'detail': 'Параметр q обязателен.'}, status=400)
    key = ccache.make_key(source, 'search', page, query.lower()[:80])
    return _safe_call(lambda: get_parser(source).search(query=query, page=page),
                      cache_key=key, cache_ttl=_ttl('SEARCH'))


@api_view(['GET'])
@permission_classes([AllowAny])
def title(_request, source, external_id):
    key = ccache.make_key(source, 'title', external_id)
    return _safe_call(lambda: get_parser(source).title(external_id),
                      cache_key=key, cache_ttl=_ttl('TITLE'))


@api_view(['GET'])
@permission_classes([AllowAny])
def stream(request, source, external_id):
    season = request.query_params.get('s')
    episode = request.query_params.get('e')
    season_n = int(season) if season and season.isdigit() else None
    episode_n = int(episode) if episode and episode.isdigit() else None
    key = ccache.make_key(source, 'stream', external_id, season_n or 0, episode_n or 0)
    return _safe_call(lambda: get_parser(source).stream(external_id, season_n, episode_n),
                      cache_key=key, cache_ttl=_ttl('STREAM'))
