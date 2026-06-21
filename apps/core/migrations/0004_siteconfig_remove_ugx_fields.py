from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_apilog_paystack'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Drop UGX price columns only if they exist (production may never have had them)
        migrations.RunSQL(
            sql="""
                ALTER TABLE core_siteconfig DROP COLUMN IF EXISTS basic_report_ugx;
                ALTER TABLE core_siteconfig DROP COLUMN IF EXISTS full_report_ugx;
                ALTER TABLE core_siteconfig DROP COLUMN IF EXISTS dealer_pack_10_ugx;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS core_dealerapplication CASCADE;",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
