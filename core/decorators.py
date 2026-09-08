from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

def admin_required(view_func):
    """
    Decorator for views that checks if the user is logged in and is an Admin or Super Admin.
    Throws PermissionDenied (HTTP 403) otherwise.
    """
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_admin():
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return _wrapped_view

def volunteer_required(view_func):
    """
    Decorator for views that checks if the user is authenticated (either Volunteer or Admin).
    Redirects to login page if not authenticated.
    """
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)
        return redirect('login')
    return _wrapped_view
