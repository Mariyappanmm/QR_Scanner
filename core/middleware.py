from .models import AuditLog

class AuditLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # We log state-modifying actions (POST, DELETE) done by authenticated administrative users.
        if request.method in ['POST', 'DELETE'] and request.user and request.user.is_authenticated:
            path = request.path
            # Determine if this path is administrative or related to managing resources
            is_admin_action = any(prefix in path for prefix in ['/colleges/', '/reports/', '/accounts/', '/api/colleges/'])
            
            # Avoid duplicate logs for scan verification API which logs separately in ScanLog
            is_scan_api = '/api/scan/' in path

            if is_admin_action and not is_scan_api:
                # Build detail description
                post_data = request.POST.copy()
                if 'password' in post_data:
                    post_data['password'] = '******'
                if 'csrfmiddlewaretoken' in post_data:
                    del post_data['csrfmiddlewaretoken']

                action_name = f"{request.method} request on {path}"
                details = f"Params: {dict(post_data.items())}"

                # Extract client IP
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip = x_forwarded_for.split(',')[0]
                else:
                    ip = request.META.get('REMOTE_ADDR')

                AuditLog.objects.create(
                    user=request.user,
                    action=action_name[:255],
                    details=details,
                    ip_address=ip
                )

        return response
