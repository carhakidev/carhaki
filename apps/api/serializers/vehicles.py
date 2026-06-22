from rest_framework import serializers
from apps.vehicles.models import VehicleSearch, VehicleReport


class VehiclePreviewSerializer(serializers.Serializer):
    """Free preview data returned before purchase."""
    vin = serializers.CharField()
    make = serializers.CharField()
    model = serializers.CharField()
    year = serializers.IntegerField()
    trim = serializers.CharField(allow_blank=True)
    engine = serializers.CharField(allow_blank=True)
    fuel_type = serializers.CharField(allow_blank=True)
    drive_type = serializers.CharField(allow_blank=True)
    body_type = serializers.CharField(allow_blank=True)
    country_of_manufacture = serializers.CharField(allow_blank=True)
    doors = serializers.IntegerField(allow_null=True)
    identifier_type = serializers.CharField()
    source_country = serializers.CharField()


class VehicleReportSerializer(serializers.ModelSerializer):
    """Full report data for authenticated owner."""
    processed_data = serializers.JSONField()
    search_identifier = serializers.CharField(source='search.identifier', read_only=True)

    class Meta:
        model = VehicleReport
        fields = [
            'id', 'search_identifier', 'report_type', 'status',
            'overall_grade', 'risk_score', 'grade_label', 'grade_colour',
            'processed_data', 'ai_summary', 'share_token', 'is_public',
            'created_at', 'completed_at',
        ]
        read_only_fields = fields


class ReportListSerializer(serializers.ModelSerializer):
    """Lightweight report for dashboard list."""
    search_identifier = serializers.CharField(source='search.identifier', read_only=True)

    class Meta:
        model = VehicleReport
        fields = [
            'id', 'search_identifier', 'report_type', 'status',
            'overall_grade', 'risk_score', 'grade_label', 'grade_colour',
            'created_at', 'completed_at',
        ]
        read_only_fields = fields
