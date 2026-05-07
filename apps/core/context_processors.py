from django.conf import settings
from .models import SiteConfig


def site_config(request):
    try:
        config = SiteConfig.get_solo()
    except Exception:
        return {}
    return {
        'site_config': config,
        'BASIC_PRICE_UGX': f'{int(config.basic_report_ugx):,}',
        'FULL_PRICE_UGX': f'{int(config.full_report_ugx):,}',
        'DEALER_PACK_PRICE_UGX': f'{int(config.dealer_pack_10_ugx):,}',
        'site_url': getattr(settings, 'SITE_URL', 'https://carhaki.ug'),
    }
