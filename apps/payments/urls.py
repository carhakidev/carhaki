from django.urls import path
from . import views
from .webhooks import flutterwave_webhook

app_name = 'payments'

urlpatterns = [
    path('checkout/<uuid:pk>/', views.CheckoutView.as_view(), name='checkout'),
    path('success/<uuid:pk>/', views.PaymentSuccessView.as_view(), name='payment_success'),
    path('failed/<uuid:pk>/', views.PaymentFailedView.as_view(), name='payment_failed'),
    path('webhooks/flutterwave/', flutterwave_webhook, name='flw_webhook'),
    path('verify/<str:ref>/', views.VerifyPaymentView.as_view(), name='verify_payment'),
]
