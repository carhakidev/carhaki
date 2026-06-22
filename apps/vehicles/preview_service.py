import logging
from apps.integrations.nhtsa import NHTSAProvider
from apps.integrations.cache import VehicleDataCache

logger = logging.getLogger(__name__)


def get_preview_data(vin: str) -> dict:
    """
    Return free NHTSA preview data for a VIN.
    Checks the cache first; falls back to NHTSA API.
    Raises ValueError if the VIN returns no usable data.
    """
    vin = vin.upper().strip()
    cache = VehicleDataCache()

    cached = cache.get_preview(vin)
    if cached and not cached.get('error'):
        cached.setdefault('vin', vin)
        cached.setdefault('identifier_type', 'VIN')
        cached.setdefault('source_country', 'USA')
        return cached

    nhtsa = NHTSAProvider()
    data = nhtsa.get_basic_info(vin)

    if not data or data.get('error') or not data.get('make'):
        raise ValueError(f'No vehicle data found for VIN {vin}')

    cache.set_preview(vin, data)

    data['vin'] = vin
    data['identifier_type'] = 'VIN'
    data['source_country'] = 'USA'
    return data
