from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, DealerProfile


class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    phone_number = forms.CharField(max_length=20, required=False)

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'account_type', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email
        if commit:
            user.save()
        return user


class CustomUserUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'phone_number', 'country']


class DealerProfileForm(forms.ModelForm):
    class Meta:
        model = DealerProfile
        fields = ['business_name', 'registration_number', 'contact_email', 'contact_phone']
