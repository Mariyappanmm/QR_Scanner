from django.urls import path
from . import views

urlpatterns = [
    path('', views.college_list, name='college_list'),
    path('create/', views.college_create, name='college_create'),
    path('<int:pk>/', views.college_detail, name='college_detail'),
    path('<int:pk>/edit/', views.college_edit, name='college_edit'),
    path('<int:pk>/delete/', views.college_delete, name='college_delete'),
    path('<int:pk>/qr/download/', views.college_qr_download, name='college_qr_download'),
    path('<int:pk>/qr/email/', views.college_qr_email, name='college_qr_email'),
    path('import/excel/', views.colleges_import_excel, name='colleges_import_excel'),
    path('export/excel/', views.colleges_export_excel, name='colleges_export_excel'),
    path('email-all/', views.colleges_bulk_email_qr, name='colleges_bulk_email_qr'),
]
