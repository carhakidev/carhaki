from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_apilog_paystack'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(model_name='siteconfig', name='basic_report_ugx'),
        migrations.RemoveField(model_name='siteconfig', name='full_report_ugx'),
        migrations.RemoveField(model_name='siteconfig', name='dealer_pack_10_ugx'),
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS core_dealerapplication CASCADE;",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
