"""WebSocket-консьюмер комнаты совместного просмотра.

Один сокет на участника. На этапе M3 обслуживает синхронизацию плеера и список
участников; на M4 расширяется чатом и вкладкой «Вопрос/ответ».

Авторитет состояния плеера — ведущий: команды play/pause/seek принимаются только
от него, остальным рассылается итоговое состояние комнаты.
"""

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.utils import timezone

from .host_transfer import find_handoff_candidate, transfer_host
from .models import RoomParticipant, WatchRoom
from .sync import effective_position


def state_payload(room):
    """Снимок состояния плеера комнаты для отправки клиентам."""
    now = timezone.now()
    position = effective_position(
        room.is_playing, room.playback_position, room.state_updated_at, now
    )
    return {
        'type': 'room.state',
        'is_playing': room.is_playing,
        'position': round(position, 3),
        'server_time': now.timestamp(),
        'host': {'id': room.host_id, 'display_name': room.host.display_name},
    }


class RoomConsumer(AsyncJsonWebsocketConsumer):
    """Сокет одной комнаты. Группа канала — room_<uuid>."""

    HOST_ACTIONS = {'player.play', 'player.pause', 'player.seek'}

    async def connect(self):
        self.room_id = str(self.scope['url_route']['kwargs']['room_id'])
        self.group_name = f'room_{self.room_id}'
        self.user = self.scope['user']
        self.participant_id = None
        self.joined = False

        room = await self._get_room()
        if room is None:
            await self.close()
            return

        self.is_host = self.user.is_authenticated and self.user.id == room.host_id
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        self.joined = True

        await self._join_participant(room)
        # Подключение к комнате — это активность: продлеваем срок жизни аккаунта.
        if self.user.is_authenticated:
            await self._touch_last_seen()
        # Новому участнику — сразу текущее состояние плеера.
        await self.send_json(state_payload(room))
        await self._broadcast_participants()

    async def disconnect(self, code):
        if not getattr(self, 'joined', False):
            return
        await self._leave_participant()
        # Если ведущий покидает комнату — автоматически передаём роль первому
        # по «стажу» из оставшихся подключённых пользователей.
        if self.is_host:
            new_host = await self._auto_handoff_host()
            if new_host is not None:
                self.is_host = False
                room = await self._get_room()
                if room is not None:
                    await self._group_send(state_payload(room))
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        await self._broadcast_participants()

    async def receive_json(self, content, **kwargs):
        message_type = content.get('type')

        # --- Синхронизация плеера ---
        if message_type in self.HOST_ACTIONS:
            # Управлять плеером может только ведущий.
            if self.is_host:
                await self._apply_host_action(message_type, content)
            return
        if message_type == 'player.sync_request':
            room = await self._get_room()
            if room is not None:
                await self.send_json(state_payload(room))
            return

        # --- Передача роли ведущего ---
        if message_type == 'room.transfer_host':
            if self.is_host:
                result = await self._transfer_host(content.get('participant_id'))
                if result is not None:
                    room, new_host_user_id = result
                    # У текущего сокета бывшего хоста снимаем флаг.
                    self.is_host = (self.user.id == new_host_user_id)
                    await self._group_send(state_payload(room))
                    await self._broadcast_participants()
            return

        # --- Чат и Q&A: отправлять может только авторизованный участник ---
        if not self.user.is_authenticated:
            return
        handler = {
            'chat.message': self._handle_chat_message,
            'chat.like': self._handle_chat_like,
            'qa.question': self._handle_question,
            'qa.answer': self._handle_answer,
            'qa.upvote': self._handle_upvote,
        }.get(message_type)
        if handler is not None:
            payload = await handler(content)
            if payload is not None:
                await self._group_send(payload)

    # --- Рассылка по группе комнаты ---
    async def room_broadcast(self, event):
        """Обработчик group_send: пересылает готовый payload клиенту.

        Заодно пересчитывает `self.is_host` по hostу из room.state — без
        этого после передачи прав/auto-handoff новый хост на своём
        сокете остаётся «зрителем» и не может управлять плеером.
        """
        payload = event['payload']
        if payload.get('type') == 'room.state' and self.user.is_authenticated:
            host = payload.get('host') or {}
            host_id = host.get('id')
            if host_id is not None:
                self.is_host = (self.user.id == host_id)
        await self.send_json(payload)

    async def _group_send(self, payload):
        await self.channel_layer.group_send(
            self.group_name, {'type': 'room.broadcast', 'payload': payload}
        )

    async def _apply_host_action(self, message_type, content):
        position = float(content.get('position') or 0.0)
        # Ведущий присылает фактическое состояние; seek не должен снимать паузу.
        is_playing = bool(content.get('is_playing', message_type != 'player.pause'))
        room = await self._update_room_state(position, is_playing)
        await self._group_send(state_payload(room))

    async def _broadcast_participants(self):
        await self._group_send(await self._participants_payload())

    # --- Доступ к БД (синхронный код в отдельном потоке) ---
    @database_sync_to_async
    def _get_room(self):
        return (
            WatchRoom.objects
            .select_related('host')
            .filter(pk=self.room_id, is_active=True)
            .first()
        )

    @database_sync_to_async
    def _touch_last_seen(self):
        """Отмечает активность пользователя (для отсчёта простоя гостей)."""
        from django.contrib.auth import get_user_model

        get_user_model().objects.filter(pk=self.user.id).update(last_seen=timezone.now())

    @database_sync_to_async
    def _update_room_state(self, position, is_playing):
        room = WatchRoom.objects.select_related('host').get(pk=self.room_id)
        room.playback_position = max(0.0, position)
        room.is_playing = is_playing
        room.state_updated_at = timezone.now()
        room.save(
            update_fields=['playback_position', 'is_playing', 'state_updated_at', 'updated_at']
        )
        return room

    @database_sync_to_async
    def _join_participant(self, room):
        role = RoomParticipant.ROLE_HOST if self.is_host else RoomParticipant.ROLE_VIEWER
        if self.user.is_authenticated:
            participant, _ = RoomParticipant.objects.get_or_create(
                room=room, user=self.user, defaults={'role': role}
            )
            participant.role = role
            participant.is_online = True
            participant.left_at = None
            participant.save(update_fields=['role', 'is_online', 'left_at', 'updated_at'])
        else:
            participant = RoomParticipant.objects.create(
                room=room, role=role, is_online=True, guest_label='Гость'
            )
        self.participant_id = participant.pk

        # Если фактический host оффлайн и в комнате нет других подключённых
        # пользователей — авто-передаём роль вошедшему. Иначе комната
        # «зависает» без управления: предыдущий хост ушёл последним,
        # а у новичков нет UI для назначения себя.
        if self.user.is_authenticated and room.host_id != self.user.id:
            has_other_user_online = (
                RoomParticipant.objects
                .filter(room=room, is_online=True, user__isnull=False)
                .exclude(pk=participant.pk)
                .exists()
            )
            if not has_other_user_online:
                transfer_host(room, participant)
                # Обновляем кешированные значения в Python-объекте, чтобы
                # последующий state_payload(room) видел новый host без
                # повторного SELECT'а.
                room.host_id = self.user.id
                room.host = self.user
                self.is_host = True

    @database_sync_to_async
    def _leave_participant(self):
        if self.participant_id is None:
            return
        RoomParticipant.objects.filter(pk=self.participant_id).update(
            is_online=False, left_at=timezone.now()
        )

    @database_sync_to_async
    def _participants_payload(self):
        online = list(
            RoomParticipant.objects
            .filter(room_id=self.room_id, is_online=True)
            .select_related('user', 'room')
            .order_by('joined_at')
        )
        host_user_id = online[0].room.host_id if online else None
        viewers = [
            {
                'id': p.pk,
                'user_id': p.user_id,
                'display_name': p.display_name,
                'is_host': p.user_id is not None and p.user_id == host_user_id,
                'is_guest': p.user_id is None,
                'joined_at': p.joined_at.isoformat(),
            }
            for p in online
        ]
        return {
            'type': 'room.participants',
            'count': len(viewers),
            'viewers': viewers,
        }

    @database_sync_to_async
    def _transfer_host(self, participant_id):
        """Передаёт роль ведущего по запросу действующего хоста.

        Возвращает (room, new_host_user_id) при успехе, None при ошибке —
        ошибка тихо игнорируется (UI откатит локальное состояние).
        """
        if not participant_id:
            return None
        try:
            target = (
                RoomParticipant.objects
                .select_related('user')
                .get(pk=participant_id, room_id=self.room_id, is_online=True)
            )
        except RoomParticipant.DoesNotExist:
            return None
        if not target.user_id or target.user_id == self.user.id:
            return None
        room = WatchRoom.objects.select_related('host').get(pk=self.room_id)
        transfer_host(room, target)
        room.refresh_from_db()
        room.host = target.user  # для безотказного state_payload
        return room, target.user_id

    @database_sync_to_async
    def _auto_handoff_host(self):
        """При выходе хоста — передаёт роль следующему по стажу.

        Возвращает user_id нового хоста или None если кандидата нет.
        """
        room = WatchRoom.objects.select_related('host').filter(pk=self.room_id).first()
        if room is None:
            return None
        leaving_user_id = self.user.id if self.user.is_authenticated else None
        if room.host_id != leaving_user_id:
            return None
        candidate = find_handoff_candidate(room, leaving_user_id)
        if candidate is None:
            # Никого не осталось — ставим плеер на паузу и оставляем host'а
            # за последним держателем (следующий вошедший станет хостом
            # при «реактивации» через UI; либо комната будет молчать).
            room.is_playing = False
            room.state_updated_at = timezone.now()
            room.save(update_fields=['is_playing', 'state_updated_at', 'updated_at'])
            return None
        transfer_host(room, candidate)
        return candidate.user_id

    # --- Чат и Q&A ---
    @database_sync_to_async
    def _handle_chat_message(self, content):
        from chat.models import ChatMessage
        from chat.serializers import message_payload

        text = (content.get('text') or '').strip()[:2000]
        if not text:
            return None
        message = ChatMessage.objects.create(
            room_id=self.room_id,
            author=self.user,
            display_name=self.user.display_name,
            text=text,
        )
        return {'type': 'chat.message', 'message': message_payload(message)}

    @database_sync_to_async
    def _handle_chat_like(self, content):
        from django.db.models import F

        from chat.models import ChatMessage, MessageLike

        message = ChatMessage.objects.filter(
            pk=content.get('message_id'), room_id=self.room_id
        ).first()
        if message is None:
            return None
        like, created = MessageLike.objects.get_or_create(message=message, user=self.user)
        delta = 1
        if not created:
            like.delete()
            delta = -1
        ChatMessage.objects.filter(pk=message.pk).update(likes_count=F('likes_count') + delta)
        message.refresh_from_db(fields=['likes_count'])
        return {
            'type': 'chat.like',
            'message_id': str(message.id),
            'likes_count': message.likes_count,
        }

    @database_sync_to_async
    def _handle_question(self, content):
        from chat.models import Question
        from chat.serializers import question_payload

        text = (content.get('text') or '').strip()[:1000]
        if not text:
            return None
        question = Question.objects.create(
            room_id=self.room_id,
            author=self.user,
            display_name=self.user.display_name,
            text=text,
        )
        return {'type': 'qa.question', 'question': question_payload(question)}

    @database_sync_to_async
    def _handle_answer(self, content):
        from chat.models import Answer, Question
        from chat.serializers import answer_payload

        text = (content.get('text') or '').strip()[:1000]
        question = Question.objects.filter(
            pk=content.get('question_id'), room_id=self.room_id
        ).first()
        if question is None or not text:
            return None
        answer = Answer.objects.create(
            question=question,
            author=self.user,
            display_name=self.user.display_name,
            text=text,
        )
        if not question.is_answered:
            question.is_answered = True
            question.save(update_fields=['is_answered', 'updated_at'])
        return {
            'type': 'qa.answer',
            'question_id': str(question.id),
            'answer': answer_payload(answer),
        }

    @database_sync_to_async
    def _handle_upvote(self, content):
        from django.db.models import F

        from chat.models import Question, QuestionUpvote

        question = Question.objects.filter(
            pk=content.get('question_id'), room_id=self.room_id
        ).first()
        if question is None:
            return None
        upvote, created = QuestionUpvote.objects.get_or_create(
            question=question, user=self.user
        )
        delta = 1
        if not created:
            upvote.delete()
            delta = -1
        Question.objects.filter(pk=question.pk).update(
            upvotes_count=F('upvotes_count') + delta
        )
        question.refresh_from_db(fields=['upvotes_count'])
        return {
            'type': 'qa.upvote',
            'question_id': str(question.id),
            'upvotes_count': question.upvotes_count,
        }
