from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0002_order_paystack'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_name='payments_order'
                    ) THEN
                        UPDATE payments_order
                        SET report_type = 'us_vehicle'
                        WHERE report_type IN ('BASIC', 'FULL', 'DEALER_PACK_10', 'basic', 'full', 'dealer_pack_10');
                    END IF;
                END $$;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        # Choices-only change — no schema mutation
        migrations.AlterField(
            model_name='order',
            name='report_type',
            field=models.CharField(
                choices=[('us_vehicle', 'US Vehicle Report')],
                max_length=20,
            ),
        ),
    ]
