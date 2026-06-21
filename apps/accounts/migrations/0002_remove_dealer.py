from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS accounts_dealerprofile CASCADE;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AlterField(
            model_name='customuser',
            name='account_type',
            field=models.CharField(
                choices=[('INDIVIDUAL', 'Individual Buyer')],
                default='INDIVIDUAL',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='country',
            field=models.CharField(default='Nigeria', max_length=50),
        ),
    ]
