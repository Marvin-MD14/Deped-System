from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from django.contrib.auth import get_user_model
from .models import User, School

# Kunin ang kasalukuyang User model
User = get_user_model()

# --- REGISTRATION FORM ---

class EmployeeRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        label="DepEd Email Address",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'name@deped.gov.ph'
        }),
        help_text="This will be used for your login username."
    )

    personal_email = forms.EmailField(
        label="Personal Gmail Address",
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'yourname@gmail.com'
        }),
        help_text="Notifications and password reset links will be sent here."
    )

    full_name = forms.CharField(
        max_length=255,
        label="Full Name",
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your full name'
        })
    )

    gender = forms.ChoiceField(
        choices=[('Male', 'Male'), ('Female', 'Female')],
        label="Gender",
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    school = forms.ModelChoiceField(
        queryset=School.objects.all(),
        label="School/Office",
        required=True,
        empty_label="Select School/Office",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '***********'
        }),
    )

    password2 = forms.CharField(
        label="Confirm Password",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '***********'
        }),
    )

    class Meta:
        model = User
        fields = ("email", "personal_email", "full_name", "school", "gender", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tanggalin ang default help texts ng Django para malinis ang UI
        if 'password1' in self.fields:
            self.fields['password1'].help_text = None
        if 'password2' in self.fields:
            self.fields['password2'].help_text = None

    def clean_email(self):
        """Siguraduhin na @deped.gov.ph ang gamit at unique."""
        email = self.cleaned_data.get('email').lower()
        if not email.endswith('@deped.gov.ph'):
            raise forms.ValidationError("Please use your official @deped.gov.ph email address.")
        
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This DepEd email is already registered.")
        return email

    def clean_personal_email(self):
        """Siguraduhin na Gmail ang recovery email."""
        p_email = self.cleaned_data.get('personal_email').lower()
        if not p_email.endswith('@gmail.com'):
            raise forms.ValidationError("Please provide a valid @gmail.com address for recovery.")
        return p_email

    def clean_password2(self):
        """Validation para sa pagtutugma ng password."""
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("The two password fields didn't match.")
        return password2

    def save(self, commit=True, is_admin_creation=False):
        user = super().save(commit=False)
        # Ang DepEd Email ang magsisilbing username at primary email
        user.username = self.cleaned_data["email"]
        user.email = self.cleaned_data["email"]
        
        # Karagdagang data
        user.personal_email = self.cleaned_data["personal_email"]
        user.full_name = self.cleaned_data["full_name"]
        user.gender = self.cleaned_data["gender"]
        user.school = self.cleaned_data["school"]

        user.is_employee = True
        
        # LOGIC: Kung Admin ang gumawa, Active agad. Kung self-register, Inactive (for approval).
        if is_admin_creation:
            user.is_active = True
        else:
            user.is_active = False

        if commit:
            user.save()
        return user

# --- PASSWORD RESET FORM (GMAIL RECOVERY LOGIC) ---

class CustomPasswordResetForm(PasswordResetForm):
    """
    Ito ang form na gagamitin sa Forgot Password.
    Customized ito para hanapin ang user gamit ang kanilang 
    Personal Gmail (personal_email field).
    """
    email = forms.EmailField(
        label="Personal Gmail Address",
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your registered @gmail.com'
        })
    )

    def get_users(self, email):
        """
        Overrides the default method to search in personal_email field
        instead of the primary email field.
        """
        active_users = User.objects.filter(
            personal_email__iexact=email, 
            is_active=True 
        )
        return active_users