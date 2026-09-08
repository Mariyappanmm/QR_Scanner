from django.db import migrations
from django.contrib.auth.hashers import make_password


def create_default_users(apps, schema_editor):
    User = apps.get_model('accounts', 'User')

    # 1. Super Admin
    if not User.objects.filter(username='superadmin').exists():
        User.objects.create(
            username='superadmin',
            email='superadmin@ras.com',
            password=make_password('superadmin123'),
            role='SUPER_ADMIN',
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
            role='ADMIN',
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
            role='VOLUNTEER',
            first_name='Standard',
            last_name='User',
            is_staff=False,
            is_superuser=False,
            is_active=True
        )


def remove_default_users(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    User.objects.filter(username__in=['superadmin', 'admin', 'John']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_users, reverse_code=remove_default_users),
    ]
