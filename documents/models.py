from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator

class UserManager(BaseUserManager):
    def create_user(self, email, full_name, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        
        # Siguraduhin na ang username ay kapareho ng email para sa AbstractUser compatibility
        extra_fields.setdefault('username', email)
        
        user = self.model(email=email, full_name=full_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_deped_admin', True) # Default role bilang Superadmin

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, full_name, password, **extra_fields)


class School(models.Model):
    name = models.CharField(max_length=255, unique=True)
    school_id = models.CharField(
        max_length=50, 
        unique=True,
        validators=[RegexValidator(r'^[A-Z0-9-]+$', 'School ID must be uppercase letters, numbers, and hyphens only')]
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "School/Office"
        verbose_name_plural = "Schools/Offices"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.school_id})"


class User(AbstractUser):
    # Authentication - email as primary identifier (@deped.gov.ph)
    email = models.EmailField(unique=True, verbose_name="Email Address")
    
    # Notification Email - Para sa Gmail/Personal notifications
    personal_email = models.EmailField(
        max_length=255, 
        verbose_name="Personal Gmail Address",
        help_text="Notifications for approval will be sent here."
    )
    
    full_name = models.CharField(max_length=255, blank=True, null=True)
    
    # Kinokonekta ang Custom UserManager
    objects = UserManager() 
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'personal_email'] 

    # Roles - mutually exclusive with priority
    is_deped_admin = models.BooleanField(default=False, verbose_name="Superadmin")
    is_deped_secretary = models.BooleanField(default=False, verbose_name="DepEd Secretary")
    is_school_head = models.BooleanField(default=False, verbose_name="School Head")
    is_employee = models.BooleanField(default=True, verbose_name="Employee")

    # Personal Information
    gender = models.CharField(
        max_length=10, 
        choices=[('Male', 'Male'), ('Female', 'Female')],
        blank=True, 
        null=True
    )
    school = models.ForeignKey(
        School, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='users'
    )
    position = models.CharField(max_length=100, blank=True)
    contact_number = models.CharField(
        max_length=15, 
        blank=True,
        validators=[RegexValidator(r'^\+?63[0-9]{10}$', 'Enter valid PH mobile number (+639xxxxxxxxx)')]
    )
    address = models.TextField(blank=True)
    
    # Timestamps
    date_joined = models.DateTimeField(default=timezone.now)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    is_email_verified = models.BooleanField(default=False)

    class Meta:
        ordering = ['-date_joined']

    def save(self, *args, **kwargs):
        # Auto-set username to email
        if self.email and not self.username:
            self.username = self.email
        
        # Ensure only one role is active (priority: admin > secretary > head > employee)
        if self.is_deped_admin:
            self.is_deped_secretary = False
            self.is_school_head = False
            self.is_employee = False
        elif self.is_deped_secretary:
            self.is_school_head = False
            self.is_employee = False
        elif self.is_school_head:
            self.is_employee = False
        
        super().save(*args, **kwargs)

    def get_role(self):
        """Returns primary role with priority"""
        if self.is_deped_admin:
            return "Superadmin"
        if self.is_deped_secretary:
            return "DepEd Secretary"
        if self.is_school_head:
            return "School Head"
        return "Employee"

    def is_school_staff(self):
        """Check if user belongs to a school"""
        return bool(self.school and self.school.is_active)

    def has_school_access(self, school_id):
        """Check if user can access specific school"""
        if self.is_deped_admin or self.is_deped_secretary:
            return True
        return self.school_id == school_id

    @property
    def display_name(self):
        return self.full_name or self.email

    def __str__(self):
        return self.display_name


class Document(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='memos/%Y/%m/%d/')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    date_uploaded = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    views_count = models.PositiveIntegerField(default=0)
    
    # For school-specific memos
    school = models.ForeignKey(
        School, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='documents'
    )

    class Meta:
        ordering = ['-date_uploaded']

    def __str__(self):
        return f"{self.title} by {self.uploaded_by.display_name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Auto-set school from uploader if not specified
        if not self.school and self.uploaded_by.school:
            self.school = self.uploaded_by.school
            super().save(update_fields=['school'])