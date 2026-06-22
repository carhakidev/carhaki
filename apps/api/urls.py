from django.urls import path
from apps.api.views.auth import (
    RegisterView, LoginView, LogoutView, RefreshTokenView, MeView
)
from apps.api.views.vehicles import (
    VehiclePreviewView, ReportListView, ReportDetailView, SharedReportView
)
from apps.api.views.orders import (
    OrderCreateView, OrderStatusView, PaymentVerifyView, PaystackWebhookAPIView
)
from apps.api.views.dashboard import DashboardView

urlpatterns = [
    # Auth
    path('auth/register/', RegisterView.as_view(),     name='api_register'),
    path('auth/login/',    LoginView.as_view(),        name='api_login'),
    path('auth/logout/',   LogoutView.as_view(),       name='api_logout'),
    path('auth/refresh/',  RefreshTokenView.as_view(), name='api_refresh'),
    path('auth/me/',       MeView.as_view(),           name='api_me'),

    # Vehicles
    path('vehicles/preview/<str:vin>/', VehiclePreviewView.as_view(), name='api_preview'),

    # Reports
    path('reports/',                    ReportListView.as_view(),   name='api_reports'),
    path('reports/<uuid:pk>/',          ReportDetailView.as_view(), name='api_report_detail'),
    path('reports/shared/<uuid:token>/', SharedReportView.as_view(), name='api_report_shared'),

    # Orders
    path('orders/create/',             OrderCreateView.as_view(),  name='api_order_create'),
    path('orders/<uuid:pk>/status/',   OrderStatusView.as_view(),  name='api_order_status'),

    # Payments
    path('payments/verify/',   PaymentVerifyView.as_view(),      name='api_payment_verify'),
    path('payments/webhook/',  PaystackWebhookAPIView.as_view(), name='api_webhook'),

    # Dashboard
    path('dashboard/', DashboardView.as_view(), name='api_dashboard'),
]
