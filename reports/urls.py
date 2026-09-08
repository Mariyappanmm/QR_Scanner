from django.urls import path
from . import views

urlpatterns = [
    path('', views.reports_home, name='reports_home'),
    path('export/attendance/', views.export_attendance_excel, name='export_attendance_excel'),
    path('export/rejected/', views.export_rejected_excel, name='export_rejected_excel'),
    path('export/volunteer/', views.export_volunteer_excel, name='export_volunteer_excel'),
    path('export/pdf/report/', views.export_pdf_report, name='export_pdf_report'),
    path('export/pdf/passes/', views.export_pdf_passes, name='export_pdf_passes'),
]
