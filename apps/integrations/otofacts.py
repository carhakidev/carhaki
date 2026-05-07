import requests
from django.conf import settings
from .base import BaseAPIProvider
from apps.core.models import APILog

OTOFACTS_BASE = 'https://api.otofacts.com/v1'


class OtoFactsProvider(BaseAPIProvider):
    provider_name = APILog.OTOFACTS
    cost_per_call_usd = 6.00

    def __init__(self):
        self.api_key = settings.OTOFACTS_API_KEY

    def _headers(self):
        return {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}

    def get_basic_info(self, identifier: str) -> dict:
        if not self.api_key:
            return {'error': 'OtoFacts API key not configured', 'source': 'otofacts'}
        url = f'{OTOFACTS_BASE}/vehicle/{identifier}/basic'
        result, elapsed, error = self._timed_request(
            lambda: requests.get(url, headers=self._headers(), timeout=15).json()
        )
        if error or not result:
            self._log(url, identifier, False, elapsed, cost_usd=0, error=error or 'No data')
            return {}
        self._log(url, identifier, True, elapsed, cost_usd=0)
        return result

    def get_full_report(self, identifier: str) -> dict:
        if not self.api_key:
            return {'error': 'OtoFacts API key not configured', 'source': 'otofacts'}
        url = f'{OTOFACTS_BASE}/vehicle/{identifier}/history'
        result, elapsed, error = self._timed_request(
            lambda: requests.get(url, headers=self._headers(), timeout=30).json()
        )
        if error or not result:
            self._log(url, identifier, False, elapsed, error=error or 'No data')
            return {'error': error or 'No response', 'source': 'otofacts'}
        self._log(url, identifier, True, elapsed)
        return {'raw': result, 'source': 'otofacts'}
