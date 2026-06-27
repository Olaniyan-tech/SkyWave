from django.core.management import BaseCommand
from django.contrib.auth import get_user_model
from decouple import config


User = get_user_model()

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        username = config("ADMIN_USERNAME")
        email = config("ADMIN_EMAIL")
        password = config("ADMIN_PASSWORD")

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.ERROR("Superuser username already exists"))

        elif User.objects.filter(email=email).exists():
            self.stdout.write(self.style.ERROR("Superuser email already exists"))
        
        else:
            User.objects.create_superuser(username, email, password)
            self.stdout.write(self.style.SUCCESS("Superuser created successfully"))