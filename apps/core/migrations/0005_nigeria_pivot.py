from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_siteconfig_remove_ugx_fields'),
    ]

    operations = [
        # Rename usd_to_ugx_rate → usd_to_ngn_rate if old column exists;
        # add usd_to_ngn_rate directly if neither column exists yet.
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='core_siteconfig' AND column_name='usd_to_ugx_rate'
                    ) THEN
                        ALTER TABLE core_siteconfig RENAME COLUMN usd_to_ugx_rate TO usd_to_ngn_rate;
                    ELSIF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='core_siteconfig' AND column_name='usd_to_ngn_rate'
                    ) THEN
                        ALTER TABLE core_siteconfig ADD COLUMN usd_to_ngn_rate numeric(10,2) DEFAULT 1600;
                    END IF;
                END $$;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        # Set the column default to 1600 (safe — column is guaranteed to exist above)
        migrations.AlterField(
            model_name='siteconfig',
            name='usd_to_ngn_rate',
            field=models.DecimalField(decimal_places=2, default=1600, max_digits=10),
        ),
        # Choices-only change — no schema mutation
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
