"""Тесты приложения videos: загрузка, видимость, просмотры, Range-стриминг."""

import os

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User
from videos.models import Video

pytestmark = pytest.mark.django_db


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create_user(
        username='owner', password='ownerpass123',
        first_name='Олег', last_name='Владелец',
    )


@pytest.fixture
def auth(api, user):
    token = RefreshToken.for_user(user).access_token
    api.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return api


def make_video_file(name='clip.mp4', size=2000):
    return SimpleUploadedFile(name, b'\x00' * size, content_type='video/mp4')


def upload(client, title='Видео', is_public=True, size=2000):
    return client.post(
        '/api/videos/',
        {
            'title': title,
            'file': make_video_file(size=size),
            'is_public': str(is_public).lower(),
        },
        format='multipart',
    )


def test_upload_requires_authentication(api):
    resp = api.post(
        '/api/videos/',
        {'title': 'X', 'file': make_video_file()},
        format='multipart',
    )
    assert resp.status_code == 401


def test_authenticated_upload_creates_video(auth, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    resp = upload(auth, title='Лекция 1', size=2000)
    assert resp.status_code == 201
    body = resp.json()
    assert body['title'] == 'Лекция 1'
    assert body['size_bytes'] == 2000
    assert body['stream_url'].endswith('/stream/')
    assert Video.objects.count() == 1


def test_list_returns_only_public_videos(auth, api, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    upload(auth, title='Открытое', is_public=True)
    upload(auth, title='Закрытое', is_public=False)
    resp = api.get('/api/videos/')
    assert resp.status_code == 200
    titles = [v['title'] for v in resp.json()['results']]
    assert titles == ['Открытое']


def test_retrieve_increments_view_counter(auth, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    video_id = upload(auth).json()['id']
    first = auth.get(f'/api/videos/{video_id}/')
    second = auth.get(f'/api/videos/{video_id}/')
    assert first.json()['views_count'] == 1
    assert second.json()['views_count'] == 2


def test_stream_returns_partial_content_for_range(auth, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    video_id = upload(auth, size=1000).json()['id']
    resp = auth.get(f'/api/videos/{video_id}/stream/', HTTP_RANGE='bytes=0-99')
    assert resp.status_code == 206
    assert resp['Content-Range'] == 'bytes 0-99/1000'
    assert resp['Content-Length'] == '100'


def test_stream_returns_full_content_without_range(auth, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    video_id = upload(auth, size=1000).json()['id']
    resp = auth.get(f'/api/videos/{video_id}/stream/')
    assert resp.status_code == 200
    assert resp['Accept-Ranges'] == 'bytes'


def test_non_owner_cannot_delete_video(auth, api, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    video_id = upload(auth).json()['id']
    other = User.objects.create_user(
        username='other', password='otherpass123',
        first_name='Чужой', last_name='Юзер',
    )
    token = RefreshToken.for_user(other).access_token
    api.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    resp = api.delete(f'/api/videos/{video_id}/')
    assert resp.status_code == 403


def test_owner_can_update_metadata(auth, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    video_id = upload(auth).json()['id']
    resp = auth.patch(
        f'/api/videos/{video_id}/',
        {'title': 'Новое название'},
        format='json',
    )
    assert resp.status_code == 200
    assert Video.objects.get(pk=video_id).title == 'Новое название'


def test_mine_returns_only_own_videos(auth, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    upload(auth, title='Моё видео')
    resp = auth.get('/api/videos/mine/')
    assert resp.status_code == 200
    assert resp.json()['count'] == 1


def test_deleting_video_removes_file_from_disk(user, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    video = Video.objects.create(
        owner=user,
        title='Удаляемое',
        file=SimpleUploadedFile('d.mp4', b'\x00' * 128, content_type='video/mp4'),
    )
    path = video.file.path
    assert os.path.exists(path)
    # Сигнал pre_delete должен убрать файл с диска вместе с записью.
    video.delete()
    assert not os.path.exists(path)
