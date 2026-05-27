"""Маршруты приложения rooms (монтируются под /api/)."""

from rest_framework.routers import DefaultRouter

from .views import WatchRoomViewSet

router = DefaultRouter()
router.register('rooms', WatchRoomViewSet, basename='room')

urlpatterns = router.urls
