from django.urls import path
from apps.api.views.auth import (
    RegisterView, LoginView, LogoutView, RefreshTokenView, MeView
)

urlpatterns = [
    # Auth
    path('auth/register/', RegisterView.as_view(), name='api_register'),
    path('auth/login/',    LoginView.as_view(),    name='api_login'),
    path('auth/logout/',   LogoutView.as_view(),   name='api_logout'),
    path('auth/refresh/',  RefreshTokenView.as_view(), name='api_refresh'),
    path('auth/me/',       MeView.as_view(),       name='api_me'),
]
