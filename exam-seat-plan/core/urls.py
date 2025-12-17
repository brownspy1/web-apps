from django.urls import path
from . import views, pdf_views

urlpatterns = [
    # Public Routes
    path('', views.public_search, name='public_search'),
    path('public/room/<int:room_id>/', views.public_room_view, name='public_room_view'),
    
    # Admin / Staff Routes
    path('dashboard/', views.dashboard, name='dashboard'),
    path('room/create/', views.room_create, name='room_create'),
    path('room/<int:room_id>/delete/', views.room_delete, name='room_delete'),
    path('room/<int:room_id>/edit/', views.room_edit, name='room_edit'),
    path('room/<int:room_id>/toggle/', views.toggle_seat, name='room_toggle_seat'),
    path('room/<int:room_id>/manage/', views.manage_seat, name='room_manage_seat'),
    path('room/<int:room_id>/', views.room_detail, name='room_detail'), # Admin interactive view
    path('allocate/', views.allocate_view, name='allocate_view'),
    path('api/analyze-image/', views.analyze_student_list, name='analyze_student_list'),
    path('manage-metadata/', views.manage_metadata, name='manage_metadata'),
    
    # Master Plan HTML
    path('master-plan/view/', views.master_plan_view, name='master_plan_view'),
    path('seats/allocate/', views.allocate_view, name='allocate_seats'),
    path('metadata/manage/', views.manage_metadata, name='manage_metadata'),
    
    # Student Management
    path('students/', views.manage_students, name='manage_students'),
    path('students/save/', views.student_save, name='student_save'),
    path('students/<int:student_id>/delete/', views.student_delete, name='student_delete'),
    path('students/bulk-delete/', views.student_bulk_delete, name='student_bulk_delete'),
    path('department/<int:dept_id>/delete/', views.department_delete, name='department_delete'),
    path('semester/<int:sem_id>/delete/', views.semester_delete, name='semester_delete'),
    
    # PDF Downloads (Legacy/Admin)
    path('room/<int:room_id>/pdf/', pdf_views.download_room_pdf, name='room_pdf'),
    path('room/<int:room_id>/attendance/', pdf_views.download_attendance_pdf, name='room_attendance_pdf'),
    path('master-plan/pdf/', pdf_views.download_master_plan_pdf, name='master_pdf'),
]
