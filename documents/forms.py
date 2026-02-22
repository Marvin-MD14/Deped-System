from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, School


class EmployeeRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    full_name = forms.CharField(
        max_length=255, 
        label="Full Name",
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    gender = forms.ChoiceField(
        choices=[('Male', 'Male'), ('Female', 'Female')],
        label="Gender",
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    school = forms.ModelChoiceField(
        queryset=School.objects.all(),
        label="School/Office",
        required=True,
        empty_label="Select School/Office",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'data-toggle': 'password'
        }),
    )
    password2 = forms.CharField(
        label="Confirm Password",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'data-toggle': 'password'
        }),
    )

    class Meta:
        model = User
        fields = ("email", "full_name", "school", "gender", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove help texts for cleaner form
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def clean_password2(self):
        """Override to fix password mismatch issue"""
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("The two password fields didn't match.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Set username to email (as per your User model's save method)
        user.username = user.email
        user.full_name = self.cleaned_data["full_name"]
        user.gender = self.cleaned_data["gender"]
        user.school = self.cleaned_data["school"]
        user.is_employee = True
        user.is_deped_admin = False
        user.is_deped_secretary = False
        user.is_school_head = False

        if commit:
            user.save()
        
        return user
