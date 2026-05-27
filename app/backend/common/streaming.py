"""Отдача файлов с поддержкой HTTP Range (частичные запросы).

Видеоплеер в браузере перематывает ролик через запросы с заголовком Range.
Эта функция разбирает его и отвечает «206 Partial Content» нужным фрагментом.
В продакшене ту же роль может выполнять nginx/Caddy; здесь — переносимый
вариант на стороне Django, работающий в любом окружении.
"""

import os
import re

from django.http import FileResponse, HttpResponse, StreamingHttpResponse

RANGE_RE = re.compile(r'bytes=(\d*)-(\d*)')
CHUNK_SIZE = 8192


def _file_chunks(path, start, length):
    """Генератор: отдаёт ровно length байт файла начиная со start."""
    with open(path, 'rb') as fh:
        fh.seek(start)
        remaining = length
        while remaining > 0:
            data = fh.read(min(CHUNK_SIZE, remaining))
            if not data:
                break
            remaining -= len(data)
            yield data


def range_file_response(request, path, content_type='application/octet-stream'):
    """Возвращает файл целиком (200) или его фрагмент (206) по заголовку Range."""
    size = os.path.getsize(path)
    match = RANGE_RE.match(request.headers.get('Range', ''))

    # Без Range — отдаём файл целиком.
    if not match:
        response = FileResponse(open(path, 'rb'), content_type=content_type)
        response['Accept-Ranges'] = 'bytes'
        response['Content-Length'] = str(size)
        return response

    start_raw, end_raw = match.groups()
    start = int(start_raw) if start_raw else 0
    end = int(end_raw) if end_raw else size - 1
    end = min(end, size - 1)

    # Некорректный диапазон — 416 Range Not Satisfiable.
    if start > end or start >= size:
        response = HttpResponse(status=416)
        response['Content-Range'] = f'bytes */{size}'
        return response

    length = end - start + 1
    response = StreamingHttpResponse(
        _file_chunks(path, start, length),
        status=206,
        content_type=content_type,
    )
    response['Content-Length'] = str(length)
    response['Content-Range'] = f'bytes {start}-{end}/{size}'
    response['Accept-Ranges'] = 'bytes'
    return response
