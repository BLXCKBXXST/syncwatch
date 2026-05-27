"""Маршруты истории чата и Q&A (монтируются под /api/)."""

from django.urls import path

from .views import RoomMessagesView, RoomQuestionsView

urlpatterns = [
    path('rooms/<uuid:room_id>/messages/', RoomMessagesView.as_view(), name='room-messages'),
    path('rooms/<uuid:room_id>/questions/', RoomQuestionsView.as_view(), name='room-questions'),
]
