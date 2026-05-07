from django.contrib import admin
from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'report_type', 'amount_ugx', 'payment_method', 'payment_status', 'created_at']
    list_filter = ['payment_status', 'payment_method', 'report_type']
    search_fields = ['user__email', 'flutterwave_ref']
    readonly_fields = ['created_at', 'paid_at']
    ordering = ['-created_at']
