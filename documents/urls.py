from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Authentication Routes
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    
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