from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import uuid

from core.decorators import volunteer_required, admin_required
from colleges.models import College
from scanner.models import ScanLog
from core.utils import generate_college_qr

@csrf_exempt
@login_required
@volunteer_required
def scan_api(request):
    """
    REST API Endpoint to verify a scanned QR token and record entry.
    POST parameter: 'token' (UUID string)
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed.'}, status=405)
        
    token_str = request.POST.get('token', '').strip()
    if not token_str:
        return JsonResponse({'error': 'Token parameter is required.'}, status=400)
        
    try:
        token_uuid = uuid.UUID(token_str)
        college = College.objects.get(qr_token=token_uuid)
    except (ValueError, College.DoesNotExist):
        return JsonResponse({
            'status': 'Denied',
            'error_message': 'Invalid QR Token - College not found'
        }, status=404)
        
    # Get user agent and client IP
    user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    ip_address = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR', '0.0.0.0')

    with transaction.atomic():
        # lock row to prevent double entry race conditions
        college = College.objects.select_for_update().get(pk=college.pk)
        
        status = 'Allowed'
        remarks = ''
        scan_number = 0
        
        if college.status == College.Status.INACTIVE:
            status = 'Denied'
            remarks = 'College Status Inactive'
            scan_number = college.used_pass + 1
        elif college.is_limit_reached():
            status = 'Denied'
            remarks = 'Pass Limit Exceeded'
            scan_number = college.used_pass + 1
        else:
            college.used_pass += 1
            college.save()
            scan_number = college.used_pass
            remarks = f"Delegate {scan_number} of {college.max_pass} checked-in."
            
        log = ScanLog.objects.create(
            college=college,
            scan_number=scan_number,
            scanned_by=request.user,
            scanner_device=user_agent[:255],
            ip_address=ip_address,
            location="Main Entrance (API)",
            status=status,
            remarks=remarks
        )

    # Trigger WebSocket Broadcast
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'dashboard_group',
            {
                'type': 'dashboard_update',
                'data': {
                    'event': 'scan',
                    'log': {
                        'time': log.scan_time.strftime('%I:%M %p'),
                        'college_name': college.college_name,
                        'college_code': college.college_code,
                        'status': log.status,
                        'volunteer': request.user.first_name or request.user.username,
                        'remaining': college.remaining_passes(),
                    }
                }
            }
        )
    except Exception:
        pass

    return JsonResponse({
        'status': log.status,
        'college_name': college.college_name,
        'college_code': college.college_code,
        'scan_number': log.scan_number,
        'max_pass': college.max_pass,
        'used_pass': college.used_pass,
        'remaining_passes': college.remaining_passes(),
        'remarks': log.remarks
    })

@login_required
@admin_required
def dashboard_stats_api(request):
    """
    Returns live statistics counts for the dashboard cards.
    """
    total_colleges = College.objects.count()
    total_passes = sum(c.max_pass for c in College.objects.all())
    used_passes = sum(c.used_pass for c in College.objects.all())
    remaining_passes = max(0, total_passes - used_passes)
    
    rejected_entries = ScanLog.objects.filter(status='Denied').count()
    today = timezone.now().date()
    today_entries = ScanLog.objects.filter(status='Allowed', scan_time__date=today).count()
    
    # Calculate hourly entries for chart
    hourly_data = {}
    today_logs = ScanLog.objects.filter(status='Allowed', scan_time__date=today)
    for l in today_logs:
        hour_str = l.scan_time.astimezone(timezone.get_current_timezone()).strftime('%I %p')
        hourly_data[hour_str] = hourly_data.get(hour_str, 0) + 1
        
    return JsonResponse({
        'total_colleges': total_colleges,
        'total_passes': total_passes,
        'used_passes': used_passes,
        'remaining_passes': remaining_passes,
        'rejected_entries': rejected_entries,
        'today_entries': today_entries,
        'hourly_chart': hourly_data
    })

@login_required
@admin_required
def recent_entries_api(request):
    """
    Returns the recent 20 scan log entries.
    """
    logs = ScanLog.objects.select_related('college', 'scanned_by')[:20]
    data = []
    for log in logs:
        data.append({
            'time': log.scan_time.astimezone(timezone.get_current_timezone()).strftime('%I:%M %p'),
            'college_name': log.college.college_name,
            'college_code': log.college.college_code,
            'status': log.status,
            'volunteer': log.scanned_by.first_name if log.scanned_by else 'System',
            'remaining': log.college.remaining_passes(),
            'remarks': log.remarks
        })
    return JsonResponse({'entries': data})

@login_required
@admin_required
def college_search_api(request):
    """
    API to search for colleges using a query parameter.
    """
    q = request.GET.get('q', '').strip()
    colleges = College.objects.all()
    if q:
        colleges = colleges.filter(college_name__icontains=q) | colleges.filter(college_code__icontains=q)
        
    data = []
    for c in colleges[:10]:  # Limit to 10 results
        data.append({
            'id': c.id,
            'college_name': c.college_name,
            'college_code': c.college_code,
            'used_pass': c.used_pass,
            'max_pass': c.max_pass,
            'status': c.status
        })
    return JsonResponse({'colleges': data})

@login_required
@admin_required
def generate_qr_api(request, college_id):
    """
    Triggers QR Code image regeneration for a specific college.
    """
    college = get_object_or_404(College, pk=college_id)
    generate_college_qr(college)
    return JsonResponse({
        'success': True,
        'message': f"QR Code successfully generated for {college.college_name}",
        'qr_image_url': college.qr_image.url if college.qr_image else ''
    })

@login_required
@admin_required
def chart_data_api(request):
    """
    Returns aggregated data for rendering the various Chart.js dashboard charts.
    """
    # 1. Allowed vs Denied count
    allowed_count = ScanLog.objects.filter(status='Allowed').count()
    denied_count = ScanLog.objects.filter(status='Denied').count()
    
    # 2. Pass utilization distribution
    unutilised = sum(c.remaining_passes() for c in College.objects.all())
    utilised = sum(c.used_pass for c in College.objects.all())
    
    # 3. Top colleges (highest attendance)
    top_colleges = College.objects.filter(used_pass__gt=0).order_by('-used_pass')[:5]
    top_colleges_labels = [c.college_code for c in top_colleges]
    top_colleges_values = [c.used_pass for c in top_colleges]
    
    return JsonResponse({
        'allowed_vs_denied': {
            'labels': ['Allowed Entries', 'Denied Attempts'],
            'data': [allowed_count, denied_count]
        },
        'pass_utilization': {
            'labels': ['Used Passes', 'Unused Passes'],
            'data': [utilised, unutilised]
        },
        'top_colleges': {
            'labels': top_colleges_labels,
            'data': top_colleges_values
        }
    })
