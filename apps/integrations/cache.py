from django.core.cache import cache
import hashlib


PREVIEW_TTL = 60 * 60 * 24 * 365  # NHTSA specs never change
REPORT_TTL = 60 * 60 * 24 * 30    # Full reports cached 30 days


def _cache_key(prefix: str, identifier: str) -> str:
    safe = hashlib.md5(identifier.upper().encode()).hexdigest()
    return f'carhaki:{prefix}:{safe}'


class VehicleDataCache:
    def get_preview(self, identifier: str) -> dict | None:
        return cache.get(_cache_key('preview', identifier))

    def set_preview(self, identifier: str, data: dict):
        cache.set(_cache_key('preview', identifier), data, PREVIEW_TTL)

    def get_report(self, identifier: str, report_type: str, country: str) -> dict | None:
        key = _cache_key(f'report:{country}:{report_type}', identifier)
        return cache.get(key)

    def set_report(self, identifier: str, report_type: str, country: str, data: dict):
        key = _cache_key(f'report:{country}:{report_type}', identifier)
        cache.set(key, data, REPORT_TTL)

    def invalidate(self, identifier: str):
        for prefix in ['preview', 'report:USA:FULL', 'report:USA:BASIC',
                        'report:JAPAN:FULL', 'report:JAPAN:BASIC']:
            cache.delete(_cache_key(prefix, identifier))
