from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
    ]

    operations = [
        # 1. Add amount_ngn if it doesn't already exist
        migrations.RunSQL(
            sql="ALTER TABLE payments_order ADD COLUMN IF NOT EXISTS amount_ngn numeric(12,2) DEFAULT 0;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        # 2. Copy UGX values into NGN only when amount_ugx column exists
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='payments_order' AND column_name='amount_ugx'
                    ) THEN
                        UPDATE payments_order SET amount_ngn = amount_ugx;
                    END IF;
                END $$;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        # 3. Drop old UGX / USD columns if they exist
        migrations.RunSQL(
            sql="""
                ALTER TABLE payments_order DROP COLUMN IF EXISTS amount_ugx;
                ALTER TABLE payments_order DROP COLUMN IF EXISTS amount_usd;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        # 4. Drop Flutterwave-specific columns if they exist
        migrations.RunSQL(
            sql="""
                ALTER TABLE payments_order DROP COLUMN IF EXISTS flutterwave_ref;
                ALTER TABLE payments_order DROP COLUMN IF EXISTS flutterwave_tx_id;
                ALTER TABLE payments_order DROP COLUMN IF EXISTS phone_number;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        # 5. Add Paystack columns if not already present
        migrations.RunSQL(
            sql="""
                ALTER TABLE payments_order ADD COLUMN IF NOT EXISTS paystack_reference varchar(100) NOT NULL DEFAULT '';
                ALTER TABLE payments_order ADD COLUMN IF NOT EXISTS paystack_access_code varchar(100) NOT NULL DEFAULT '';
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        # 6. Choices-only change — no schema mutation
        migrations.AlterField(
            model_name='order',
            name='payment_method',
            field=models.CharField(
                blank=True,
                choices=[('paystack', 'Paystack')],
                max_length=20,
            ),
        ),
        # 7. Choices-only change — no schema mutation
        migrations.AlterField(
            model_name='order',
            name='report_type',
            field=models.CharField(
                choices=[
                    ('BASIC', 'Basic Report'),
                    ('FULL', 'Full Report'),
                    ('DEALER_PACK_10', 'Dealer Pack (10 Reports)'),
                ],
                max_length=20,
            ),
        ),
    ]
