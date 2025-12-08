# core/management/commands/create_admin.py
import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = "Creates a superuser non-interactively if it doesn't exist"

    def handle(self, *args, **options):
        User = get_user_model()
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

        if not username or not password:
            self.stdout.write(self.style.WARNING("⚠️ Missing DJANGO_SUPERUSER_USERNAME or PASSWORD env vars. Skipping admin creation."))
            return

        if not User.objects.filter(username=username).exists():
            self.stdout.write(f"👤 Creating superuser: {username}...")
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS("✅ Superuser created successfully!"))
        else:
            self.stdout.write(self.style.SUCCESS("✅ Superuser already exists. Skipping."))