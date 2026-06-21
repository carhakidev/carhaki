import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('vehicles', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('report_type', models.CharField(
                    choices=[('us_vehicle', 'US Vehicle Report')],
                    max_length=20,
                )),
                ('amount_ngn', models.DecimalField(decimal_places=2, max_digits=12)),
                ('payment_method', models.CharField(
                    blank=True,
                    choices=[('paystack', 'Paystack')],
                    max_length=20,
                )),
                ('payment_status', models.CharField(
                    choices=[
                        ('PENDING', 'Pending'),
                        ('COMPLETED', 'Completed'),
                        ('FAILED', 'Failed'),
                        ('REFUNDED', 'Refunded'),
                    ],
                    default='PENDING',
                    max_length=10,
                )),
                ('paystack_reference', models.CharField(blank=True, max_length=100)),
                ('paystack_access_code', models.CharField(blank=True, max_length=100)),
                ('customer_email', models.EmailField(blank=True, max_length=254)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('paid_at', models.DateTimeField(blank=True, null=True)),
                ('report', models.OneToOneField(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='order',
                    to='vehicles.vehiclereport',
                )),
                ('user', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='orders',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Order',
                'verbose_name_plural': 'Orders',
                'ordering': ['-created_at'],
            },
        ),
    ]
