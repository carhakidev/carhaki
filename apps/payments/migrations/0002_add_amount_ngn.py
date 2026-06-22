from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE payments_order ADD COLUMN IF NOT EXISTS amount_ngn integer DEFAULT 0;
                UPDATE payments_order SET amount_ngn = amount_ugx WHERE amount_ngn = 0 AND amount_ugx IS NOT NULL;
                ALTER TABLE payments_order ADD COLUMN IF NOT EXISTS paystack_reference varchar(100) DEFAULT '';
                ALTER TABLE payments_order ADD COLUMN IF NOT EXISTS paystack_access_code varchar(100) DEFAULT '';
                ALTER TABLE payments_order DROP COLUMN IF EXISTS amount_ugx;
                ALTER TABLE payments_order DROP COLUMN IF EXISTS amount_usd;
                ALTER TABLE payments_order DROP COLUMN IF EXISTS flutterwave_ref;
                ALTER TABLE payments_order DROP COLUMN IF EXISTS flutterwave_tx_id;
                ALTER TABLE payments_order DROP COLUMN IF EXISTS phone_number;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
