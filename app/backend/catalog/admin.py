from django import forms
from django.contrib import admin

from .models import SourceConfig


class SourceConfigForm(forms.ModelForm):
    password = forms.CharField(
        label='Пароль',
        required=False,
        widget=forms.PasswordInput(render_value=True),
        help_text='Хранится в БД как обычная строка. Использовать одноразовую учётку.',
    )

    class Meta:
        model = SourceConfig
        fields = ('source_id', 'base_url', 'username', 'password', 'is_active', 'notes')


@admin.register(SourceConfig)
class SourceConfigAdmin(admin.ModelAdmin):
    form = SourceConfigForm
    list_display = ('source_id', 'base_url', 'username', 'is_active', 'updated_at')
    list_filter = ('is_active', 'source_id')
    search_fields = ('source_id', 'base_url')
    readonly_fields = ('created_at', 'updated_at')
