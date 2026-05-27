"""Тесты комнат: чистая логика синхронизации, REST и WebSocket-консьюмер."""

from datetime import timedelta

import pytest
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User
from config.asgi import application
from rooms.models import WatchRoom
from rooms.sync import effective_position
from videos.models import Video


# --- Чистая функция синхронизации (ядро ключевой фичи) ----------------------

def test_effective_position_paused_is_frozen():
    now = timezone.now()
    earlier = now - timedelta(seconds=30)
    # На паузе позиция не зависит от прошедшего времени.
    assert effective_position(False, 42.0, earlier, now) == 42.0


def test_effective_position_playing_advances_with_time():
    now = timezone.now()
    started = now - timedelta(seconds=10)
    # За 10 секунд воспроизведения позиция выросла на 10.
    assert effective_position(True, 5.0, started, now) == pytest.approx(15.0, abs=0.01)


def test_effective_position_never_goes_backwards():
    now = timezone.now()
    future = now + timedelta(seconds=5)
    # Рассинхрон часов не должен уводить позицию назад.
    assert effective_position(True, 8.0, future, now) == 8.0


# --- Фикстуры ---------------------------------------------------------------

@pytest.fixture
def host_user():
    return User.objects.create_user(
        username='host', password='hostpass123',
        first_name='Хост', last_name='Ведущий',
    )


