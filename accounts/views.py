from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from .forms import BootstrapLoginForm

class CustomLoginView(LoginView):
    form_class = BootstrapLoginForm
    template_name = 'accounts/login.html'
    
    def get(self, request, *args, **kwargs):
        # Redirect already logged-in users
        if request.user.is_authenticated:
            if request.user.is_admin():
                return redirect('dashboard')
            else:
                return redirect('scanner_home')
        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        user = self.request.user
        if user.is_admin():
            return reverse_lazy('dashboard')
        return reverse_lazy('scanner_home')
