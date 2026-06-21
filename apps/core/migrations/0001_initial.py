import uuid
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('usd_to_ngn_rate', models.DecimalField(decimal_places=2, default=1600, max_digits=10)),
                ('maintenance_mode', models.BooleanField(default=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Site Configuration',
            },
        ),
        migrations.CreateModel(
            name='APILog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider', models.CharField(
                    choices=[
                        ('NHTSA', 'NHTSA (Free)'),
                        ('VINAUDIT', 'VinAudit'),
                        ('CLEARVIN', 'ClearVin'),
                        ('ANTHROPIC', 'Anthropic Claude'),
                        ('PAYSTACK', 'Paystack'),
                    ],
                    max_length=20,
                )),
                ('endpoint', models.CharField(max_length=200)),
                ('identifier', models.CharField(blank=True, max_length=30)),
                ('cost_usd', models.DecimalField(decimal_places=4, default=0, max_digits=8)),
                ('success', models.BooleanField(default=True)),
                ('response_time_ms', models.IntegerField(default=0)),
                ('error_message', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'API Log',
                'verbose_name_plural': 'API Logs',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ContactMessage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200)),
                ('email', models.EmailField(max_length=254)),
                ('phone', models.CharField(blank=True, max_length=30)),
                ('subject', models.CharField(
                    choices=[
                        ('GENERAL', 'General Inquiry'),
                        ('REPORT_ISSUE', 'Report Issue'),
                        ('PAYMENT_PROBLEM', 'Payment Problem'),
                        ('PARTNERSHIP', 'Partnership'),
                        ('PRESS', 'Press'),
                        ('DEALER_INQUIRY', 'Dealer Account Inquiry'),
                    ],
                    default='GENERAL',
                    max_length=20,
                )),
                ('message', models.TextField()),
                ('status', models.CharField(
                    choices=[('UNREAD', 'Unread'), ('READ', 'Read'), ('REPLIED', 'Replied')],
                    default='UNREAD',
                    max_length=10,
                )),
                ('admin_notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('replied_at', models.DateTimeField(blank=True, null=True)),
                ('replied_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='contact_replies',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Contact Message',
                'verbose_name_plural': 'Contact Messages',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='FAQ',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('category', models.CharField(
                    choices=[
                        ('ABOUT_REPORTS', 'About the Reports'),
                        ('SEARCHING', 'Searching for a Vehicle'),
                        ('PAYMENTS', 'Payments'),
                        ('UNDERSTANDING', 'Understanding Results'),
                    ],
                    max_length=20,
                )),
                ('question', models.CharField(max_length=500)),
                ('answer', models.TextField()),
                ('order', models.PositiveIntegerField(default=0, help_text='Display order within category')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'FAQ',
                'verbose_name_plural': 'FAQs',
                'ordering': ['category', 'order'],
            },
        ),
        migrations.CreateModel(
            name='SiteStatistic',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stat_key', models.CharField(max_length=100, unique=True)),
                ('stat_value', models.CharField(default='0', max_length=200)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Site Statistic',
                'verbose_name_plural': 'Site Statistics',
            },
        ),
    ]
