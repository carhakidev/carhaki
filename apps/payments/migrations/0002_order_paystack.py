from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
    ]

    operations = [
        # 1. Add new NGN amount field (allow null temporarily for the rename)
        migrations.AddField(
            model_name='order',
            name='amount_ngn',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
            preserve_default=False,
        ),
        # 2. Copy existing UGX values into NGN column
        migrations.RunSQL(
            sql='UPDATE payments_order SET amount_ngn = amount_ugx',
            reverse_sql=migrations.RunSQL.noop,
        ),
        # 3. Remove the old UGX and USD fields
        migrations.RemoveField(model_name='order', name='amount_ugx'),
        migrations.RemoveField(model_name='order', name='amount_usd'),
        # 4. Remove Flutterwave-specific fields
        migrations.RemoveField(model_name='order', name='flutterwave_ref'),
        migrations.RemoveField(model_name='order', name='flutterwave_tx_id'),
        migrations.RemoveField(model_name='order', name='phone_number'),
        # 5. Add Paystack reference fields
        migrations.AddField(
            model_name='order',
            name='paystack_reference',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='order',
            name='paystack_access_code',
            field=models.CharField(blank=True, max_length=100),
        ),
        # 6. Update payment_method choices (existing rows keep their value; blank is still valid)
        migrations.AlterField(
            model_name='order',
            name='payment_method',
            field=models.CharField(
                blank=True,
                choices=[('paystack', 'Paystack')],
                max_length=20,
            ),
        ),
        # 7. Update report_type display labels (remove currency strings)
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
