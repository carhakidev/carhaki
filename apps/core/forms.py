from django import forms
from .models import ContactMessage, DealerApplication


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Your full name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'your@email.com'}),
            'phone': forms.TextInput(attrs={'placeholder': '+256 7XX XXX XXX'}),
            'message': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Tell us how we can help...'}),
        }


class DealerApplicationForm(forms.ModelForm):
    class Meta:
        model = DealerApplication
        fields = [
            'business_name', 'contact_person', 'email', 'phone',
            'physical_address', 'district', 'website',
            'monthly_sales_volume', 'how_did_you_hear', 'message',
        ]
        widgets = {
            'business_name': forms.TextInput(attrs={'placeholder': 'e.g. Kampala Auto Mart'}),
            'contact_person': forms.TextInput(attrs={'placeholder': 'Full name of primary contact'}),
            'email': forms.EmailInput(attrs={'placeholder': 'business@email.com'}),
            'phone': forms.TextInput(attrs={'placeholder': '+256 7XX XXX XXX'}),
            'physical_address': forms.TextInput(attrs={'placeholder': 'Plot number, street, area'}),
            'district': forms.TextInput(attrs={'placeholder': 'e.g. Kampala, Wakiso, Mbarara'}),
            'website': forms.URLInput(attrs={'placeholder': 'https://yourwebsite.com (optional)'}),
            'monthly_sales_volume': forms.Select(choices=[
                ('', 'Select range'),
                ('1-5', '1 to 5 vehicles per month'),
                ('6-15', '6 to 15 vehicles per month'),
                ('16-30', '16 to 30 vehicles per month'),
                ('31-50', '31 to 50 vehicles per month'),
                ('50+', 'More than 50 vehicles per month'),
            ]),
            'how_did_you_hear': forms.TextInput(attrs={'placeholder': 'e.g. Google, referral, social media'}),
            'message': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Any additional information about your dealership or questions about the program',
            }),
        }
