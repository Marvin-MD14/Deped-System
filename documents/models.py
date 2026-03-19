from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator

class UserManager(BaseUserManager):
    def create_user(self, email, full_name, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        extra_fields.setdefault('username', email)
        user = self.model(email=email, full_name=full_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_deped_admin', True)
        extra_fields.setdefault('is_active', True)
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
    email = models.EmailField(unique=True, verbose_name="Email Address")
    personal_email = models.EmailField(
        max_length=255, 
        verbose_name="Personal Gmail Address",
        help_text="Notifications for approval will be sent here.",
        null=True, blank=True
    )
    full_name = models.CharField(max_length=255, blank=True, null=True)
    
    objects = UserManager() 
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    is_deped_admin = models.BooleanField(default=False, verbose_name="Superadmin")
    is_deped_secretary = models.BooleanField(default=False, verbose_name="DepEd Secretary")
    is_school_head = models.BooleanField(default=False, verbose_name="School Head")
    is_employee = models.BooleanField(default=True, verbose_name="Employee")

    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female')], blank=True, null=True)
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    position = models.CharField(max_length=100, blank=True, null=True)
    contact_number = models.CharField(
        max_length=15, 
        blank=True, null=True,
        validators=[RegexValidator(r'^\+?63[0-9]{10}$', 'Enter valid PH mobile number (+639xxxxxxxxx)')]
    )
    address = models.TextField(blank=True, null=True)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    is_email_verified = models.BooleanField(default=False)

    class Meta:
        ordering = ['-date_joined']

    def save(self, *args, **kwargs):
        if self.email and not self.username:
            self.username = self.email
        if self.is_deped_admin:
            self.is_deped_secretary = self.is_school_head = self.is_employee = False
        elif self.is_deped_secretary:
            self.is_school_head = self.is_employee = False
        elif self.is_school_head:
            self.is_employee = False
        super().save(*args, **kwargs)

    @property
    def display_name(self):
        return self.full_name or self.email

    def __str__(self):
        return self.display_name

class Document(models.Model):
    # Idinagdag na Category para sa Dashboard Charts
    CATEGORY_CHOICES = [
        ('word', 'Word Document'),
        ('excel', 'Excel Spreadsheet'),
        ('ppt', 'PowerPoint Presentation'),
        ('pdf', 'PDF File'),
    ]

    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='memos/%Y/%m/%d/')
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='pdf') # <--- SOLUSYON SA FIELDERROR
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    date_uploaded = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    views_count = models.PositiveIntegerField(default=0)
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True, blank=True, related_name='documents')

    class Meta:
        verbose_name = "Document/Memo"
        ordering = ['-date_uploaded']

    def __str__(self):
        return f"{self.title} ({self.category})"

    def save(self, *args, **kwargs):
        if not self.school and self.uploaded_by.school:
            self.school = self.uploaded_by.school
        
        # Auto-category base sa file extension kung walang value
        if not self.category and self.file:
            ext = self.file.name.split('.')[-1].lower()
            if ext in ['doc', 'docx']: self.category = 'word'
            elif ext in ['xls', 'xlsx']: self.category = 'excel'
            elif ext in ['ppt', 'pptx']: self.category = 'ppt'
            else: self.category = 'pdf'
            
        super().save(*args, **kwargs)

class ReceivedDocument(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='deliveries')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_memos')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sent_memos') # <--- Idinagdag para sa Inbox tracking
    date_received = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Received Document"
        verbose_name_plural = "Received Documents"
        ordering = ['-date_received']

    def __str__(self):
        return f"{self.document.title} -> {self.recipient.display_name}"