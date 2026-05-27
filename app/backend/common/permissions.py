"""Общие классы разрешений DRF."""

from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOwnerOrReadOnly(BasePermission):
    """Изменять объект может только его владелец (поле owner)."""

    message = 'Изменять можно только свой контент.'

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.owner_id == getattr(request.user, 'id', None)
