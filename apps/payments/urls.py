from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('pay/<uuid:order_id>/', views.InitiatePaymentView.as_view(), name='initiate'),
    path('verify/', views.VerifyPaymentView.as_view(), name='verify'),
    path('success/<uuid:pk>/', views.PaymentSuccessView.as_view(), name='payment_success'),
    path('failed/<uuid:pk>/', views.PaymentFailedView.as_view(), name='payment_failed'),
    path('webhooks/paystack/', views.PaystackWebhookView.as_view(), name='paystack_webhook'),
]
