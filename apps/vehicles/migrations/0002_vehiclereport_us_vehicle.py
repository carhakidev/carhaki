from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vehicles', '0001_initial'),
    ]

    operations = [
        # Update existing rows only if the table exists (it always should, but be safe)
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_name='vehicles_vehiclereport'
                    ) THEN
                        UPDATE vehicles_vehiclereport
                        SET report_type = 'us_vehicle'
                        WHERE report_type IN ('BASIC', 'FULL', 'basic', 'full');
                    END IF;
                END $$;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        # AlterField changes max_length 10→20 and default/choices — safe on PostgreSQL
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
