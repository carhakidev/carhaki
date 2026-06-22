from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0003_order_missing_columns'),
    ]

    operations = [
        # quantity was added as raw SQL in 0003; use IF NOT EXISTS so this is safe on production
        migrations.RunSQL(
            sql="ALTER TABLE payments_order ADD COLUMN IF NOT EXISTS quantity integer DEFAULT 1;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        # Update Django's migration state to reflect the field exists on the model
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name='order',
                    name='quantity',
                    field=models.PositiveIntegerField(default=1),
                ),
            ],
        ),
    ]
