#!/usr/bin/python
from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from . import views
from rest_framework.routers import DefaultRouter
from rest_framework.schemas import get_schema_view

app_name = 'game'

router = DefaultRouter()
router.register(r'user', views.UserViewSet)
router.register(r'enemy', views.EnemyViewSet)
router.register(r'item', views.ItemViewSet)
router.register(r'player', views.PlayerViewSet)
router.register(r'board', views.BoardViewSet)
router.register(r'game', views.GameViewSet)
router.register(r'score', views.ScoreViewSet)
router.register(r'mine', views.MineViewSet)
router.register(r'market', views.MarketViewSet)

schema_view = get_schema_view(title='Game')

urlpatterns = [
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'), name='login'),
    url(r'^schema/$', schema_view),
    url(r'^game/now_playing/$', views.now_playing),
    url(r'^', include(router.urls), name='game'),
    url(r'^new/(?P<player_code>[0-9A-Z]{15})/$', views.DungeonMasterView.as_view()),
    url(r'^play/(?P<game_code>[0-9A-Z]{15})/$', views.DungeonMasterView.as_view())
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
