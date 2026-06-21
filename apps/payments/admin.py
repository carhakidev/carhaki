from django.contrib import admin
from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'report_type', 'amount_ngn', 'payment_status', 'created_at']
    list_filter = ['payment_status', 'report_type']
    search_fields = ['user__email', 'paystack_reference', 'customer_email']
    readonly_fields = ['created_at', 'paid_at', 'paystack_reference', 'paystack_access_code']
    ordering = ['-created_at']
