"""REST-эндпоинты истории чата и Q&A.

Живые сообщения, лайки и вопросы идут по WebSocket; REST отдаёт уже накопленную
историю при входе в комнату.
"""

from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from .models import ChatMessage, Question
from .serializers import ChatMessageSerializer, QuestionSerializer


class RoomMessagesView(ListAPIView):
    """История сообщений чата комнаты (по возрастанию времени)."""

    serializer_class = ChatMessageSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        return ChatMessage.objects.filter(
            room_id=self.kwargs['room_id']
        ).prefetch_related('likes')


class RoomQuestionsView(ListAPIView):
    """Вопросы комнаты с вложенными ответами."""

    serializer_class = QuestionSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        return Question.objects.filter(
            room_id=self.kwargs['room_id']
        ).prefetch_related('answers')
