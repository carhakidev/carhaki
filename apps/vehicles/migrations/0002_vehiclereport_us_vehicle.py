from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vehicles', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="UPDATE vehicles_vehiclereport SET report_type = 'us_vehicle'",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AlterField(
            model_name='vehiclereport',
            name='report_type',
            field=models.CharField(
                choices=[('us_vehicle', 'US Vehicle Report')],
                default='us_vehicle',
                max_length=20,
            ),
        ),
    ]
