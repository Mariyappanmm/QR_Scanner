from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.paginator import Paginator

from core.decorators import admin_required
from colleges.models import College
from scanner.models import ScanLog
from core.models import AuditLog

@login_required
@admin_required
def dashboard_home(request):
    """
    Computes registration numbers and renders the main admin dashboard page.
    """
    total_colleges = College.objects.count()
    total_passes = sum(c.max_pass for c in College.objects.all())
    used_passes = sum(c.used_pass for c in College.objects.all())
    remaining_passes = max(0, total_passes - used_passes)
    
    rejected_entries = ScanLog.objects.filter(status='Denied').count()
    
    today = timezone.now().date()
    today_entries = ScanLog.objects.filter(status='Allowed', scan_time__date=today).count()
    
    # Recent 10 scans
    recent_scans = ScanLog.objects.select_related('college', 'scanned_by')[:10]
    
    context = {
        'total_colleges': total_colleges,
        'total_passes': total_passes,
        'used_passes': used_passes,
        'remaining_passes': remaining_passes,
        'rejected_entries': rejected_entries,
        'today_entries': today_entries,
        'recent_scans': recent_scans,
    }
    return render(request, 'dashboard/index.html', context)

@login_required
@admin_required
def audit_logs(request):
    """
    Renders administrative audit log activity list with pagination.
    """
    logs_list = AuditLog.objects.select_related('user').all()
    paginator = Paginator(logs_list, 20)  # Show 20 records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'dashboard/audit_logs.html', {'page_obj': page_obj})
