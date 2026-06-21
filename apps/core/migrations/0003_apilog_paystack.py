from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_faq_sitestatistic_contactmessage_dealerapplication'),
    ]

    operations = [
        migrations.AlterField(
            model_name='apilog',
            name='provider',
            field=models.CharField(
                choices=[
                    ('NHTSA', 'NHTSA (Free)'),
                    ('VINAUDIT', 'VinAudit'),
                    ('OTOFACTS', 'OtoFacts'),
                    ('CARCHECK_JP', 'CarCheck.jp'),
                    ('ANTHROPIC', 'Anthropic Claude'),
                    ('PAYSTACK', 'Paystack'),
                ],
                max_length=20,
            ),
        ),
    ]
