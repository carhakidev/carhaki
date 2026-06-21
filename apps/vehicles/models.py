import uuid
from django.db import models
from django.conf import settings


class VehicleSearch(models.Model):
    VIN = 'VIN'
    CHASSIS = 'CHASSIS'
    IDENTIFIER_TYPE_CHOICES = [(VIN, 'VIN (USA)'), (CHASSIS, 'Chassis Number (Japan)')]

    USA = 'USA'
    JAPAN = 'JAPAN'
    COUNTRY_CHOICES = [(USA, 'USA'), (JAPAN, 'Japan')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    identifier = models.CharField(max_length=25)
    identifier_type = models.CharField(max_length=10, choices=IDENTIFIER_TYPE_CHOICES)
    source_country = models.CharField(max_length=5, choices=COUNTRY_CHOICES)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='searches'
    )
    session_key = models.CharField(max_length=40, blank=True)
    basic_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Vehicle Search'
        verbose_name_plural = 'Vehicle Searches'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.identifier} ({self.source_country})'


class VehicleReport(models.Model):
    US_VEHICLE = 'us_vehicle'
    REPORT_TYPE_CHOICES = [
        (US_VEHICLE, 'US Vehicle Report'),
    ]

    PENDING = 'PENDING'
    PROCESSING = 'PROCESSING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (PROCESSING, 'Processing'),
        (COMPLETED, 'Completed'),
        (FAILED, 'Failed'),
    ]

    GRADE_CHOICES = [
        ('A', 'A — Excellent'),
        ('B', 'B — Good'),
        ('C', 'C — Acceptable'),
        ('D', 'D — Concerning'),
        ('E', 'E — Poor'),
        ('F', 'F — Critical Risk'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    search = models.ForeignKey(
        VehicleSearch, on_delete=models.CASCADE, related_name='reports'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reports'
    )
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES, default=US_VEHICLE)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=PENDING)
    raw_data = models.JSONField(null=True, blank=True)
    processed_data = models.JSONField(null=True, blank=True)
    ai_summary = models.TextField(blank=True)
    overall_grade = models.CharField(max_length=1, choices=GRADE_CHOICES, blank=True)
    risk_score = models.IntegerField(default=100)
    pdf_file = models.FileField(upload_to='reports/pdfs/', null=True, blank=True)
    share_token = models.UUIDField(default=uuid.uuid4, unique=True)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Vehicle Report'
        verbose_name_plural = 'Vehicle Reports'
        ordering = ['-created_at']

    def __str__(self):
        return f'Report {self.search.identifier} — {self.overall_grade or self.status}'

    @property
    def grade_colour(self):
        colours = {
            'A': '#198754', 'B': '#28a745',
            'C': '#ffc107', 'D': '#fd7e14',
            'E': '#dc3545', 'F': '#721c24',
        }
        return colours.get(self.overall_grade, '#6c757d')

    @property
    def grade_label(self):
        labels = {
            'A': 'Excellent', 'B': 'Good', 'C': 'Acceptable',
            'D': 'Concerning', 'E': 'Poor — Avoid', 'F': 'Critical Risk',
        }
        return labels.get(self.overall_grade, 'Unknown')

    @property
    def traffic_light(self):
        if self.overall_grade in ('A', 'B'):
            return 'green'
        elif self.overall_grade == 'C':
            return 'amber'
        return 'red'

    @property
    def share_url(self):
        return f'/reports/shared/{self.share_token}/'


class RecallAlert(models.Model):
    NHTSA = 'NHTSA'
    OTOFACTS = 'OTOFACTS'
    SOURCE_CHOICES = [(NHTSA, 'NHTSA'), (OTOFACTS, 'OtoFacts')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vin = models.CharField(max_length=17)
    recall_number = models.CharField(max_length=50)
    component = models.CharField(max_length=200)
    summary = models.TextField()
    remedy = models.TextField(blank=True)
    issued_date = models.DateField(null=True, blank=True)
    is_open = models.BooleanField(default=True)
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default=NHTSA)

    class Meta:
        verbose_name = 'Recall Alert'
        verbose_name_plural = 'Recall Alerts'
        unique_together = ['vin', 'recall_number']

    def __str__(self):
        return f'{self.recall_number} — {self.component}'
