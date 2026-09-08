from django.contrib.auth.hashers import make_password


def create_default_users_signal(sender, **kwargs):
    """
    Post-migrate signal handler to ensure default users exist in any database environment.
    """
    try:
        from accounts.models import User
    except ImportError:
        return

    # 1. Super Admin
    if not User.objects.filter(username='superadmin').exists():
        User.objects.create(
            username='superadmin',
            email='superadmin@ras.com',
            password=make_password('superadmin123'),
            role=User.Role.SUPER_ADMIN,
            first_name='Super',
            last_name='Admin',
            is_staff=True,
            is_superuser=True,
            is_active=True
        )

    # 2. Admin
    if not User.objects.filter(username='admin').exists():
        User.objects.create(
            username='admin',
            email='admin@ras.com',
            password=make_password('admin123'),
            role=User.Role.ADMIN,
            first_name='System',
            last_name='Admin',
            is_staff=True,
            is_superuser=False,
            is_active=True
        )

    # 3. User / Volunteer
    if not User.objects.filter(username='John').exists():
        User.objects.create(
            username='John',
            email='user@ras.com',
            password=make_password('user123'),
            role=User.Role.VOLUNTEER,
            first_name='Standard',
            last_name='User',
            is_staff=False,
            is_superuser=False,
            is_active=True
        )
