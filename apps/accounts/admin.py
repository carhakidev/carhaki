from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'is_verified', 'created_at']
    list_filter = ['is_verified', 'is_active']
    search_fields = ['email', 'first_name', 'last_name', 'phone_number']
    ordering = ['-created_at']
    fieldsets = UserAdmin.fieldsets + (
        ('CarHaki Profile', {
            'fields': ('phone_number', 'country', 'account_type', 'is_verified')
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('CarHaki Profile', {
            'fields': ('email', 'first_name', 'last_name', 'phone_number')
        }),
    )
