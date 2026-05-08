import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Create a superuser from ADMIN_EMAIL / ADMIN_PASSWORD env vars (idempotent)'

    def handle(self, *args, **options):
        User = get_user_model()
        email = os.environ.get('ADMIN_EMAIL')
        password = os.environ.get('ADMIN_PASSWORD')

        if not email or not password:
            self.stdout.write('ADMIN_EMAIL or ADMIN_PASSWORD not set — skipping.')
            return

        if User.objects.filter(email=email).exists():
            self.stdout.write(f'Admin {email} already exists — skipping.')
            return

        User.objects.create_superuser(
            username=email,
            email=email,
            password=password,
            first_name='Admin',
            last_name='CarHaki',
        )
        self.stdout.write(self.style.SUCCESS(f'Superuser {email} created.'))
