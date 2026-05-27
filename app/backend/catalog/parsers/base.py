"""Абстрактный парсер каталога. Реализации — в kinogo.py, zona.py."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from ..dataclasses import Page, Stream, TitleDetails


class CatalogParser(ABC):
    """Общий интерфейс источника каталога.

    Каждая реализация задаёт class-level `id` и `label`, и методы
    `feed/search/title/stream`. Они должны быть синхронными (вызываются из
    обычных DRF-вьюх) и кешируются вызывающим кодом, не самим парсером.
    """

    id: str = ''
    label: str = ''
    available: bool = True  # парсер живой; False — у нас есть только заглушка

    @abstractmethod
    def feed(self, page: int = 1, kind: Optional[str] = None) -> Page:
        """Лента (главная страница / новинки)."""

    @abstractmethod
    def search(self, query: str, page: int = 1) -> Page:
        """Поиск по строке."""

    @abstractmethod
    def title(self, external_id: str) -> TitleDetails:
        """Полная информация о тайтле."""

    @abstractmethod
    def stream(
        self,
        external_id: str,
        season: Optional[int] = None,
        episode: Optional[int] = None,
    ) -> Stream:
        """Извлекает прямой URL потока."""
