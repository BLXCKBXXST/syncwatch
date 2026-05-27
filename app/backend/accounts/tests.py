"""Тесты авторизации: регистрация, вход, гостевые аккаунты, профиль, уборка гостей."""

import os
from datetime import timedelta
from io import StringIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from videos.models import Video

pytestmark = pytest.mark.django_db


@pytest.fixture
def api():
    return APIClient()


# --- Регистрация ------------------------------------------------------------

def test_register_creates_user_and_returns_tokens(api):
    resp = api.post(
        '/api/auth/register/',
        {'username': 'ivan', 'password': 'strong-pass-9'},
        format='json',
    )
    assert resp.status_code == 201
    body = resp.json()
    assert 'access' in body and 'refresh' in body
    assert body['user']['username'] == 'ivan'
    assert body['user']['is_guest'] is False

    user = User.objects.get(username='ivan')
    assert user.has_usable_password()
    assert user.check_password('strong-pass-9')


def test_register_duplicate_username_rejected(api):
    User.objects.create_user(username='ivan', password='strong-pass-9')
    resp = api.post(
        '/api/auth/register/',
        {'username': 'ivan', 'password': 'another-pass-7'},
        format='json',
    )
    assert resp.status_code == 400
    assert 'username' in resp.json()


def test_register_weak_password_rejected(api):
    resp = api.post(
        '/api/auth/register/',
        {'username': 'petya', 'password': '123'},
        format='json',
    )
    assert resp.status_code == 400
    assert 'password' in resp.json()
    assert not User.objects.filter(username='petya').exists()


# --- Вход -------------------------------------------------------------------

def test_login_with_correct_credentials(api):
    User.objects.create_user(username='ivan', password='strong-pass-9')
    resp = api.post(
        '/api/auth/login/',
        {'username': 'ivan', 'password': 'strong-pass-9'},
        format='json',
    )
    assert resp.status_code == 200
    body = resp.json()
    assert 'access' in body and 'refresh' in body
    assert body['user']['username'] == 'ivan'


def test_login_with_wrong_password_rejected(api):
    User.objects.create_user(username='ivan', password='strong-pass-9')
    resp = api.post(
        '/api/auth/login/',
        {'username': 'ivan', 'password': 'wrong-pass-0'},
        format='json',
    )
    assert resp.status_code == 400


def test_login_unknown_username_rejected(api):
    resp = api.post(
        '/api/auth/login/',
        {'username': 'nobody', 'password': 'whatever-pass-1'},
        format='json',
    )
    assert resp.status_code == 400


def test_guest_cannot_login_with_password(api):
    guest = User.objects.create_guest()
    resp = api.post(
        '/api/auth/login/',
        {'username': guest.username, 'password': 'any-pass-here-1'},
        format='json',
    )
    assert resp.status_code == 400


# --- Гостевой вход ----------------------------------------------------------

def test_guest_endpoint_creates_guest(api):
    resp = api.post('/api/auth/guest/')
    assert resp.status_code == 201
    body = resp.json()
    assert 'access' in body and 'refresh' in body
    assert body['user']['is_guest'] is True

    user = User.objects.get(username=body['user']['username'])
    assert user.is_guest
    assert user.username.startswith('guest_')
    assert user.chat_display_name
    assert not user.has_usable_password()


def test_guest_endpoint_creates_unique_accounts(api):
    first = api.post('/api/auth/guest/').json()['user']['username']
    second = api.post('/api/auth/guest/').json()['user']['username']
    assert first != second


# --- Профиль ----------------------------------------------------------------

def test_me_requires_authentication(api):
    assert api.get('/api/auth/me/').status_code == 401


def test_me_returns_and_updates_profile(api):
    tokens = api.post(
        '/api/auth/register/',
        {'username': 'ivan', 'password': 'strong-pass-9'},
        format='json',
    ).json()
    api.credentials(HTTP_AUTHORIZATION='Bearer ' + tokens['access'])

    resp = api.get('/api/auth/me/')
    assert resp.status_code == 200
    assert resp.json()['username'] == 'ivan'

    updated = api.patch('/api/auth/me/', {'chat_display_name': 'Ванёк'}, format='json')
    assert updated.status_code == 200
    assert updated.json()['chat_display_name'] == 'Ванёк'


def test_refresh_issues_new_access_token(api):
    tokens = api.post(
        '/api/auth/register/',
        {'username': 'ivan', 'password': 'strong-pass-9'},
        format='json',
    ).json()
    resp = api.post('/api/auth/refresh/', {'refresh': tokens['refresh']}, format='json')
    assert resp.status_code == 200
    assert 'access' in resp.json()


# --- Уборка неактивных гостевых аккаунтов -----------------------------------

def test_cleanup_removes_stale_guest_with_content(settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    guest = User.objects.create_guest()
    video = Video.objects.create(
        owner=guest,
        title='Гостевое видео',
        file=SimpleUploadedFile('g.mp4', b'\x00' * 64, content_type='video/mp4'),
    )
    file_path = video.file.path
    assert os.path.exists(file_path)
    # Гость не активен 25 часов.
    User.objects.filter(pk=guest.pk).update(last_seen=timezone.now() - timedelta(hours=25))

    call_command('cleanup_guests', stdout=StringIO())

    assert not User.objects.filter(pk=guest.pk).exists()
    assert not Video.objects.filter(pk=video.pk).exists()
    # Файл удалён сигналом pre_delete, а не остался сиротой.
    assert not os.path.exists(file_path)


def test_cleanup_keeps_recent_guest():
    guest = User.objects.create_guest()  # last_seen = сейчас
    call_command('cleanup_guests', stdout=StringIO())
    assert User.objects.filter(pk=guest.pk).exists()


def test_cleanup_never_touches_regular_users():
    user = User.objects.create_user(username='ivan', password='strong-pass-9')
    User.objects.filter(pk=user.pk).update(last_seen=timezone.now() - timedelta(days=30))
    call_command('cleanup_guests', stdout=StringIO())
    assert User.objects.filter(pk=user.pk).exists()


def test_cleanup_dry_run_deletes_nothing():
    guest = User.objects.create_guest()
    User.objects.filter(pk=guest.pk).update(last_seen=timezone.now() - timedelta(hours=25))
    call_command('cleanup_guests', '--dry-run', stdout=StringIO())
    assert User.objects.filter(pk=guest.pk).exists()


# --- Трекинг активности -----------------------------------------------------

def test_authenticated_request_updates_last_seen(api):
    tokens = api.post(
        '/api/auth/register/',
        {'username': 'ivan', 'password': 'strong-pass-9'},
        format='json',
    ).json()
    user = User.objects.get(username='ivan')
    User.objects.filter(pk=user.pk).update(last_seen=timezone.now() - timedelta(hours=1))
    stale = User.objects.get(pk=user.pk).last_seen

    api.credentials(HTTP_AUTHORIZATION='Bearer ' + tokens['access'])
    api.get('/api/auth/me/')

    assert User.objects.get(pk=user.pk).last_seen > stale
