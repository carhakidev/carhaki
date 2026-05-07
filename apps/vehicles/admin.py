from django.contrib import admin
from .models import VehicleSearch, VehicleReport, RecallAlert


@admin.register(VehicleSearch)
class VehicleSearchAdmin(admin.ModelAdmin):
    list_display = ['identifier', 'identifier_type', 'source_country', 'user', 'created_at']
    list_filter = ['source_country', 'identifier_type']
    search_fields = ['identifier', 'user__email']
    readonly_fields = ['created_at']


@admin.register(VehicleReport)
class VehicleReportAdmin(admin.ModelAdmin):
    list_display = ['search', 'report_type', 'status', 'overall_grade', 'risk_score', 'created_at']
    list_filter = ['status', 'report_type', 'overall_grade']
    search_fields = ['search__identifier', 'user__email']
    readonly_fields = ['share_token', 'created_at', 'completed_at']


@admin.register(RecallAlert)
class RecallAlertAdmin(admin.ModelAdmin):
    list_display = ['vin', 'recall_number', 'component', 'is_open', 'source']
    list_filter = ['is_open', 'source']
    search_fields = ['vin', 'recall_number', 'component']
