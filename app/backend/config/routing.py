"""Маршрутизация WebSocket-соединений."""

from django.urls import path

from common.consumers import EchoConsumer
from rooms.consumers import RoomConsumer

websocket_urlpatterns = [
    # Проверочный сокет инфра-спайка.
    path('ws/echo/', EchoConsumer.as_asgi()),
    # Сокет комнаты совместного просмотра.
    path('ws/rooms/<uuid:room_id>/', RoomConsumer.as_asgi()),
]
