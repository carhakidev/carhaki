import requests
from django.conf import settings
from .base import BaseAPIProvider
from apps.core.models import APILog

CARCHECK_BASE = 'https://api.carcheck.jp/v1'


class CarCheckJPProvider(BaseAPIProvider):
    provider_name = APILog.CARCHECK_JP
    cost_per_call_usd = 6.00

    def __init__(self):
        self.api_key = settings.CARCHECK_JP_API_KEY

    def get_basic_info(self, identifier: str) -> dict:
        return {}

    def get_full_report(self, identifier: str) -> dict:
        if not self.api_key:
            return {'error': 'CarCheck.jp API key not configured', 'source': 'carcheck_jp'}
        url = f'{CARCHECK_BASE}/report'
        params = {'api_key': self.api_key, 'chassis': identifier}
        result, elapsed, error = self._timed_request(
            lambda: requests.get(url, params=params, timeout=30).json()
        )
        if error or not result:
            self._log(url, identifier, False, elapsed, error=error or 'No data')
            return {'error': error or 'No response', 'source': 'carcheck_jp'}
        self._log(url, identifier, True, elapsed)
        return {'raw': result, 'source': 'carcheck_jp'}
