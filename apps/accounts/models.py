import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    INDIVIDUAL = 'INDIVIDUAL'
    DEALER = 'DEALER'
    BANK = 'BANK'
    INSURANCE = 'INSURANCE'
    MECHANIC = 'MECHANIC'

    ACCOUNT_TYPE_CHOICES = [
        (INDIVIDUAL, 'Individual Buyer'),
        (DEALER, 'Car Dealer / Importer'),
        (BANK, 'Bank / Microfinance'),
        (INSURANCE, 'Insurance Company'),
        (MECHANIC, 'Mechanic / Inspector'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=50, default='Uganda')
    account_type = models.CharField(
        max_length=20, choices=ACCOUNT_TYPE_CHOICES, default=INDIVIDUAL
    )
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'.strip() or self.email

    @property
    def is_dealer(self):
        return self.account_type == self.DEALER

    @property
    def dealer_credit_balance(self):
        if hasattr(self, 'dealer_profile'):
            return self.dealer_profile.credit_balance
        return 0


class DealerProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name='dealer_profile'
    )
    business_name = models.CharField(max_length=200)
    registration_number = models.CharField(max_length=100, blank=True)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20)
    credit_balance = models.PositiveIntegerField(default=0)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Dealer Profile'
        verbose_name_plural = 'Dealer Profiles'

    def __str__(self):
        return self.business_name

    def deduct_credit(self):
        if self.credit_balance > 0:
            self.credit_balance -= 1
            self.save(update_fields=['credit_balance'])
            return True
        return False
