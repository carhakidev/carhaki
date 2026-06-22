import uuid
from django.db import models
from django.conf import settings


class Order(models.Model):
    US_VEHICLE = 'us_vehicle'
    REPORT_TYPE_CHOICES = [
        (US_VEHICLE, 'US Vehicle Report'),
    ]

    PAYSTACK = 'paystack'
    PAYMENT_METHOD_CHOICES = [
        (PAYSTACK, 'Paystack'),
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
    amount_ngn = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True
    )
    payment_status = models.CharField(
        max_length=10, choices=PAYMENT_STATUS_CHOICES, default=PENDING
    )
    paystack_reference = models.CharField(max_length=100, blank=True)
    paystack_access_code = models.CharField(max_length=100, blank=True)
    customer_email = models.EmailField(blank=True)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']

    def __str__(self):
        return f'Order {self.id} — {self.payment_status} — NGN {self.amount_ngn:,.0f}'

    @property
    def is_paid(self):
        return self.payment_status == self.COMPLETED
