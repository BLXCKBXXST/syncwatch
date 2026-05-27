"""Сериализаторы и payload-функции чата и Q&A.

DRF-сериализаторы используются REST-эндпоинтами истории; payload-функции
строят плоские словари для рассылки по WebSocket.
"""

from rest_framework import serializers

from .models import Answer, ChatMessage, Question


# --- Плоские payload для WebSocket ------------------------------------------

def message_payload(message):
    return {
        'id': str(message.id),
        'display_name': message.display_name,
        'text': message.text,
        'likes_count': message.likes_count,
        'created_at': message.created_at.isoformat(),
    }


def answer_payload(answer):
    return {
        'id': str(answer.id),
        'display_name': answer.display_name,
        'text': answer.text,
        'created_at': answer.created_at.isoformat(),
    }


def question_payload(question, answers=()):
    return {
        'id': str(question.id),
        'display_name': question.display_name,
        'text': question.text,
        'is_answered': question.is_answered,
        'upvotes_count': question.upvotes_count,
        'created_at': question.created_at.isoformat(),
        'answers': [answer_payload(a) for a in answers],
    }


# --- DRF-сериализаторы для REST-истории --------------------------------------

class ChatMessageSerializer(serializers.ModelSerializer):
    liked_by_me = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = ('id', 'display_name', 'text', 'likes_count', 'liked_by_me', 'created_at')

    def get_liked_by_me(self, obj):
        user = self.context['request'].user
        return user.is_authenticated and obj.likes.filter(user=user).exists()


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ('id', 'display_name', 'text', 'created_at')


class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = (
            'id', 'display_name', 'text', 'is_answered',
            'upvotes_count', 'created_at', 'answers',
        )
