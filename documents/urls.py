from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from .forms import CustomPasswordResetForm

urlpatterns = [
    # ==============================
    # --- AUTHENTICATION ---
    # ==============================
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    
    # ==============================
    # --- DASHBOARD SELECTOR ---
    # ==============================
    path('dashboard/', views.dashboard_selector, name='dashboard_selector'),

    # ==============================
    # --- DASHBOARD TYPES ---
    # ==============================
    # Super Admin Dashboard
    path('super-admin/', views.superadmin_dashboard, name='super_admin_dashboard'), 
    
    # Admin Panel
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    
    # School Head Dashboard
    path('school-head/', views.school_head_dashboard, name='school_head_dashboard'),

    # ==============================
    # --- MESSENGER / CHAT SYSTEM ---
    # ==============================
    # Ito ang kailangan para gumana ang Messenger sa Sidebar
    path('messenger/', views.internal_chat, name='internal_chat'),

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
    # --- PROFILE ---
    # ==============================
    path('profile/', views.employee_profile, name='employee_profile'),

    # ==============================
    # --- DOCUMENTS / MEMOS ---
    # ==============================
    path('memos/received/', views.received_documents, name='received_documents'),
    path('documents/my-uploads/', views.upload_document, name='upload_document'),
    path('documents/delete/<int:doc_id>/', views.delete_document, name='delete_document'),
    path('documents/send/', views.send_document, name='send_document'), 
    
    # ==============================
    # --- PASSWORD RESET (GMAIL BASED) ---
    # ==============================
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='password_reset.html',
             form_class=CustomPasswordResetForm,
             email_template_name='password_reset_email.html',
             subject_template_name='password_reset_subject.txt'
         ), 
         name='password_reset'),
         
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='password_reset_done.html'
         ), 
         name='password_reset_done'),
         
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='password_reset_confirm.html'
         ), 
         name='password_reset_confirm'),
         
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='password_reset_complete.html'
         ), 
         name='password_reset_complete'),
]

# Helper for Media and Static files during Development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)