from django import forms
from django.contrib.auth.forms import AuthenticationForm

class BootstrapLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Enter your username',
                'id': 'username_field'
            }
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Enter your password',
                'id': 'password_field'
            }
        )
    )
