"""Регистрация и доступ к доступным парсерам каталога."""

from __future__ import annotations

from typing import Iterable

from ..errors import UnknownSourceError
from .base import CatalogParser
from .kinopoiskdev import KinopoiskDevParser

_PARSERS: dict[str, CatalogParser] = {
    KinopoiskDevParser.id: KinopoiskDevParser(),
}


def get_parser(source_id: str) -> CatalogParser:
    """Возвращает парсер по id или бросает UnknownSourceError."""
    parser = _PARSERS.get(source_id)
    if parser is None:
        raise UnknownSourceError(f'Источник {source_id!r} не зарегистрирован')
    return parser


def all_parsers() -> Iterable[CatalogParser]:
    return _PARSERS.values()
