from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
<<<<<<< HEAD
from django.conf import settings
from django.conf.urls.static import static
from .forms import CustomPasswordResetForm

urlpatterns = [
    # ==============================
    # --- AUTHENTICATION ---
    # ==============================
=======

urlpatterns = [
    # Authentication Routes
>>>>>>> 2a655c12c6c8b21f5a50521e333da5482ea0df0f
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    
<<<<<<< HEAD
    # ==============================
    # --- DASHBOARDS ---
    # ==============================
    path('dashboard/', views.dashboard_selector, name='dashboard_selector'),
    path('super-admin/', views.super_admin_dashboard, name='super_admin_dashboard'),
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('school-head/', views.school_head_dashboard, name='school_head_dashboard'),

    # ==============================
    # --- USER MANAGEMENT (SUPER ADMIN) ---
    # ==============================
    path('super-admin/users/', views.user_management, name='user_management'),
    path('super-admin/add-user/', views.add_user, name='add_user'),
    path('super-admin/edit-user/<int:user_id>/', views.edit_user, name='edit_user'),
    path('super-admin/delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('super-admin/access-requests/', views.access_requests, name='access_requests'),
    
    path('super-admin/pending-approvals/', views.pending_approvals, name='pending_approvals'),
    path('super-admin/approve-user/<int:user_id>/<str:action>/', views.approve_user_process, name='approve_user_process'),
    
    # ==============================
    # --- EMPLOYEE PROFILE ---
    # ==============================
    path('profile/', views.employee_profile, name='employee_profile'),

    # ==============================
    # --- DOCUMENTS ---
    # ==============================
    path('memos/received/', views.received_documents, name='received_documents'),
    
    # ==============================
    # --- PASSWORD RESET (GMAIL BASED) ---
    # ==============================
    # 1. Page kung saan itatype ang email
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='password_reset.html',
             form_class=CustomPasswordResetForm,
             email_template_name='password_reset_email.html',
             subject_template_name='password_reset_subject.txt'
         ), 
         name='password_reset'),
         
    # 2. Page na magsasabing "Check your email"
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='password_reset_done.html'
         ), 
         name='password_reset_done'),
         
    # 3. Ang link na iki-click mula sa email (UID at Token)
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='password_reset_confirm.html'
         ), 
         name='password_reset_confirm'),
         
    # 4. Page na lalabas pagkatapos ma-update ang password
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='password_reset_complete.html'
         ), 
         name='password_reset_complete'),
]

# Media at Static files handling
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
=======
    # Dashboard Selector
    path('dashboard/', views.dashboard_selector, name='dashboard_selector'),
    
    # Role-Based Dashboards
    path('superadmin-panel/', views.superadmin_dashboard, name='superadmin_dashboard'),
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('school-head/', views.school_head_dashboard, name='school_head_dashboard'),
    path('profile/', views.employee_profile, name='employee_profile'),

    # Master Files / Documents
    path('superadmin/all-documents/', views.all_documents, name='all_documents'),

    # Password Reset Routes
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(template_name='password_reset.html'), 
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), 
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), 
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), 
         name='password_reset_complete'),
     path('superadmin/access-requests/', views.superadmin_dashboard, name='access_requests'),
]
>>>>>>> 2a655c12c6c8b21f5a50521e333da5482ea0df0f
