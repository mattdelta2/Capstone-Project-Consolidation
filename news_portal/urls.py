# news_portal/urls.py

from django.contrib import admin
from django.urls import path, include, reverse_lazy
from django.contrib.auth.views import LoginView, LogoutView
from news.views import SignupView

urlpatterns = [
    path('admin/', admin.site.urls),

    # User signup
    path('signup/', SignupView.as_view(), name='signup'),

    # Custom auth
    path(
        'login/',
        LoginView.as_view(
            template_name='registration/login.html',
            redirect_authenticated_user=True,
            success_url=reverse_lazy('news:article-list')
        ),
        name='login'
    ),
    path(
        'logout/',
        LogoutView.as_view(next_page='news:article-list'),
        name='logout'
    ),

    # 1) API endpoints (all /api/... → DRF viewsets → 401 if no token)
    path('api/', include(('news.api.urls', 'api'), namespace='api')),

    # 2) HTML app URLs (all /… → your Django CBVs as before)
    path('', include(('news.urls', 'news'), namespace='news')),
]
