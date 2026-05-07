import requests
from .base import BaseAPIProvider
from apps.core.models import APILog

VPIC_BASE = 'https://vpic.nhtsa.dot.gov/api/vehicles'
RECALLS_BASE = 'https://api.nhtsa.gov/recalls/recallsByVehicle'


class NHTSAProvider(BaseAPIProvider):
    provider_name = APILog.NHTSA
    cost_per_call_usd = 0.0

    def get_basic_info(self, identifier: str) -> dict:
        url = f'{VPIC_BASE}/DecodeVinValuesExtended/{identifier}?format=json'
        result, elapsed, error = self._timed_request(
            lambda: requests.get(url, timeout=10).json()
        )
        if error or not result:
            self._log(url, identifier, False, elapsed, error=error or 'No data')
            return {}

        results = result.get('Results', [{}])[0]
        self._log(url, identifier, True, elapsed, cost_usd=0)

        make = results.get('Make', '')
        model = results.get('Model', '')
        year = results.get('ModelYear', '')
        body = results.get('BodyClass', '')
        engine = results.get('DisplacementL', '')
        cylinders = results.get('EngineCylinders', '')
        fuel = results.get('FuelTypePrimary', '')
        drive = results.get('DriveType', '')
        transmission = results.get('TransmissionStyle', '')
        doors = results.get('Doors', '')
        plant_country = results.get('PlantCountry', '')
        trim = results.get('Trim', '')
        series = results.get('Series', '')

        return {
            'make': make,
            'model': model,
            'year': int(year) if year and year.isdigit() else None,
            'trim': trim or series,
            'body_type': body,
            'engine': f'{engine}L' if engine else '',
            'cylinders': cylinders,
            'fuel_type': fuel,
            'drive_type': drive,
            'transmission': transmission,
            'doors': int(doors) if doors and doors.isdigit() else None,
            'country_of_manufacture': plant_country,
            'source': 'NHTSA',
        }

    def get_recalls(self, make: str, model: str, year: int) -> list:
        url = f'{RECALLS_BASE}?make={make}&model={model}&modelYear={year}'
        result, elapsed, error = self._timed_request(
            lambda: requests.get(url, timeout=10).json()
        )
        if error or not result:
            self._log(url, f'{make}/{model}/{year}', False, elapsed, error=error or 'No data')
            return []

        self._log(url, f'{make}/{model}/{year}', True, elapsed, cost_usd=0)
        recalls = []
        for r in result.get('results', []):
            recalls.append({
                'recall_number': r.get('NHTSACampaignNumber', ''),
                'component': r.get('Component', ''),
                'summary': r.get('Summary', ''),
                'remedy': r.get('Remedy', ''),
                'is_open': True,
                'source': 'NHTSA',
            })
        return recalls

    def get_full_report(self, identifier: str) -> dict:
        return self.get_basic_info(identifier)
