from django.conf import settings
from .models import SiteConfig
from .constants import REPORT_PRICE_NGN


def site_config(request):
    try:
        config = SiteConfig.get_solo()
    except Exception:
        return {}
    return {
        'site_config': config,
        'REPORT_PRICE_NGN': f'{REPORT_PRICE_NGN:,}',
        'site_url': getattr(settings, 'SITE_URL', 'https://carhaki.com.ng'),
    }
