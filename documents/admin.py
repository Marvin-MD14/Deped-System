from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, School, Document

class CustomUserAdmin(UserAdmin):
    model = User
    # In-update ang list_display: tinanggal ang 'get_role' at pinalitan ng email/full_name
    list_display = ('email', 'full_name', 'school', 'is_deped_admin', 'is_school_head', 'is_staff')
    list_filter = ('is_deped_admin', 'is_deped_secretary', 'is_school_head', 'is_staff', 'school')
    
    # Para makita ang custom fields sa edit page
    fieldsets = UserAdmin.fieldsets + (
        ('Roles & Access', {'fields': ('is_deped_admin', 'is_deped_secretary', 'is_school_head', 'is_employee', 'school')}),
        ('Personal Information', {'fields': ('personal_email', 'contact_number', 'position', 'gender', 'address')}),
        ('System Info', {'fields': ('last_login_ip', 'is_email_verified')}),
    )
    
    # Para sa "Add User" form sa admin panel
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Required Info', {'fields': ('full_name', 'email', 'personal_email')}),
    )

    ordering = ('email',)

# Registering models
admin.site.register(User, CustomUserAdmin)
admin.site.register(School)

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'uploaded_by', 'school', 'date_uploaded', 'is_active')
    list_filter = ('school', 'is_active', 'date_uploaded')
    search_fields = ('title', 'uploaded_by__email')