# news/urls.py

from django.urls import path
from .views import (
    ArticleDeleteView,
    ArticleListView,
    ArticleDetailView,
    ArticleCreateView,
    ArticleUpdateView,
    NewsletterListView,
    NewsletterDetailView,
    NewsletterCreateView,
    SubscriptionUpdateView,
    SignupView,
    PendingArticlesListView,
    PendingNewslettersListView,    
    approve_article,
    deny_article,
    approve_newsletter,
    deny_newsletter,
    subscribe_journalist,
    unsubscribe_journalist,
    subscribe_publisher,
    unsubscribe_publisher,
)

app_name = 'news'

urlpatterns = [
    # --- Articles -----------------------------------------------------------
    path('', ArticleListView.as_view(), name='article-list'),
    path('article/create/', ArticleCreateView.as_view(), name='article-create'),
    path('article/<int:pk>/', ArticleDetailView.as_view(), name='article-detail'),
    path('article/<int:pk>/approve/', approve_article, name='article-approve'),
    path('article/<int:pk>/deny/',    deny_article,    name='article-deny'),
    path('article/<int:pk>/edit/',   
         ArticleUpdateView.as_view(), name='article-update'),
    path('article/<int:pk>/delete/', 
         ArticleDeleteView.as_view(), name='article-delete'),

    # --- Reader Subscriptions -----------------------------------------------
    path('subscriptions/', SubscriptionUpdateView.as_view(), name='subscriptions'),

    # --- Sign Up ------------------------------------------------------------
    path('signup/', SignupView.as_view(), name='signup'),

    # --- Editor Dashboards -------------------------------------------------
    path('editor/pending/', 
         PendingArticlesListView.as_view(), name='pending_articles'),
    path('newsletters/pending/', 
         PendingNewslettersListView.as_view(), name='pending_newsletters'),

    # --- Follow / Unfollow Journalists & Publishers ------------------------
    path('subscribe/journalist/<int:pk>/', 
         subscribe_journalist, name='subscribe-journalist'),
    path('unsubscribe/journalist/<int:pk>/', 
         unsubscribe_journalist, name='unsubscribe-journalist'),
    path('subscribe/publisher/<int:pk>/', 
         subscribe_publisher, name='subscribe-publisher'),
    path('unsubscribe/publisher/<int:pk>/', 
         unsubscribe_publisher, name='unsubscribe-publisher'),

    # --- Newsletters --------------------------------------------------------
    path('newsletters/', NewsletterListView.as_view(), name='newsletter-list'),
    path('newsletters/create/', NewsletterCreateView.as_view(), 
         name='newsletter-create'),
    path('newsletters/<int:pk>/', NewsletterDetailView.as_view(), 
         name='newsletter-detail'),
    path('newsletters/<int:pk>/approve/', approve_newsletter, 
         name='newsletter-approve'),
    path('newsletters/<int:pk>/deny/', deny_newsletter, name='newsletter-deny'),

]
