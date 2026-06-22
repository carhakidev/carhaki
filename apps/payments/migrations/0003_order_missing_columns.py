from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0002_add_amount_ngn'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE payments_order ADD COLUMN IF NOT EXISTS updated_at timestamptz;
                ALTER TABLE payments_order ADD COLUMN IF NOT EXISTS quantity integer DEFAULT 1;
                ALTER TABLE payments_order ADD COLUMN IF NOT EXISTS payment_method varchar(20) DEFAULT 'paystack';
                ALTER TABLE payments_order ADD COLUMN IF NOT EXISTS order_tracking_id varchar(100) DEFAULT '';
                ALTER TABLE payments_order ADD COLUMN IF NOT EXISTS customer_email varchar(254) DEFAULT '';
                UPDATE payments_order SET updated_at = created_at WHERE updated_at IS NULL;
                ALTER TABLE payments_order ALTER COLUMN updated_at SET DEFAULT now();
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
