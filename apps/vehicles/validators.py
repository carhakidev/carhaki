import re
from datetime import date
from django import forms


VIN_PATTERN = re.compile(r'^[A-HJ-NPR-Z0-9]{17}$')
CHASSIS_PATTERN = re.compile(r'^[A-Z0-9]{6,14}$')
UGANDA_MAX_VEHICLE_AGE = 15


def validate_vin(value: str) -> str:
    value = value.upper().strip()
    if not VIN_PATTERN.match(value):
        raise forms.ValidationError(
            'Invalid VIN. A VIN must be exactly 17 characters and cannot contain I, O, or Q.'
        )
    return value


def validate_chassis(value: str) -> str:
    value = value.upper().strip()
    if not CHASSIS_PATTERN.match(value):
        raise forms.ValidationError(
            'Invalid chassis number. Must be 6–14 alphanumeric characters (e.g. NZE141-6048723).'
        )
    return value


def detect_identifier_type(value: str) -> str:
    value = value.upper().strip().replace('-', '').replace(' ', '')
    if len(value) == 17 and VIN_PATTERN.match(value):
        return 'VIN'
    return 'CHASSIS'


def check_uganda_import_eligibility(year: int) -> dict:
    current_year = date.today().year
    age = current_year - year
    eligible = age <= UGANDA_MAX_VEHICLE_AGE
    return {
        'eligible': eligible,
        'vehicle_age_years': age,
        'max_allowed_years': UGANDA_MAX_VEHICLE_AGE,
        'note': (
            f'Within the {UGANDA_MAX_VEHICLE_AGE}-year URA import limit.'
            if eligible
            else f'This vehicle is {age} years old and exceeds Uganda\'s {UGANDA_MAX_VEHICLE_AGE}-year import restriction.'
        ),
    }
