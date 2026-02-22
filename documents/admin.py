from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, School, Document

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'get_role', 'school', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Roles', {'fields': ('is_deped_admin', 'is_deped_secretary', 'is_school_head', 'is_employee', 'school')}),
        ('Personal Info', {'fields': ('contact_number', 'address', 'position')}),
    )

admin.site.register(User, CustomUserAdmin)
admin.site.register(School)
admin.site.register(Document)