@pytest.fixture
def video(host_user, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    return Video.objects.create(
        owner=host_user,
        title='Тестовое видео',
        file=SimpleUploadedFile('v.mp4', b'\x00' * 1024, content_type='video/mp4'),
        size_bytes=1024,
    )


@pytest.fixture
def auth(host_user):
    client = APIClient()
    token = RefreshToken.for_user(host_user).access_token
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return client


# --- REST комнат ------------------------------------------------------------

@pytest.mark.django_db
def test_create_room_requires_authentication(video):
    resp = APIClient().post('/api/rooms/', {'video': str(video.id)}, format='json')
    assert resp.status_code == 401


@pytest.mark.django_db
def test_create_room_returns_room_with_video(auth, video):
    resp = auth.post(
        '/api/rooms/',
        {'video': str(video.id), 'title': 'Смотрим вместе'},
        format='json',
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body['title'] == 'Смотрим вместе'
    assert body['video']['id'] == str(video.id)
    assert body['is_host'] is True
    assert body['participants_count'] == 0


@pytest.mark.django_db
def test_retrieve_room_is_public(auth, video):
    room_id = auth.post('/api/rooms/', {'video': str(video.id)}, format='json').json()['id']
    # Гость без токена открывает комнату по ссылке.
    resp = APIClient().get(f'/api/rooms/{room_id}/')
    assert resp.status_code == 200
    assert resp.json()['is_host'] is False


# --- WebSocket-консьюмер комнаты --------------------------------------------

def _ws_url(room_id, token=None):
    url = f'/ws/rooms/{room_id}/'
    return f'{url}?token={token}' if token else url


async def _make_room(video, host):
    return await database_sync_to_async(WatchRoom.objects.create)(video=video, host=host)


@pytest.mark.django_db(transaction=True)
async def test_room_socket_sends_initial_state(host_user, video):
    room = await _make_room(video, host_user)
    token = str(RefreshToken.for_user(host_user).access_token)
    communicator = WebsocketCommunicator(application, _ws_url(room.id, token))
    connected, _ = await communicator.connect()
    assert connected

    state = await communicator.receive_json_from()
    assert state['type'] == 'room.state'
    assert state['is_playing'] is False
    assert state['position'] == 0.0
    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
async def test_host_play_broadcasts_state(host_user, video):
    room = await _make_room(video, host_user)
    token = str(RefreshToken.for_user(host_user).access_token)
    communicator = WebsocketCommunicator(application, _ws_url(room.id, token))
    await communicator.connect()
    await communicator.receive_json_from()  # начальное room.state
    await communicator.receive_json_from()  # room.participants

    await communicator.send_json_to(
        {'type': 'player.play', 'position': 17.5, 'is_playing': True}
    )
    broadcast = await communicator.receive_json_from()
    assert broadcast['type'] == 'room.state'
    assert broadcast['is_playing'] is True
    assert broadcast['position'] == pytest.approx(17.5, abs=0.5)
    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
async def test_guest_cannot_control_playback(host_user, video):
    room = await _make_room(video, host_user)
    # Гость подключается без токена — он не ведущий.
    communicator = WebsocketCommunicator(application, _ws_url(room.id))
    await communicator.connect()
    await communicator.receive_json_from()  # начальное room.state
    await communicator.receive_json_from()  # room.participants

    await communicator.send_json_to(
        {'type': 'player.play', 'position': 50.0, 'is_playing': True}
    )
    await communicator.send_json_to({'type': 'player.sync_request'})
    state = await communicator.receive_json_from()
    # Команда гостя проигнорирована — комната всё ещё на паузе в начале.
    assert state['is_playing'] is False
    assert state['position'] == 0.0
    await communicator.disconnect()


# --- Внешние видео (yt-dlp) -------------------------------------------------

@pytest.mark.django_db
def test_create_room_requires_video_or_url(auth):
    resp = auth.post('/api/rooms/', {}, format='json')
    assert resp.status_code == 400


@pytest.mark.django_db
def test_create_room_rejects_both_video_and_url(auth, video):
    resp = auth.post(
        '/api/rooms/',
        {'video': str(video.id), 'external_url': 'https://example.com/v'},
        format='json',
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_create_room_rejects_youtube_url(auth):
    resp = auth.post(
        '/api/rooms/',
        {'external_url': 'https://www.youtube.com/watch?v=abc'},
        format='json',
    )
    assert resp.status_code == 400
    assert 'youtube' in resp.content.decode('utf-8').lower()


@pytest.mark.django_db
def test_create_room_with_external_url_uses_resolver(auth, monkeypatch):
    fake = {
        'url': 'https://cdn.example.com/stream.mp4',
        'kind': 'youtube',
        'title': 'Тестовое внешнее видео',
        'duration': 123.4,
        'thumbnail': 'https://example.com/poster.jpg',
    }
    monkeypatch.setattr('rooms.serializers.resolve_external', lambda _url: fake)

    resp = auth.post(
        '/api/rooms/',
        {'external_url': 'https://www.youtube.com/watch?v=abc'},
        format='json',
    )
    assert resp.status_code == 201, resp.content
    body = resp.json()
    assert body['is_external'] is True
    assert body['stream_url'] == fake['url']
    assert body['external_title'] == fake['title']
    assert body['external_thumbnail_url'] == fake['thumbnail']
    assert body['display_title'] == fake['title']


# --- Передача роли ведущего -------------------------------------------------

@pytest.fixture
def viewer_user():
    return User.objects.create_user(username='viewer', password='viewpass123')


@pytest.mark.django_db(transaction=True)
async def test_host_can_transfer_role_to_viewer(host_user, viewer_user, video):
    room = await _make_room(video, host_user)
    host_token = str(RefreshToken.for_user(host_user).access_token)
    viewer_token = str(RefreshToken.for_user(viewer_user).access_token)

    host_comm = WebsocketCommunicator(application, _ws_url(room.id, host_token))
    await host_comm.connect()
    await host_comm.receive_json_from()  # state
    await host_comm.receive_json_from()  # participants

    viewer_comm = WebsocketCommunicator(application, _ws_url(room.id, viewer_token))
    await viewer_comm.connect()
    await viewer_comm.receive_json_from()  # state (initial для зрителя)
    # host получает рассылку нового participants после подключения viewer.
    participants_event = await host_comm.receive_json_from()
    assert participants_event['type'] == 'room.participants'
    viewer_participant = next(
        v for v in participants_event['viewers'] if v['user_id'] == viewer_user.id
    )
    viewer_participant_id = viewer_participant['id']

    # viewer на своей стороне тоже видит participants
    await viewer_comm.receive_json_from()

    # Host передаёт роль
    await host_comm.send_json_to(
        {'type': 'room.transfer_host', 'participant_id': viewer_participant_id}
    )
    # Обе стороны получают новый state и новый participants.
    state_host = await host_comm.receive_json_from()
    assert state_host['type'] == 'room.state'
    assert state_host['host']['id'] == viewer_user.id
    participants_after = await host_comm.receive_json_from()
    new_host_record = next(
        v for v in participants_after['viewers'] if v['user_id'] == viewer_user.id
    )
    assert new_host_record['is_host'] is True

    # В БД отражена смена.
    refreshed = await database_sync_to_async(WatchRoom.objects.get)(pk=room.id)
    assert refreshed.host_id == viewer_user.id

    await viewer_comm.disconnect()
    await host_comm.disconnect()


@pytest.mark.django_db(transaction=True)
async def test_viewer_cannot_transfer_host(host_user, viewer_user, video):
    room = await _make_room(video, host_user)
    host_token = str(RefreshToken.for_user(host_user).access_token)
    viewer_token = str(RefreshToken.for_user(viewer_user).access_token)

    host_comm = WebsocketCommunicator(application, _ws_url(room.id, host_token))
    await host_comm.connect()
    await host_comm.receive_json_from()  # state
    await host_comm.receive_json_from()  # participants
    viewer_comm = WebsocketCommunicator(application, _ws_url(room.id, viewer_token))
    await viewer_comm.connect()
    await viewer_comm.receive_json_from()  # state
    await viewer_comm.receive_json_from()  # participants
    # Стянем из host'а событие о новом подключении viewer'а (нужны id).
    participants_event = await host_comm.receive_json_from()
    host_participant_id = next(
        v for v in participants_event['viewers'] if v['user_id'] == host_user.id
    )['id']

    # viewer пытается «забрать» хоста — команда должна быть проигнорирована.
    await viewer_comm.send_json_to(
        {'type': 'room.transfer_host', 'participant_id': host_participant_id}
    )

    refreshed = await database_sync_to_async(WatchRoom.objects.get)(pk=room.id)
    assert refreshed.host_id == host_user.id

    await viewer_comm.disconnect()
    await host_comm.disconnect()


@pytest.mark.django_db(transaction=True)
async def test_new_host_can_play_after_transfer(host_user, viewer_user, video):
    """После передачи прав новый хост должен мочь стартовать плеер.

    Регрессия: сокеты других участников не пересчитывали self.is_host,
    поэтому новый хост на своём сокете оставался зрителем и его
    player.play игнорировался.
    """
    room = await _make_room(video, host_user)
    host_token = str(RefreshToken.for_user(host_user).access_token)
    viewer_token = str(RefreshToken.for_user(viewer_user).access_token)

    host_comm = WebsocketCommunicator(application, _ws_url(room.id, host_token))
    await host_comm.connect()
    await host_comm.receive_json_from()  # state
    await host_comm.receive_json_from()  # participants

    viewer_comm = WebsocketCommunicator(application, _ws_url(room.id, viewer_token))
    await viewer_comm.connect()
    await viewer_comm.receive_json_from()  # state
    participants_event = await host_comm.receive_json_from()
    viewer_participant_id = next(
        v for v in participants_event['viewers'] if v['user_id'] == viewer_user.id
    )['id']
    await viewer_comm.receive_json_from()  # participants на стороне viewer

    # Хост передаёт роль.
    await host_comm.send_json_to(
        {'type': 'room.transfer_host', 'participant_id': viewer_participant_id}
    )
    # Обе стороны получают новый state (с новым host) и новый participants.
    await host_comm.receive_json_from()    # state
    await host_comm.receive_json_from()    # participants
    await viewer_comm.receive_json_from()  # state — здесь viewer-сокет должен
    await viewer_comm.receive_json_from()  # participants    обновить self.is_host

    # Теперь новый хост (viewer-сокет) пробует включить плеер.
    await viewer_comm.send_json_to(
        {'type': 'player.play', 'position': 5.0, 'is_playing': True}
    )
    # Должен прийти room.state с is_playing=True (рассылка хост-действия).
    msg = await viewer_comm.receive_json_from()
    assert msg['type'] == 'room.state'
    assert msg['is_playing'] is True
    assert msg['position'] == pytest.approx(5.0, abs=0.5)

    await viewer_comm.disconnect()
    await host_comm.disconnect()


@pytest.mark.django_db(transaction=True)
async def test_lone_joiner_becomes_host_when_room_orphaned(host_user, viewer_user, video):
    """Если хост ушёл и в комнате никого нет, следующий вошедший становится хостом."""
    room = await _make_room(video, host_user)
    # Хост подключился и сразу ушёл — комната пустая, host_id остался за ним.
    host_token = str(RefreshToken.for_user(host_user).access_token)
    host_comm = WebsocketCommunicator(application, _ws_url(room.id, host_token))
    await host_comm.connect()
    await host_comm.receive_json_from()
    await host_comm.receive_json_from()
    await host_comm.disconnect()

    # Заходит viewer — должен стать хостом автоматически.
    viewer_token = str(RefreshToken.for_user(viewer_user).access_token)
    viewer_comm = WebsocketCommunicator(application, _ws_url(room.id, viewer_token))
    await viewer_comm.connect()
    state = await viewer_comm.receive_json_from()
    assert state['type'] == 'room.state'
    assert state['host']['id'] == viewer_user.id

    refreshed = await database_sync_to_async(WatchRoom.objects.get)(pk=room.id)
    assert refreshed.host_id == viewer_user.id

    await viewer_comm.disconnect()


@pytest.mark.django_db(transaction=True)
async def test_host_disconnect_auto_handoff(host_user, viewer_user, video):
    room = await _make_room(video, host_user)
    host_token = str(RefreshToken.for_user(host_user).access_token)
    viewer_token = str(RefreshToken.for_user(viewer_user).access_token)

    host_comm = WebsocketCommunicator(application, _ws_url(room.id, host_token))
    await host_comm.connect()
    await host_comm.receive_json_from()
    await host_comm.receive_json_from()

    viewer_comm = WebsocketCommunicator(application, _ws_url(room.id, viewer_token))
    await viewer_comm.connect()
    await viewer_comm.receive_json_from()  # state
    await viewer_comm.receive_json_from()  # participants

    await host_comm.disconnect()

    # На стороне viewer прилетает новый state и новый participants.
    msg = await viewer_comm.receive_json_from()
    # Порядок (state и participants) может варьироваться — читаем оба.
    msgs = [msg, await viewer_comm.receive_json_from()]
    state = next(m for m in msgs if m['type'] == 'room.state')
    assert state['host']['id'] == viewer_user.id

    refreshed = await database_sync_to_async(WatchRoom.objects.get)(pk=room.id)
    assert refreshed.host_id == viewer_user.id

    await viewer_comm.disconnect()
