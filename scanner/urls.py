from django.urls import path
from . import views

urlpatterns = [
    path('', views.scanner_home, name='scanner_home'),
    path('verify/<str:token>/', views.scanner_verify, name='scanner_verify'),
]
