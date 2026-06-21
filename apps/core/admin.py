from django.contrib import admin
from django.utils import timezone
from .models import SiteConfig, APILog, ContactMessage, FAQ, SiteStatistic
from solo.admin import SingletonModelAdmin


@admin.register(SiteConfig)
class SiteConfigAdmin(SingletonModelAdmin):
    pass


@admin.register(APILog)
class APILogAdmin(admin.ModelAdmin):
    list_display = ['provider', 'identifier', 'cost_usd', 'success', 'response_time_ms', 'created_at']
    list_filter = ['provider', 'success']
    search_fields = ['identifier']
    readonly_fields = ['created_at']
    ordering = ['-created_at']


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'status', 'created_at']
    list_filter = ['status', 'subject']
    search_fields = ['name', 'email', 'message']
    readonly_fields = ['created_at']
    actions = ['mark_as_read', 'mark_as_replied']

    def mark_as_read(self, request, queryset):
        queryset.update(status=ContactMessage.READ)
    mark_as_read.short_description = 'Mark selected messages as read'

    def mark_as_replied(self, request, queryset):
        queryset.update(status=ContactMessage.REPLIED, replied_at=timezone.now(), replied_by=request.user)
    mark_as_replied.short_description = 'Mark selected messages as replied'


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question', 'category', 'order', 'is_active', 'updated_at']
    list_filter = ['category', 'is_active']
    search_fields = ['question', 'answer']
    list_editable = ['order', 'is_active']
    ordering = ['category', 'order']


@admin.register(SiteStatistic)
class SiteStatisticAdmin(admin.ModelAdmin):
    list_display = ['stat_key', 'stat_value', 'updated_at']
    readonly_fields = ['updated_at']
