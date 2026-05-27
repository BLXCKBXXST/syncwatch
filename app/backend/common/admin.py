from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse

from .models import SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """Singleton-страница глобальных настроек сайта."""

    list_display = ('default_theme', 'updated_at')

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        # Список из одного объекта бесполезен — сразу открываем форму.
        obj = SiteSettings.get_solo()
        return HttpResponseRedirect(
            reverse('admin:common_sitesettings_change', args=[obj.pk])
        )
