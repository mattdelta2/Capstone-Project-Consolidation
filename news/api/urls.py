# news/api/urls.py

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

from .views import ArticleViewSet, PublisherViewSet, JournalistViewSet

router = DefaultRouter()
router.register(r'articles',    ArticleViewSet,    basename='articles')
router.register(r'publishers',  PublisherViewSet,  basename='publishers')
router.register(r'journalists', JournalistViewSet, basename='journalists')

urlpatterns = [
    # → /api/articles/         name='articles-list'  
    # → /api/articles/{pk}/    name='articles-detail'
    path('', include(router.urls)),

    # → /api/article/create/   name='article-create'
    path(
        'article/create/',
        ArticleViewSet.as_view({'post': 'create'}),
        name='article-create'
    ),

    # → /api/article/<pk>/update/  name='article-update'
    path(
        'article/<int:pk>/update/',
        ArticleViewSet.as_view({
            'put':   'update',
            'patch': 'partial_update',
        }),
        name='article-update'
    ),

    # → /api/article/<pk>/delete/  name='article-delete'
    path(
        'article/<int:pk>/delete/',
        ArticleViewSet.as_view({'delete': 'destroy'}),
        name='article-delete'
    ),

    # token‐auth remains
    path('auth/token/', obtain_auth_token, name='token-auth'),
]
