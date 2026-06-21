import uuid
from django.db import models
from django.conf import settings
from solo.models import SingletonModel


class SiteConfig(SingletonModel):
    usd_to_ngn_rate = models.DecimalField(max_digits=10, decimal_places=2, default=1600)
    maintenance_mode = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Site Configuration'

    def __str__(self):
        return 'Site Configuration'


class APILog(models.Model):
    NHTSA = 'NHTSA'
    VINAUDIT = 'VINAUDIT'
    CLEARVIN = 'CLEARVIN'
    ANTHROPIC = 'ANTHROPIC'
    PAYSTACK = 'PAYSTACK'

    PROVIDER_CHOICES = [
        (NHTSA, 'NHTSA (Free)'),
        (VINAUDIT, 'VinAudit'),
        (CLEARVIN, 'ClearVin'),
        (ANTHROPIC, 'Anthropic Claude'),
        (PAYSTACK, 'Paystack'),
    ]

    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    endpoint = models.CharField(max_length=200)
    identifier = models.CharField(max_length=30, blank=True)
    cost_usd = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    success = models.BooleanField(default=True)
    response_time_ms = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'API Log'
        verbose_name_plural = 'API Logs'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.provider} - {self.identifier} ({self.created_at:%Y-%m-%d})'


class ContactMessage(models.Model):
    GENERAL = 'GENERAL'
    REPORT_ISSUE = 'REPORT_ISSUE'
    PAYMENT_PROBLEM = 'PAYMENT_PROBLEM'
    PARTNERSHIP = 'PARTNERSHIP'
    PRESS = 'PRESS'
    DEALER_INQUIRY = 'DEALER_INQUIRY'

    SUBJECT_CHOICES = [
        (GENERAL, 'General Inquiry'),
        (REPORT_ISSUE, 'Report Issue'),
        (PAYMENT_PROBLEM, 'Payment Problem'),
        (PARTNERSHIP, 'Partnership'),
        (PRESS, 'Press'),
        (DEALER_INQUIRY, 'Dealer Account Inquiry'),
    ]

    UNREAD = 'UNREAD'
    READ = 'READ'
    REPLIED = 'REPLIED'
    STATUS_CHOICES = [
        (UNREAD, 'Unread'),
        (READ, 'Read'),
        (REPLIED, 'Replied'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    subject = models.CharField(max_length=20, choices=SUBJECT_CHOICES, default=GENERAL)
    message = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=UNREAD)
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    replied_at = models.DateTimeField(null=True, blank=True)
    replied_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='contact_replies'
    )

    class Meta:
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} - {self.get_subject_display()} ({self.created_at:%Y-%m-%d})'



class FAQ(models.Model):
    ABOUT_REPORTS = 'ABOUT_REPORTS'
    SEARCHING = 'SEARCHING'
    PAYMENTS = 'PAYMENTS'
    UNDERSTANDING = 'UNDERSTANDING'

    CATEGORY_CHOICES = [
        (ABOUT_REPORTS, 'About the Reports'),
        (SEARCHING, 'Searching for a Vehicle'),
        (PAYMENTS, 'Payments'),
        (UNDERSTANDING, 'Understanding Results'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    question = models.CharField(max_length=500)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0, help_text='Display order within category')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'
        ordering = ['category', 'order']

    def __str__(self):
        return self.question[:80]


class SiteStatistic(models.Model):
    stat_key = models.CharField(max_length=100, unique=True)
    stat_value = models.CharField(max_length=200, default='0')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Site Statistic'
        verbose_name_plural = 'Site Statistics'

    def __str__(self):
        return f'{self.stat_key}: {self.stat_value}'

    @classmethod
    def get(cls, key, default='0'):
        try:
            return cls.objects.get(stat_key=key).stat_value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set(cls, key, value):
        cls.objects.update_or_create(stat_key=key, defaults={'stat_value': str(value)})
