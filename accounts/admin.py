from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    model = User
    
    # Extend standard fieldsets to display role and mobile in admin edit page
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Role & Contact', {'fields': ('role', 'mobile')}),
    )
    
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'mobile', 'is_staff']
    list_filter = ['role', 'is_staff', 'is_superuser', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'mobile']
    ordering = ['username']

admin.site.register(User, CustomUserAdmin)
