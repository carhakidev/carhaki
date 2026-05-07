from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, DealerProfile


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'account_type', 'is_verified', 'created_at']
    list_filter = ['account_type', 'is_verified', 'is_active']
    search_fields = ['email', 'first_name', 'last_name', 'phone_number']
    ordering = ['-created_at']
    fieldsets = UserAdmin.fieldsets + (
        ('CarHaki Profile', {
            'fields': ('phone_number', 'country', 'account_type', 'is_verified')
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('CarHaki Profile', {
            'fields': ('email', 'first_name', 'last_name', 'phone_number', 'account_type')
        }),
    )


@admin.register(DealerProfile)
class DealerProfileAdmin(admin.ModelAdmin):
    list_display = ['business_name', 'user', 'credit_balance', 'is_approved', 'created_at']
    list_filter = ['is_approved']
    search_fields = ['business_name', 'user__email']
    actions = ['approve_dealers']

    def approve_dealers(self, request, queryset):
        queryset.update(is_approved=True)
    approve_dealers.short_description = 'Approve selected dealers'
