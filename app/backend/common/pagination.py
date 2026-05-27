"""Общая постраничная навигация для всех списочных эндпоинтов."""

from rest_framework.pagination import PageNumberPagination


class DefaultPagination(PageNumberPagination):
    """Пагинация по 12 элементов с возможностью переопределить размер через ?page_size."""

    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 60
