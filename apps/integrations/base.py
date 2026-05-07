import time
import logging
from abc import ABC, abstractmethod
from apps.core.models import APILog

logger = logging.getLogger(__name__)


class BaseAPIProvider(ABC):
    provider_name = ''
    cost_per_call_usd = 0.0

    @abstractmethod
    def get_basic_info(self, identifier: str) -> dict:
        pass

    @abstractmethod
    def get_full_report(self, identifier: str) -> dict:
        pass

    def _log(self, endpoint: str, identifier: str, success: bool,
             response_time_ms: int, cost_usd: float = None, error: str = ''):
        APILog.objects.create(
            provider=self.provider_name,
            endpoint=endpoint,
            identifier=identifier,
            cost_usd=cost_usd if cost_usd is not None else self.cost_per_call_usd,
            success=success,
            response_time_ms=response_time_ms,
            error_message=error,
        )

    def _timed_request(self, func, *args, **kwargs):
        start = time.time()
        try:
            result = func(*args, **kwargs)
            elapsed = int((time.time() - start) * 1000)
            return result, elapsed, None
        except Exception as e:
            elapsed = int((time.time() - start) * 1000)
            return None, elapsed, str(e)
