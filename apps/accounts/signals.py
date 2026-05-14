"""
accounts/signals.py

Signals for the accounts app.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import CustomUser, DealerProfile


@receiver(post_save, sender=CustomUser)
def handle_dealer_account_type(sender, instance, created, **kwargs):
    """
    When an existing user switches their account_type to DEALER:
      1. Create a blank DealerProfile shell if one doesn't already exist.
      2. The profile starts unapproved (is_approved=False) — admin must approve.

    Note: we do NOT redirect here (signals have no request context).
    The redirect to dealer_register is handled in ProfileView.form_valid()
    — see accounts/views.py.
    """
    if instance.account_type == CustomUser.DEALER:
        # create_or_ignore: only create if no DealerProfile exists yet
        if not DealerProfile.objects.filter(user=instance).exists():
            DealerProfile.objects.create(
                user=instance,
                business_name='',          # user fills this in on dealer_register
                contact_email=instance.email,
                contact_phone=instance.phone_number or '',
                credit_balance=0,
                is_approved=False,
            )