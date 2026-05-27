"""Тесты каталога: API endpoint'ы с мок-парсером + KinopoiskDevParser
через httpx MockTransport."""

import httpx
import pytest
from rest_framework.test import APIClient

from catalog import cache as ccache
from catalog import config_loader
from catalog.config_loader import SourceSettings
from catalog.dataclasses import KIND_MOVIE, KIND_SERIES, Page, Stream, Title, TitleDetails
from catalog.errors import ParserUnavailableError, StreamUnavailableError
from catalog.parsers import _PARSERS
from catalog.parsers.base import CatalogParser
from catalog.parsers.kinopoiskdev import KinopoiskDevParser


SOURCE = 'kinopoiskdev'


class _MockParser(CatalogParser):
    id = SOURCE
    label = 'poiskkino.dev'

    def __init__(self, *, raise_unavail=False):
        self._raise = raise_unavail

    def feed(self, page=1, kind=None):
        if self._raise:
            raise ParserUnavailableError('poiskkino.dev недоступен')
        return Page(
            items=[Title(id='123', title='Тестовый фильм', year=2024, kind=KIND_MOVIE)],
            page=page,
            has_next=False,
        )

    def search(self, query, page=1):
        return Page(
            items=[Title(id='456', title=f'Search {query}', year=2024, kind=KIND_MOVIE)],
            page=page,
        )

    def title(self, external_id):
        return TitleDetails(id=external_id, title='Подробности', year=2024, kind=KIND_MOVIE)

    def stream(self, external_id, season=None, episode=None):
        raise StreamUnavailableError('poiskkino.dev — справочник без потоков')


@pytest.fixture(autouse=True)
def clear_cache():
    ccache._memory_cache._data.clear()
    config_loader.invalidate()
    yield


@pytest.fixture
def mock_parser(monkeypatch):
    parser = _MockParser()
    monkeypatch.setitem(_PARSERS, SOURCE, parser)
    return parser


# --- API endpoints ----------------------------------------------------------

@pytest.mark.django_db
def test_sources_endpoint_lists_kinopoiskdev(mock_parser):
    resp = APIClient().get('/api/catalog/sources/')
    assert resp.status_code == 200
    ids = {s['id'] for s in resp.json()['sources']}
    assert ids == {SOURCE}


@pytest.mark.django_db
def test_feed_returns_titles(mock_parser):
    resp = APIClient().get(f'/api/catalog/{SOURCE}/feed/')
    assert resp.status_code == 200
    body = resp.json()
    assert body['items'][0]['title'] == 'Тестовый фильм'


@pytest.mark.django_db
def test_feed_503_when_parser_unavailable(monkeypatch):
    monkeypatch.setitem(_PARSERS, SOURCE, _MockParser(raise_unavail=True))
    resp = APIClient().get(f'/api/catalog/{SOURCE}/feed/')
    assert resp.status_code == 503


@pytest.mark.django_db
def test_search_requires_q(mock_parser):
    resp = APIClient().get(f'/api/catalog/{SOURCE}/search/')
    assert resp.status_code == 400


@pytest.mark.django_db
def test_search_returns_results(mock_parser):
    resp = APIClient().get(f'/api/catalog/{SOURCE}/search/?q=batman')
    assert resp.status_code == 200
    assert resp.json()['items'][0]['title'] == 'Search batman'


@pytest.mark.django_db
def test_title_returns_details(mock_parser):
    resp = APIClient().get(f'/api/catalog/{SOURCE}/title/777/')
    assert resp.status_code == 200
    assert resp.json()['id'] == '777'


@pytest.mark.django_db
def test_stream_502_for_kinopoisk(mock_parser):
    resp = APIClient().get(f'/api/catalog/{SOURCE}/stream/777/')
    assert resp.status_code == 502


@pytest.mark.django_db
def test_unknown_source_404(mock_parser):
    resp = APIClient().get('/api/catalog/tmdb/feed/')
    assert resp.status_code == 404


# --- KinopoiskDevParser изолированно (через httpx MockTransport) -----------

def _make_parser(monkeypatch, handler, api_key='test-key'):
    monkeypatch.setattr(
        config_loader, 'get',
        lambda _id: SourceSettings(
            base_url='https://api.poiskkino.dev', username='',
            password=api_key, is_active=True,
        ),
    )
    parser = KinopoiskDevParser()
    transport = httpx.MockTransport(handler)
    parser._client = httpx.Client(transport=transport, timeout=5.0)
    return parser


