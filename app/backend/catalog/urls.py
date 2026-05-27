"""URL'ы каталога (монтируется в config.urls под /api/catalog/)."""

from django.urls import path

from . import views

urlpatterns = [
    path('sources/', views.sources, name='catalog-sources'),
    path('<str:source>/feed/', views.feed, name='catalog-feed'),
    path('<str:source>/search/', views.search, name='catalog-search'),
    path('<str:source>/title/<str:external_id>/', views.title, name='catalog-title'),
    path('<str:source>/stream/<str:external_id>/', views.stream, name='catalog-stream'),
]
