"""JWT-аутентификация для WebSocket-соединений.

Браузерный WebSocket API не позволяет задавать заголовок Authorization, поэтому
access-токен передаётся query-параметром (?token=...). Гости (без токена)
получают AnonymousUser и допускаются к подключению только для чтения.
"""

from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser


@database_sync_to_async
def _resolve_user(token):
    """Возвращает пользователя по access-токену либо AnonymousUser."""
    from rest_framework_simplejwt.exceptions import TokenError
    from rest_framework_simplejwt.tokens import AccessToken

    user_model = get_user_model()
    try:
        access = AccessToken(token)
        user = user_model.objects.get(id=access['user_id'])
    except (TokenError, KeyError, user_model.DoesNotExist):
        return AnonymousUser()
    return user if user.is_active else AnonymousUser()


class JwtAuthMiddleware(BaseMiddleware):
    """Кладёт пользователя в scope['user'] на основе токена из query-строки."""

    async def __call__(self, scope, receive, send):
        query = parse_qs(scope.get('query_string', b'').decode())
        token = query.get('token', [None])[0]
        scope['user'] = await _resolve_user(token) if token else AnonymousUser()
        return await super().__call__(scope, receive, send)
