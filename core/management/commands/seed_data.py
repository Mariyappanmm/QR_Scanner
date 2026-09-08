from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from colleges.models import College
from core.utils import generate_college_qr

User = get_user_model()

class Command(BaseCommand):
    help = "Seed database with default user accounts and college records for testing"

    def handle(self, *args, **options):
        self.stdout.write("Seeding user accounts...")

        # 1. Seed Super Admin
        super_admin, created = User.objects.get_or_create(
            username="superadmin",
            defaults={
                "email": "superadmin@event.company.com",
                "first_name": "Super",
                "last_name": "Admin",
                "role": User.Role.SUPER_ADMIN,
                "is_staff": True,
                "is_superuser": True
            }
        )
        if created:
            super_admin.set_password("password123")
            super_admin.save()
            self.stdout.write(self.style.SUCCESS("Super Admin 'superadmin' created (password: password123)"))

        # 2. Seed Admin
        admin, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@event.company.com",
                "first_name": "Event",
                "last_name": "Manager",
                "role": User.Role.ADMIN,
                "is_staff": True
            }
        )
        if created:
            admin.set_password("password123")
            admin.save()
            self.stdout.write(self.style.SUCCESS("Admin 'admin' created (password: password123)"))

        # 3. Seed Volunteer
        volunteer, created = User.objects.get_or_create(
            username="john",
            defaults={
                "email": "john.volunteer@event.company.com",
                "first_name": "John",
                "last_name": "Volunteer",
                "role": User.Role.VOLUNTEER,
                "mobile": "9876543210"
            }
        )
        if created:
            volunteer.set_password("password123")
            volunteer.save()
            self.stdout.write(self.style.SUCCESS("Volunteer 'john' created (password: password123)"))

        # 4. Seed Colleges
        colleges_data = []

        self.stdout.write("Seeding colleges and generating QR codes...")
        for data in colleges_data:
            college, created = College.objects.get_or_create(
                college_code=data["college_code"],
                defaults={
                    "college_name": data["college_name"],
                    "email": data["email"],
                    "max_pass": data["max_pass"],
                    "used_pass": 0,
                    "status": College.Status.ACTIVE
                }
            )
            if created:
                generate_college_qr(college)
                self.stdout.write(self.style.SUCCESS(f"College '{college.college_name}' created and QR code generated."))

        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))
