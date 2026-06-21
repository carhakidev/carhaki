from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_siteconfig_remove_ugx_fields'),
    ]

    operations = [
        migrations.RenameField(
            model_name='siteconfig',
            old_name='usd_to_ugx_rate',
            new_name='usd_to_ngn_rate',
        ),
        migrations.AlterField(
            model_name='siteconfig',
            name='usd_to_ngn_rate',
            field=models.DecimalField(decimal_places=2, default=1600, max_digits=10),
        ),
        migrations.AlterField(
            model_name='apilog',
            name='provider',
            field=models.CharField(
                choices=[
                    ('NHTSA', 'NHTSA (Free)'),
                    ('VINAUDIT', 'VinAudit'),
                    ('CLEARVIN', 'ClearVin'),
                    ('ANTHROPIC', 'Anthropic Claude'),
                    ('PAYSTACK', 'Paystack'),
                ],
                max_length=20,
            ),
        ),
    ]
