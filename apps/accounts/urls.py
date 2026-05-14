"""
accounts/urls.py
"""

from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/',                           views.RegisterView.as_view(),               name='register'),
    path('login/',                              views.LoginView.as_view(),                  name='login'),
    path('logout/',                             views.LogoutView.as_view(),                 name='logout'),
    path('dashboard/',                          views.DashboardView.as_view(),              name='dashboard'),
    path('profile/',                            views.ProfileView.as_view(),                name='profile'),

    # *** FIX APPLIED ***
    # Added missing change_password URL — referenced in dashboard.html as
    # {% url 'accounts:change_password' %} but was missing from urlpatterns.
    path('password-change/',
         views.PasswordChangeView.as_view(),
         name='change_password'),
    path('password-change/done/',
         views.PasswordChangeDoneView.as_view(),
         name='password_change_done'),

    path('dealers/register/',                   views.DealerRegisterView.as_view(),         name='dealer_register'),
    path('dealers/dashboard/',                  views.DealerDashboardView.as_view(),        name='dealer_dashboard'),

    # Password reset flow
    path('password-reset/',
         views.PasswordResetView.as_view(),
         name='password_reset'),
    path('password-reset/done/',
         views.PasswordResetDoneView.as_view(),
         name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/',
         views.PasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),
    path('password-reset/complete/',
         views.PasswordResetCompleteView.as_view(),
         name='password_reset_complete'),
]