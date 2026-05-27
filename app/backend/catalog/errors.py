"""Доменные исключения каталога — обрабатываются на уровне DRF-вью."""


class CatalogError(Exception):
    """Базовая ошибка каталога."""


class ParserUnavailableError(CatalogError):
    """Источник недоступен (зеркало упало, бот закрыл API и т.п.)."""


class TitleNotFoundError(CatalogError):
    """Запрошенный тайтл не найден."""


class StreamUnavailableError(CatalogError):
    """Поток не удалось извлечь (плеер сменил формат / запись приватная)."""


class UnknownSourceError(CatalogError):
    """Запрошен источник, для которого не зарегистрирован парсер."""
