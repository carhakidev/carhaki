import uuid
from django.db import models
from django.conf import settings


class Order(models.Model):
    BASIC = 'BASIC'
    FULL = 'FULL'
    DEALER_PACK_10 = 'DEALER_PACK_10'
    REPORT_TYPE_CHOICES = [
        (BASIC, 'Basic Report — UGX 35,000'),
        (FULL, 'Full Report — UGX 75,000'),
        (DEALER_PACK_10, 'Dealer Pack (10 Reports) — UGX 600,000'),
    ]

    MTN = 'MTN'
    AIRTEL = 'AIRTEL'
    CARD_FLW = 'CARD_FLUTTERWAVE'
    DEALER_CREDIT = 'DEALER_CREDIT'
    PAYMENT_METHOD_CHOICES = [
        (MTN, 'MTN Mobile Money'),
        (AIRTEL, 'Airtel Money'),
        (CARD_FLW, 'Visa / Mastercard'),
        (DEALER_CREDIT, 'Dealer Credit'),
    ]

    PENDING = 'PENDING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'
    REFUNDED = 'REFUNDED'
    PAYMENT_STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (COMPLETED, 'Completed'),
        (FAILED, 'Failed'),
        (REFUNDED, 'Refunded'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='orders'
    )
    report = models.OneToOneField(
        'vehicles.VehicleReport', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='order'
    )
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    amount_ugx = models.DecimalField(max_digits=12, decimal_places=2)
    amount_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True
    )
    payment_status = models.CharField(
        max_length=10, choices=PAYMENT_STATUS_CHOICES, default=PENDING
    )
    flutterwave_ref = models.CharField(max_length=150, blank=True)
    flutterwave_tx_id = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    customer_email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']

    def __str__(self):
        return f'Order {self.id} — {self.payment_status} — UGX {self.amount_ugx:,.0f}'

    @property
    def is_paid(self):
        return self.payment_status == self.COMPLETED

    def get_flutterwave_currency(self):
        return 'UGX'
