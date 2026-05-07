from django import forms
from .validators import validate_vin, validate_chassis, detect_identifier_type


class VehicleSearchForm(forms.Form):
    identifier = forms.CharField(
        max_length=25,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter VIN or Chassis Number',
            'class': 'w-full px-4 py-3 text-lg rounded-lg border-0 focus:ring-2 focus:ring-ch-gold outline-none',
            'autocomplete': 'off',
            'autofocus': True,
        }),
        label='',
    )
    source_country = forms.ChoiceField(
        choices=[('USA', 'Imported from USA'), ('JAPAN', 'Imported from Japan')],
        widget=forms.RadioSelect(attrs={'class': 'hidden'}),
        initial='USA',
    )

    def clean_identifier(self):
        value = self.cleaned_data['identifier'].upper().strip().replace(' ', '').replace('-', '')
        return value

    def clean(self):
        cleaned = super().clean()
        identifier = cleaned.get('identifier', '')
        country = cleaned.get('source_country', 'USA')

        if identifier:
            id_type = detect_identifier_type(identifier)
            if id_type == 'VIN' and country == 'JAPAN':
                raise forms.ValidationError(
                    'That looks like a 17-digit VIN. Please select "Imported from USA" or enter a chassis number for Japan.'
                )
            if id_type == 'CHASSIS' and country == 'USA':
                raise forms.ValidationError(
                    'That looks like a chassis number. Please select "Imported from Japan".'
                )
            if id_type == 'VIN':
                try:
                    validate_vin(identifier)
                except forms.ValidationError as e:
                    self.add_error('identifier', e)
            elif id_type == 'CHASSIS':
                try:
                    validate_chassis(identifier)
                except forms.ValidationError as e:
                    self.add_error('identifier', e)
        return cleaned
