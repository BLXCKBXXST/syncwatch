"""Корневая маршрутизация HTTP-запросов."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from common.views import health, site_settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health),
    path('api/site-settings/', site_settings),
    path('api/auth/', include('accounts.urls')),
    path('api/', include('videos.urls')),
    path('api/', include('rooms.urls')),
    path('api/', include('chat.urls')),
    path('api/catalog/', include('catalog.urls')),
]

# В режиме разработки Django сам отдаёт медиафайлы; на сервере это делает Caddy.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
