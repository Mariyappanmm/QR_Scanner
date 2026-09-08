from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    class Role(models.TextChoices):
        SUPER_ADMIN = 'SUPER_ADMIN', 'Super Admin'
        ADMIN = 'ADMIN', 'Admin'
        VOLUNTEER = 'VOLUNTEER', 'Volunteer'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.VOLUNTEER,
        help_text="Role of the user in the system"
    )
    mobile = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        help_text="Contact number of the volunteer or admin"
    )

    def is_super_admin(self):
        return self.role == self.Role.SUPER_ADMIN

    def is_admin(self):
        return self.role in [self.Role.ADMIN, self.Role.SUPER_ADMIN]

    def is_volunteer(self):
        return self.role == self.Role.VOLUNTEER

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
