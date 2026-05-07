"""
Normalize API responses from different providers into a single standard schema.
All callers work with the normalized dict -- never raw API data.
"""
from datetime import datetime, timezone
from apps.vehicles.validators import check_uganda_import_eligibility


class ReportNormalizer:

    def normalize(self, raw_data: dict, source: str, basic_info: dict = None, recalls: list = None) -> dict:
        source = source.lower()
        if source == 'vinaudit':
            return self._normalize_vinaudit(raw_data, basic_info or {}, recalls or [])
        elif source in ('otofacts',):
            return self._normalize_otofacts(raw_data, basic_info or {})
        elif source == 'carcheck_jp':
            return self._normalize_carcheck_jp(raw_data, basic_info or {})
        return raw_data

    def _normalize_vinaudit(self, data: dict, basic_info: dict, recalls: list) -> dict:
        raw = data.get('raw', {})
        attributes = raw.get('attributes', {})
        year = basic_info.get('year') or int(attributes.get('year', 0) or 0)
        title_records = raw.get('titleRecords', [])
        odometer_records = raw.get('odometerRecords', [])
        accidents = raw.get('accidentRecords', [])
        brands_raw = raw.get('brands', [])
        theft_records = raw.get('theftRecords', [])
        junk_salvage = raw.get('junkSalvageRecords', [])

        brands = []
        for b in brands_raw:
            brand_name = b.get('name', '').upper()
            if brand_name:
                brands.append(brand_name)
        for js in junk_salvage:
            js_type = js.get('type', '').upper()
            if js_type and js_type not in brands:
                brands.append(js_type)

        normalized_titles = [
            {'state': t.get('state', ''), 'date': t.get('date', ''),
             'odometer': t.get('odometer', 0), 'brand': t.get('brand', '')}
            for t in title_records
        ]
        normalized_odometer = [
            {'date': o.get('date', ''), 'reading': o.get('value', 0),
             'unit': o.get('unit', 'miles'), 'source': o.get('source', '')}
            for o in odometer_records
        ]
        normalized_accidents = [
            {'date': a.get('date', ''),
             'severity': 'MAJOR' if a.get('airbagDeployed') else 'MINOR',
             'airbags_deployed': bool(a.get('airbagDeployed')),
             'damage_zones': a.get('damageZones', []),
             'description': a.get('description', '')}
            for a in accidents
        ]
        normalized_recalls = [
            {'recall_number': r.get('recall_number', ''),
             'component': r.get('component', ''),
             'summary': r.get('summary', ''),
             'remedy': r.get('remedy', ''),
             'is_open': r.get('is_open', True),
             'source': r.get('source', 'NHTSA')}
            for r in recalls
        ]
        market_value = raw.get('marketValue', {})
        market_value_usd = market_value.get('above', 0) if isinstance(market_value, dict) else 0
        uganda = check_uganda_import_eligibility(year) if year else {}

        return {
            'meta': {
                'source_country': 'USA',
                'identifier': raw.get('vin', basic_info.get('vin', '')),
                'identifier_type': 'VIN',
                'report_type': 'FULL',
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'data_providers': ['nhtsa', 'vinaudit'],
            },
            'vehicle': {
                'make': basic_info.get('make', attributes.get('make', '')),
                'model': basic_info.get('model', attributes.get('model', '')),
                'year': year,
                'trim': basic_info.get('trim', ''),
                'body_type': basic_info.get('body_type', ''),
                'engine': basic_info.get('engine', ''),
                'fuel_type': basic_info.get('fuel_type', ''),
                'drive_type': basic_info.get('drive_type', ''),
                'transmission': basic_info.get('transmission', ''),
                'doors': basic_info.get('doors'),
                'country_of_manufacture': basic_info.get('country_of_manufacture', 'USA'),
                'image_url': None,
            },
            'title_history': normalized_titles,
            'brands': brands,
            'odometer_records': normalized_odometer,
            'accidents': normalized_accidents,
            'total_loss': bool(raw.get('totalLoss') or any('TOTAL LOSS' in b for b in brands)),
            'theft': theft_records,
            'insurance_records': [],
            'recalls': normalized_recalls,
            'auction_history': None,
            'auction_grade': None,
            'shaken_expiry': None,
            'market_value': {'estimate_usd': market_value_usd, 'estimate_ugx': 0, 'source': 'vinaudit'},
            'uganda_eligibility': uganda,
        }

    def _normalize_otofacts(self, data: dict, basic_info: dict) -> dict:
        raw = data.get('raw', {})
        year = basic_info.get('year') or raw.get('year')
        uganda = check_uganda_import_eligibility(int(year)) if year else {}
        auction_history = raw.get('auction_history', [])
        auction_grade = auction_history[0].get('grade') if auction_history else None
        return {
            'meta': {'source_country': 'JAPAN', 'identifier_type': 'CHASSIS',
                     'report_type': 'FULL', 'data_providers': ['otofacts'],
                     'generated_at': datetime.now(timezone.utc).isoformat()},
            'vehicle': {
                'make': raw.get('make', basic_info.get('make', '')),
                'model': raw.get('model', basic_info.get('model', '')),
                'year': year, 'trim': raw.get('grade_name', ''),
                'body_type': raw.get('body_type', ''), 'engine': raw.get('engine_displacement', ''),
                'fuel_type': raw.get('fuel_type', ''), 'drive_type': raw.get('drive', ''),
                'transmission': raw.get('transmission', ''), 'doors': raw.get('doors'),
                'country_of_manufacture': 'Japan', 'image_url': None,
            },
            'title_history': [], 'brands': [],
            'odometer_records': [
                {'date': r.get('date', ''), 'reading': r.get('mileage', 0), 'unit': 'km', 'source': 'OtoFacts'}
                for r in raw.get('mileage_history', [])
            ],
            'accidents': [], 'total_loss': False, 'theft': [], 'insurance_records': [], 'recalls': [],
            'auction_history': auction_history, 'auction_grade': auction_grade,
            'shaken_expiry': raw.get('shaken_expiry'),
            'market_value': {'estimate_usd': 0, 'estimate_ugx': 0, 'source': 'otofacts'},
            'uganda_eligibility': uganda,
        }

    def _normalize_carcheck_jp(self, data: dict, basic_info: dict) -> dict:
        raw = data.get('raw', {})
        year = basic_info.get('year') or raw.get('year')
        uganda = check_uganda_import_eligibility(int(year)) if year else {}
        return {
            'meta': {'source_country': 'JAPAN', 'identifier_type': 'CHASSIS',
                     'report_type': 'FULL', 'data_providers': ['carcheck_jp'],
                     'generated_at': datetime.now(timezone.utc).isoformat()},
            'vehicle': {
                'make': raw.get('make', ''), 'model': raw.get('model', ''), 'year': year,
                'trim': raw.get('grade', ''), 'body_type': raw.get('body', ''),
                'engine': raw.get('engine', ''), 'fuel_type': raw.get('fuel', ''),
                'drive_type': raw.get('drive', ''), 'transmission': raw.get('transmission', ''),
                'doors': None, 'country_of_manufacture': 'Japan', 'image_url': raw.get('image_url'),
            },
            'title_history': [], 'brands': [], 'odometer_records': [], 'accidents': [],
            'total_loss': False, 'theft': [], 'insurance_records': [], 'recalls': [],
            'auction_history': raw.get('auction_records', []), 'auction_grade': raw.get('auction_grade'),
            'shaken_expiry': raw.get('shaken_expiry'),
            'market_value': {'estimate_usd': 0, 'estimate_ugx': 0, 'source': 'carcheck_jp'},
            'uganda_eligibility': uganda,
        }
