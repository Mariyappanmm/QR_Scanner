from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import uuid

from core.decorators import volunteer_required
from colleges.models import College
from .models import ScanLog

@login_required
@volunteer_required
def scanner_home(request):
    """
    Renders the QR scanner camera screen.
    Only accessible to authenticated Volunteers/Admins.
    """
    return render(request, 'scanner/index.html')

@login_required
@volunteer_required
def scanner_verify(request, token):
    """
    Validates the UUID token parsed from scanned QR,
    handles atomic limit checks, updates database, and broadcasts updates.
    """
    # 1. Fetch details of client device and IP
    user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(',')[0]
    else:
        ip_address = request.META.get('REMOTE_ADDR', '0.0.0.0')

    # Try to find the college by UUID
    try:
        token_uuid = uuid.UUID(str(token))
        college = College.objects.get(qr_token=token_uuid)
        is_valid_token = True
    except (ValueError, College.DoesNotExist):
        is_valid_token = False

    # 2. Handle invalid token scan
    if not is_valid_token:
        context = {
            'status': 'Denied',
            'error_title': 'INVALID QR CODE',
            'error_message': 'The scanned QR code is invalid or does not belong to any registered college.',
            'college_name': 'Unknown / Fake Pass',
            'remaining_pass': 0,
            'max_pass': 0,
            'used_pass': 0,
            'scan_time': timezone.now().strftime('%I:%M %p'),
            'volunteer': request.user.first_name or request.user.username
        }
        return render(request, 'scanner/verify.html', context)

    # 3. Process token verification in an atomic database transaction
    with transaction.atomic():
        # lock the college row to prevent parallel scan race conditions
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
            # Entry allowed
            college.used_pass += 1
            college.save()
            scan_number = college.used_pass
            remarks = f"Delegate {scan_number} of {college.max_pass} checked-in."
            
        # Create scan log record
        log = ScanLog.objects.create(
            college=college,
            scan_number=scan_number,
            scanned_by=request.user,
            scanner_device=user_agent[:255],
            ip_address=ip_address,
            location="Main Entrance",
            status=status,
            remarks=remarks
        )

    # 4. Broadcast real-time update to dashboard group via WebSockets
    try:
        channel_layer = get_channel_layer()
        # Recalculate stats counters to push
        total_colleges = College.objects.count()
        total_passes = sum(c.max_pass for c in College.objects.all())
        used_passes = sum(c.used_pass for c in College.objects.all())
        remaining_passes = max(0, total_passes - used_passes)
        rejected_entries = ScanLog.objects.filter(status='Denied').count()
        today_entries = ScanLog.objects.filter(status='Allowed', scan_time__date=timezone.now().date()).count()

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
                    },
                    'stats': {
                        'total_colleges': total_colleges,
                        'total_passes': total_passes,
                        'used_passes': used_passes,
                        'remaining_passes': remaining_passes,
                        'rejected_entries': rejected_entries,
                        'today_entries': today_entries
                    }
                }
            }
        )
    except Exception as e:
        # Channels layer not running or redis down, will fall back gracefully to AJAX polling
        pass

    # 5. Render confirmation screen
    context = {
        'status': status,
        'college_name': college.college_name,
        'college_code': college.college_code,
        'scan_number': scan_number,
        'max_pass': college.max_pass,
        'used_pass': college.used_pass,
        'remaining_pass': college.remaining_passes(),
        'scan_time': log.scan_time.strftime('%I:%M %p'),
        'volunteer': request.user.first_name or request.user.username,
        'error_title': 'ENTRY DENIED' if college.status == College.Status.ACTIVE else 'COLLEGE INACTIVE',
        'error_message': 'Maximum delegate passes for this college have already been checked-in.' if college.status == College.Status.ACTIVE else 'This college has been deactivated by event administrators.'
    }
    return render(request, 'scanner/verify.html', context)
