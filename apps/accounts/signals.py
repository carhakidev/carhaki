from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser


@receiver(post_save, sender=CustomUser)
def handle_dealer_account_type(sender, instance, created, **kwargs):
    """When an existing user switches to DEALER type, prompt them to complete dealer profile."""
    pass
