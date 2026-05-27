"""Проверочный WebSocket-консьюмер (инфра-спайк M0).

Используется только для подтверждения, что связка ASGI + Channels + Daphne
поднимается и WebSocket проходит end-to-end. В рабочем потоке заменяется
консьюмером комнат (rooms.consumers.RoomConsumer).
"""

import json

from channels.generic.websocket import AsyncWebsocketConsumer


class EchoConsumer(AsyncWebsocketConsumer):
    """Принимает сообщение и возвращает его обратно отправителю."""

    async def connect(self):
        await self.accept()
        await self.send(text_data=json.dumps({'type': 'ready', 'detail': 'syncwatch ws'}))

    async def receive(self, text_data=None, bytes_data=None):
        await self.send(text_data=json.dumps({'type': 'echo', 'data': text_data}))
