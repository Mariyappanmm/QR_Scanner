from django.contrib import admin
from .models import ScanLog

@admin.register(ScanLog)
class ScanLogAdmin(admin.ModelAdmin):
    list_display = [
        'college', 
        'scan_number', 
        'status', 
        'scanned_by', 
        'scan_time', 
        'ip_address', 
        'location'
    ]
    list_filter = ['status', 'scan_time', 'location']
    search_fields = [
        'college__college_name', 
        'college__college_code', 
        'scanned_by__username', 
        'remarks', 
        'ip_address'
    ]
    readonly_fields = ['scan_time']
