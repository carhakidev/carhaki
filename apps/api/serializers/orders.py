from rest_framework import serializers
from apps.payments.models import Order
from apps.core.constants import REPORT_PRICE_NGN, BUNDLE_PRICES_NGN
import re


class OrderCreateSerializer(serializers.Serializer):
    """Validate order creation request."""
    vin = serializers.CharField(min_length=17, max_length=17)
    quantity = serializers.ChoiceField(choices=['1', '3', '5'], default='1')

    def validate_vin(self, value):
        value = value.upper().strip()
        if not re.match(r'^[A-HJ-NPR-Z0-9]{17}$', value):
            raise serializers.ValidationError(
                'Invalid VIN format. Must be 17 alphanumeric characters (no I, O, or Q).'
            )
        return value


class OrderSerializer(serializers.ModelSerializer):
    """Order status response."""
    report_id = serializers.UUIDField(source='report.id', read_only=True, allow_null=True)
    report_status = serializers.CharField(source='report.status', read_only=True, allow_null=True)

    class Meta:
        model = Order
        fields = [
            'id', 'report_type', 'amount_ngn', 'quantity',
            'payment_status', 'paystack_reference',
            'created_at', 'paid_at',
            'report_id', 'report_status',
        ]
        read_only_fields = fields
