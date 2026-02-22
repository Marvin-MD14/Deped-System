from django.urls import path
from . import views

urlpatterns = [
    # Ito dapat ang gamitin para sa custom logic at error messages
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard_selector, name='dashboard_selector'),
    path('profile/', views.employee_profile, name='employee_profile'),
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('school-head/', views.school_head_dashboard, name='school_head_dashboard'),
]