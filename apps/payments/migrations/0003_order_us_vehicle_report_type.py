from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0002_order_paystack'),
    ]

    operations = [
        migrations.RunSQL(
            sql="UPDATE payments_order SET report_type = 'us_vehicle'",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AlterField(
            model_name='order',
            name='report_type',
            field=models.CharField(
                choices=[('us_vehicle', 'US Vehicle Report')],
                max_length=20,
            ),
        ),
    ]
