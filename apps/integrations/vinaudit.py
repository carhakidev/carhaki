import requests
from django.conf import settings
from .base import BaseAPIProvider
from apps.core.models import APILog

VINAUDIT_BASE = 'https://marketvalue.vinaudit.com/getmarketvalue.php'
VINAUDIT_HISTORY_BASE = 'https://api.vinaudit.com/query.php'


class VinAuditProvider(BaseAPIProvider):
    provider_name = APILog.VINAUDIT
    cost_per_call_usd = 1.50

    def __init__(self):
        self.api_key = settings.VINAUDIT_API_KEY

    def get_basic_info(self, identifier: str) -> dict:
        return {}

    def get_full_report(self, identifier: str) -> dict:
        if not self.api_key:
            return {'error': 'VinAudit API key not configured', 'source': 'vinaudit'}

        url = VINAUDIT_HISTORY_BASE
        params = {
            'key': self.api_key,
            'vin': identifier,
            'format': 'json',
        }
        result, elapsed, error = self._timed_request(
            lambda: requests.get(url, params=params, timeout=30).json()
        )

        if error or not result:
            self._log(url, identifier, False, elapsed, error=error or 'No response')
            return {'error': error or 'No response', 'source': 'vinaudit'}

        if not result.get('success'):
            self._log(url, identifier, False, elapsed,
                     error=result.get('error', 'API returned failure'))
            return {'error': result.get('error', 'Unknown error'), 'source': 'vinaudit'}

        self._log(url, identifier, True, elapsed)
        return {'raw': result, 'source': 'vinaudit'}