def test_kinopoisk_feed_parses_movies(monkeypatch):
    def handler(request):
        assert request.url.path == '/v1.4/movie'
        assert request.headers['X-API-KEY'] == 'test-key'
        return httpx.Response(200, json={
            'docs': [
                {'id': 535341, 'name': 'Зелёная миля', 'year': 1999,
                 'type': 'movie',
                 'poster': {'url': 'https://kp.ru/p/535341.jpg'},
                 'rating': {'kp': 9.122}},
                {'id': 250227, 'name': 'Сериал', 'year': 2023,
                 'type': 'tv-series', 'poster': {}, 'rating': {'kp': 0}},
            ],
            'pages': 5, 'page': 1,
        })
    parser = _make_parser(monkeypatch, handler)
    page = parser.feed(page=1)
    assert page.has_next is True
    assert len(page.items) == 2
    assert page.items[0].id == '535341'
    assert page.items[0].title == 'Зелёная миля'
    assert page.items[0].rating == 9.1
    assert page.items[0].poster.endswith('535341.jpg')
    assert page.items[1].kind == KIND_SERIES
    assert page.items[1].rating is None


def test_kinopoisk_search(monkeypatch):
    def handler(request):
        assert request.url.path == '/v1.4/movie/search'
        return httpx.Response(200, json={
            'docs': [
                {'id': 1, 'name': 'Зеленый', 'type': 'movie', 'year': 2024,
                 'poster': {}, 'rating': {'kp': 7}},
            ],
            'pages': 1, 'page': 1,
        })
    parser = _make_parser(monkeypatch, handler)
    page = parser.search('зелён', page=1)
    assert page.has_next is False
    assert page.items[0].title == 'Зеленый'


def test_kinopoisk_title_movie(monkeypatch):
    def handler(request):
        assert request.url.path == '/v1.4/movie/535341'
        return httpx.Response(200, json={
            'id': 535341, 'name': 'Зелёная миля', 'year': 1999,
            'type': 'movie', 'movieLength': 189,
            'description': 'Описание',
            'genres': [{'name': 'драма'}, {'name': 'фэнтези'}],
            'poster': {'url': 'p.jpg'},
            'rating': {'kp': 9.1},
        })
    parser = _make_parser(monkeypatch, handler)
    details = parser.title('535341')
    assert details.title == 'Зелёная миля'
    assert details.duration_minutes == 189
    assert 'драма' in details.genres
    assert details.seasons == []


def test_kinopoisk_title_series_with_seasons(monkeypatch):
    def handler(request):
        if request.url.path == '/v1.4/movie/250227':
            return httpx.Response(200, json={
                'id': 250227, 'name': 'Сериал', 'year': 2023,
                'type': 'tv-series',
                'description': 'Про сериал',
                'genres': [], 'poster': {}, 'rating': {'kp': 8},
            })
        if request.url.path == '/v1.4/season':
            assert request.url.params['movieId'] == '250227'
            return httpx.Response(200, json={
                'docs': [
                    {'number': 1, 'episodes': [
                        {'number': 1, 'name': 'Пилот'},
                        {'number': 2, 'name': 'Вторая'},
                    ]},
                    {'number': 0, 'episodes': []},  # «специальные» — отброс
                ],
            })
        return httpx.Response(404)
    parser = _make_parser(monkeypatch, handler)
    details = parser.title('250227')
    assert details.kind == KIND_SERIES
    assert len(details.seasons) == 1
    assert details.seasons[0].number == 1
    assert [ep.title for ep in details.seasons[0].episodes] == ['Пилот', 'Вторая']


def test_kinopoisk_stream_unavailable(monkeypatch):
    def handler(request):
        return httpx.Response(200, json={})
    parser = _make_parser(monkeypatch, handler)
    with pytest.raises(StreamUnavailableError):
        parser.stream('1')


def test_kinopoisk_missing_api_key(monkeypatch):
    monkeypatch.setattr(
        config_loader, 'get',
        lambda _id: SourceSettings(
            base_url='https://api.poiskkino.dev', username='',
            password='', is_active=True,
        ),
    )
    parser = KinopoiskDevParser()
    with pytest.raises(ParserUnavailableError):
        parser.feed()
