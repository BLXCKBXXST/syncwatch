"""Передача роли ведущего в комнате.

Общая логика для HTTP-вьюхи и WebSocket-консьюмера: атомарная смена
`Room.host` и обновление `RoomParticipant.role` у обоих участников.
"""

from django.db import transaction

from .models import RoomParticipant, WatchRoom


@transaction.atomic
def transfer_host(room: WatchRoom, new_host_participant: RoomParticipant) -> None:
    """Делает участника ведущим. Старый получает роль зрителя.

    Предполагается, что вызывающая сторона уже проверила:
      - инициатор имеет право (текущий хост или auto-handoff после disconnect);
      - new_host_participant.user_id заполнен (гость не может быть хостом);
      - new_host_participant.is_online == True.
    """
    if not new_host_participant.user_id:
        raise ValueError('Гостю нельзя передать роль ведущего')

    old_host_user_id = room.host_id

    # Запись зрителя для бывшего хоста — может отсутствовать, если он
    # был хостом «номинально» без подключения. Берём по user, не по pk.
    RoomParticipant.objects.filter(
        room=room, user_id=old_host_user_id
    ).update(role=RoomParticipant.ROLE_VIEWER)

    new_host_participant.role = RoomParticipant.ROLE_HOST
    new_host_participant.save(update_fields=['role', 'updated_at'])

    room.host_id = new_host_participant.user_id
    room.save(update_fields=['host', 'updated_at'])


def find_handoff_candidate(room: WatchRoom, leaving_user_id) -> RoomParticipant | None:
    """Возвращает следующего по `joined_at` онлайн-участника-не-гостя.

    Используется при выходе ведущего: первый из оставшихся подключённых
    пользователей становится новым хостом. Гости отсекаются — они не могут
    управлять плеером.
    """
    qs = (
        RoomParticipant.objects
        .select_related('user')
        .filter(room=room, is_online=True, user__isnull=False)
        .exclude(user_id=leaving_user_id)
        .order_by('joined_at')
    )
    return qs.first()
