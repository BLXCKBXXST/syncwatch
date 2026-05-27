"""DRF-сериализаторы для DTO каталога (преобразуют dataclass'ы в JSON)."""

from dataclasses import asdict

from rest_framework import serializers


class TitleSerializer(serializers.Serializer):
    id = serializers.CharField()
    title = serializers.CharField()
    year = serializers.IntegerField(allow_null=True)
    kind = serializers.CharField()
    poster = serializers.CharField(allow_blank=True)
    rating = serializers.FloatField(allow_null=True)
    url = serializers.CharField(allow_blank=True)


class EpisodeSerializer(serializers.Serializer):
    number = serializers.IntegerField()
    title = serializers.CharField(allow_blank=True)


class SeasonSerializer(serializers.Serializer):
    number = serializers.IntegerField()
    episodes = EpisodeSerializer(many=True)


class TitleDetailsSerializer(TitleSerializer):
    description = serializers.CharField(allow_blank=True)
    genres = serializers.ListField(child=serializers.CharField())
    duration_minutes = serializers.IntegerField(allow_null=True)
    seasons = SeasonSerializer(many=True)


class StreamSerializer(serializers.Serializer):
    url = serializers.CharField()
    kind = serializers.CharField()
    title = serializers.CharField(allow_blank=True)
    thumbnail = serializers.CharField(allow_blank=True)
    duration = serializers.FloatField(allow_null=True)


class PageSerializer(serializers.Serializer):
    items = TitleSerializer(many=True)
    page = serializers.IntegerField()
    has_next = serializers.BooleanField()


def serialize(obj) -> dict:
    """Универсальный шорткат: dataclass → dict."""
    return asdict(obj)
