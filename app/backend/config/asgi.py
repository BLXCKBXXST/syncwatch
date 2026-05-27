"""ASGI-точка входа blxck.hub: маршрутизирует HTTP и WebSocket по протоколу."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# HTTP-приложение инициализируется до импорта кода, обращающегося к моделям.
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from channels.security.websocket import AllowedHostsOriginValidator  # noqa: E402

from accounts.ws_auth import JwtAuthMiddleware  # noqa: E402
from config.routing import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    # WebSocket: проверка Origin -> JWT-аутентификация -> маршрутизация по URL.
    'websocket': AllowedHostsOriginValidator(
        JwtAuthMiddleware(URLRouter(websocket_urlpatterns))
    ),
})
