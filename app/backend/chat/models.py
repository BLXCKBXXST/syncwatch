"""Модели чата и раздела «Вопрос/ответ» комнаты просмотра."""

from django.conf import settings
from django.db import models

from common.models import TimeStampedModel, UUIDModel
from rooms.models import WatchRoom


class ChatMessage(UUIDModel, TimeStampedModel):
    """Сообщение в живом чате комнаты."""

    room = models.ForeignKey(WatchRoom, on_delete=models.CASCADE, related_name='messages')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_messages'
    )
    # Имя на момент отправки — чтобы история не менялась при смене имени в чате.
    display_name = models.CharField('имя автора', max_length=150)
    text = models.TextField('текст')
    likes_count = models.PositiveIntegerField('лайки', default=0)

    class Meta:
        verbose_name = 'сообщение чата'
        verbose_name_plural = 'сообщения чата'
        ordering = ('created_at',)

    def __str__(self):
        return f'{self.display_name}: {self.text[:40]}'


class MessageLike(TimeStampedModel):
    """Лайк сообщения. Один пользователь — один лайк на сообщение."""

    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='message_likes'
    )

    class Meta:
        verbose_name = 'лайк сообщения'
        verbose_name_plural = 'лайки сообщений'
        constraints = [
            models.UniqueConstraint(fields=['message', 'user'], name='uniq_message_like'),
        ]


class Question(UUIDModel, TimeStampedModel):
    """Вопрос со вкладки «Вопрос/ответ»."""

    room = models.ForeignKey(WatchRoom, on_delete=models.CASCADE, related_name='questions')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='asked_questions'
    )
    display_name = models.CharField('имя автора', max_length=150)
    text = models.TextField('текст вопроса')
    is_answered = models.BooleanField('есть ответ', default=False)
    upvotes_count = models.PositiveIntegerField('голоса', default=0)

    class Meta:
        verbose_name = 'вопрос'
        verbose_name_plural = 'вопросы'
        ordering = ('-upvotes_count', 'created_at')

    def __str__(self):
        return self.text[:50]


class QuestionUpvote(TimeStampedModel):
    """Голос за вопрос. Один пользователь — один голос."""

    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='upvotes')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='question_upvotes'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['question', 'user'], name='uniq_question_upvote'),
        ]


class Answer(UUIDModel, TimeStampedModel):
    """Ответ на вопрос."""

    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='given_answers'
    )
    display_name = models.CharField('имя автора', max_length=150)
    text = models.TextField('текст ответа')

    class Meta:
        verbose_name = 'ответ'
        verbose_name_plural = 'ответы'
        ordering = ('created_at',)

    def __str__(self):
        return f'{self.display_name}: {self.text[:40]}'
