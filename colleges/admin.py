from django.contrib import admin
from .models import College

@admin.register(College)
class CollegeAdmin(admin.ModelAdmin):
    list_display = [
        'college_code', 
        'college_name', 
        'email', 
        'used_pass', 
        'max_pass', 
        'status'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['college_name', 'college_code', 'email']
    readonly_fields = ['qr_token', 'qr_image', 'created_at']
    
    fieldsets = (
        ('College Details', {
            'fields': ('college_name', 'college_code', 'email', 'status')
        }),
        ('Pass Limits', {
            'fields': ('max_pass', 'used_pass')
        }),
        ('Security & System Generated QR', {
            'fields': ('qr_token', 'qr_image', 'created_at')
        }),
    )
