"""Тесты чата и Q&A: WebSocket-консьюмер и REST-история."""

import pytest
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User
from chat.models import ChatMessage
from config.asgi import application
from rooms.models import WatchRoom
from videos.models import Video


@pytest.fixture
def user():
    return User.objects.create_user(
        username='viewer', password='viewerpass123',
        first_name='Нина', last_name='Зрителева',
    )


@pytest.fixture
def video(user, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    return Video.objects.create(
        owner=user,
        title='Видео',
        file=SimpleUploadedFile('v.mp4', b'\x00' * 512, content_type='video/mp4'),
    )


def _ws_url(room_id, token=None):
    url = f'/ws/rooms/{room_id}/'
    return f'{url}?token={token}' if token else url


async def _make_room(video, host):
    return await database_sync_to_async(WatchRoom.objects.create)(video=video, host=host)


async def _drain_join(communicator):
    """Считывает начальные сообщения room.state и room.participants."""
    await communicator.receive_json_from()
    await communicator.receive_json_from()


@pytest.mark.django_db(transaction=True)
async def test_authenticated_user_sends_chat_message(user, video):
    room = await _make_room(video, user)
    token = str(RefreshToken.for_user(user).access_token)
    communicator = WebsocketCommunicator(application, _ws_url(room.id, token))
    await communicator.connect()
    await _drain_join(communicator)

    await communicator.send_json_to({'type': 'chat.message', 'text': 'Всем привет'})
    broadcast = await communicator.receive_json_from()
    assert broadcast['type'] == 'chat.message'
    assert broadcast['message']['text'] == 'Всем привет'
    assert broadcast['message']['display_name'] == 'Нина'
    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
async def test_chat_like_toggles_count(user, video):
    room = await _make_room(video, user)
    token = str(RefreshToken.for_user(user).access_token)
    communicator = WebsocketCommunicator(application, _ws_url(room.id, token))
    await communicator.connect()
    await _drain_join(communicator)

    await communicator.send_json_to({'type': 'chat.message', 'text': 'Сообщение'})
    message = (await communicator.receive_json_from())['message']

    await communicator.send_json_to({'type': 'chat.like', 'message_id': message['id']})
    liked = await communicator.receive_json_from()
    assert liked['type'] == 'chat.like'
    assert liked['likes_count'] == 1

    # Повторный лайк снимает отметку.
    await communicator.send_json_to({'type': 'chat.like', 'message_id': message['id']})
    unliked = await communicator.receive_json_from()
    assert unliked['likes_count'] == 0
    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
async def test_guest_cannot_send_chat_message(user, video):
    room = await _make_room(video, user)
    # Гость подключается без токена.
    communicator = WebsocketCommunicator(application, _ws_url(room.id))
    await communicator.connect()
    await _drain_join(communicator)

    await communicator.send_json_to({'type': 'chat.message', 'text': 'спам'})
    # Дожидаемся обработки: запрос синхронизации гость отправить может.
    await communicator.send_json_to({'type': 'player.sync_request'})
    await communicator.receive_json_from()

    count = await database_sync_to_async(ChatMessage.objects.count)()
    assert count == 0
    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
async def test_qa_question_is_broadcast(user, video):
    room = await _make_room(video, user)
    token = str(RefreshToken.for_user(user).access_token)
    communicator = WebsocketCommunicator(application, _ws_url(room.id, token))
    await communicator.connect()
    await _drain_join(communicator)

    await communicator.send_json_to({'type': 'qa.question', 'text': 'Когда продолжение?'})
    broadcast = await communicator.receive_json_from()
    assert broadcast['type'] == 'qa.question'
    assert broadcast['question']['text'] == 'Когда продолжение?'
    assert broadcast['question']['is_answered'] is False
    await communicator.disconnect()


@pytest.mark.django_db
def test_messages_history_endpoint(user, video):
    room = WatchRoom.objects.create(video=video, host=user)
    ChatMessage.objects.create(
        room=room, author=user, display_name='Нина', text='История чата'
    )
    resp = APIClient().get(f'/api/rooms/{room.id}/messages/')
    assert resp.status_code == 200
    assert resp.json()[0]['text'] == 'История чата'
