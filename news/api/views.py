# news/api/views.py

from django.db.models import Q
from django.contrib.auth import get_user_model

from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS

from news.models import Article, Publisher
from .serializers import (
    ArticleSerializer,
    PublisherSerializer,
    JournalistSerializer,
)
from .permissions import IsAuthorOrReadOnly

User = get_user_model()


class ArticleViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [
        IsAuthenticated,
        IsAuthorOrReadOnly,
    ]
    serializer_class = ArticleSerializer

    def get_queryset(self):
        qs = Article.objects.all()
        if self.request.method in SAFE_METHODS:
            user = self.request.user
            qs = qs.filter(status=Article.STATUS_APPROVED).filter(
                Q(author__in=user.subscriptions_journalists.all()) |
                Q(publisher__in=user.subscriptions_publishers.all())
            )
        return qs.distinct()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class PublisherViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer


class JournalistViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = User.objects.filter(groups__name='Journalist')
    serializer_class = JournalistSerializer
