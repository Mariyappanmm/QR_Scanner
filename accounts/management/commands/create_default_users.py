from django.core.management.base import BaseCommand
from accounts.models import User
from django.contrib.auth.hashers import make_password


class Command(BaseCommand):
    help = 'Creates or resets default users: superadmin, admin, and user (volunteer)'

    def handle(self, *args, **options):
        users_data = [
            {
                'username': 'superadmin',
                'email': 'superadmin@ras.com',
                'password': 'superadmin123',
                'role': User.Role.SUPER_ADMIN,
                'first_name': 'Super',
                'last_name': 'Admin',
                'is_staff': True,
                'is_superuser': True,
            },
            {
                'username': 'admin',
                'email': 'admin@ras.com',
                'password': 'admin123',
                'role': User.Role.ADMIN,
                'first_name': 'System',
                'last_name': 'Admin',
                'is_staff': True,
                'is_superuser': False,
            },
            {
                'username': 'John',
                'email': 'user@ras.com',
                'password': 'user123',
                'role': User.Role.VOLUNTEER,
                'first_name': 'Standard',
                'last_name': 'User',
                'is_staff': False,
                'is_superuser': False,
            }
        ]

        for user_info in users_data:
            username = user_info['username']
            password = user_info.pop('password')
            user, created = User.objects.get_or_create(
                username=username,
                defaults={**user_info, 'password': make_password(password)}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"✔ Created default user: {username} ({user.get_role_display()})"))
            else:
                self.stdout.write(self.style.WARNING(f"ℹ User '{username}' already exists."))
