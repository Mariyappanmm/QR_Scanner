from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_home, name='dashboard'),
    path('audit-logs/', views.audit_logs, name='audit_logs'),
]
