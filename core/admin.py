from django.contrib import admin
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'action', 'ip_address']
    list_filter = ['timestamp', 'action']
    search_fields = ['user__username', 'action', 'details', 'ip_address']
    readonly_fields = ['timestamp']
