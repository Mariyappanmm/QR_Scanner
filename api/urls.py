from django.urls import path
from . import views

urlpatterns = [
    path('scan/', views.scan_api, name='api_scan'),
    path('dashboard-stats/', views.dashboard_stats_api, name='api_dashboard_stats'),
    path('recent-entries/', views.recent_entries_api, name='api_recent_entries'),
    path('college-search/', views.college_search_api, name='api_college_search'),
    path('generate-qr/<int:college_id>/', views.generate_qr_api, name='api_generate_qr'),
    path('charts/', views.chart_data_api, name='api_charts'),
]
