from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from django.urls import reverse

# Imports para sa Email
from django.core.mail import send_mail
from django.conf import settings

# Imports para sa Password Reset (Built-in Views)
from django.contrib.auth import views as auth_views

# Imports para sa models at forms
from .models import User, School, Document
from .forms import EmployeeRegistrationForm, CustomPasswordResetForm

# Kunin ang official User model
User = get_user_model()

# Helper function para sa decorators
def is_super_admin(user):
    return user.is_authenticated and user.is_superuser

# --- AUTHENTICATION VIEWS ---

@never_cache
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_selector')

    if request.method == 'POST':
        u = request.POST.get('username') 
        p = request.POST.get('password')
        remember_me = request.POST.get('remember')

        # Check muna kung ang email ay DepEd o kung Superuser
        check_user = User.objects.filter(email__iexact=u).first()
        is_super = check_user.is_superuser if check_user else False

        if u and not u.lower().endswith('@deped.gov.ph') and not is_super:
            messages.error(request, "Access Denied. Only official DepEd email addresses (@deped.gov.ph) are allowed.")
            return render(request, 'login.html')

        user = authenticate(request, username=u, password=p)

        if user is not None:
            if user.is_active:
                login(request, user)
                if remember_me:
                    request.session.set_expiry(1209600) # 2 weeks
                else:
                    request.session.set_expiry(0) 
                return redirect('dashboard_selector')
            else:
                messages.error(request, "Account disabled or pending approval. Please contact the ICT Unit.")
        else:
            messages.error(request, "Incorrect email or password. Please try again.")
            
    return render(request, 'login.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

@never_cache
def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_selector')

    if request.method == 'POST':
        form = EmployeeRegistrationForm(request.POST)
        if form.is_valid():
            # Ang validation ng @deped at @gmail ay handle na ng Form
            user = form.save() 
            messages.success(request, f'Welcome {user.full_name}! Your registration is pending for approval. You will receive a notification via your Gmail once approved.')
            return redirect('login')
        else:
            # I-display ang specific errors mula sa form validation
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
    else:
        form = EmployeeRegistrationForm()

    return render(request, 'register.html', {
        'form': form, 
        'schools': School.objects.all().order_by('name')
    })

# --- PASSWORD RESET OVERRIDE ---

class CustomPasswordResetView(auth_views.PasswordResetView):
    template_name = 'password_reset.html'
    form_class = CustomPasswordResetForm
    email_template_name = 'password_reset_email.html'
    subject_template_name = 'password_reset_subject.txt'
    
    def form_valid(self, form):
        # Dagdag validation: Siguraduhin na may nahanap na active user gamit ang Gmail na iyon
        email = form.cleaned_data.get('email')
        if not form.get_users(email).exists():
            messages.error(self.request, "No active account found with that Gmail address.")
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('password_reset_done')

# --- DASHBOARD SELECTOR ---

@login_required
def dashboard_selector(request):
    user = request.user
    if user.is_superuser:
        return redirect('super_admin_dashboard')
    elif getattr(user, 'is_deped_secretary', False):
        return redirect('admin_dashboard')
    elif getattr(user, 'is_school_head', False):
        return redirect('school_head_dashboard')
    else:
        return redirect('employee_profile')

# --- SUPER ADMIN VIEWS ---

@login_required
def super_admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('dashboard_selector')

    context = {
        'total_users': User.objects.count(),
        'total_schools': School.objects.count(),
        'total_memos': Document.objects.count(),
        'recent_users': User.objects.all().order_by('-date_joined')[:5],
        'title': "System Super Admin"
    }
    return render(request, 'super_admin_dashboard.html', context)

@login_required
def user_management(request):
    if not request.user.is_superuser:
        return redirect('dashboard_selector')
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'user_management.html', {'users': users})

@login_required
def add_user(request):
    if not request.user.is_superuser:
        return redirect('dashboard_selector')

    if request.method == 'POST':
        form = EmployeeRegistrationForm(request.POST)
        if form.is_valid():
            # I-save bilang ACTIVE dahil Super Admin ang gumawa
            user = form.save(is_admin_creation=True) 
            
            personal_email = form.cleaned_data.get('personal_email')
            deped_email = form.cleaned_data.get('email')
            full_name = form.cleaned_data.get('full_name')
            
            protocol = 'https' if request.is_secure() else 'http'
            domain = request.get_host()
            login_url = reverse('login') 
            system_link = f"{protocol}://{domain}{login_url}"

            subject = 'Account Activated - DepEd DMS'
            message = f"""
Dear {full_name},

Good day!

Your account has been successfully created and ACTIVATED in the Systematic Memorandum Automation & Reporting Services (DMS) by the ICT Administrator.

You can now log in to the system using your official credentials:

Official Email (Login ID): {deped_email}
Recovery Gmail: {personal_email}
Status: Active / Ready to Use

Please log in here to access your dashboard:
{system_link}

Thank you!
            """
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [personal_email],
                    fail_silently=False,
                )
                messages.success(request, f"User {user.email} created and activated successfully!")
            except Exception as e:
                messages.warning(request, f"User activated, but notification email failed: {str(e)}")

            return redirect('user_management')
        else:
            messages.error(request, "Failed to create user. Please check the form for errors.")
    else:
        form = EmployeeRegistrationForm()

    return render(request, 'add_user.html', {
        'form': form,
        'title': "Create New User"
    })

# --- PENDING APPROVALS LOGIC ---

@user_passes_test(is_super_admin)
def pending_approvals(request):
    pending_users = User.objects.filter(is_active=False).order_by('-date_joined')
    return render(request, 'pending_approvals.html', {'pending_users': pending_users})

@user_passes_test(is_super_admin)
def approve_user_process(request, user_id, action):
    if request.method == 'POST':
        target_user = get_object_or_404(User, id=user_id)
        
        if action == 'approve':
            target_user.is_active = True
            target_user.save()

            # Sa Gmail ipapadala ang approval notice
            recipient = target_user.personal_email or target_user.email
            
            try:
                protocol = 'https' if request.is_secure() else 'http'
                domain = request.get_host()
                login_url = reverse('login')
                system_link = f"{protocol}://{domain}{login_url}"

                subject = 'Account Approved - DepEd DMS'
                message = f"""
Dear {target_user.full_name},

Good day!

Your registration for the Systematic Memorandum Automation & Reporting Services (DMS) has been APPROVED by the administrator.

You can now log in to the system using your official DepEd email.

Account Details:
Login Email: {target_user.email}
Status: Active

Login here:
{system_link}

Thank you!
                """
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [recipient],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Error sending approval email: {e}")

            return JsonResponse({'status': 'success', 'message': 'User approved and notified via email!'})
        
        elif action == 'reject':
            target_user.delete()
            return JsonResponse({'status': 'success', 'message': 'User registration rejected.'})
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request.'}, status=400)

@login_required
def access_requests(request):
    if not request.user.is_superuser:
        return redirect('dashboard_selector')
    pending_users = User.objects.filter(is_active=False).order_by('-date_joined')
    return render(request, 'access_requests.html', {'pending_users': pending_users})

@login_required
def delete_user(request, user_id):
    if not request.user.is_superuser:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)
        
    if request.method == 'POST':
        user_to_delete = get_object_or_404(User, id=user_id)
        if user_to_delete == request.user:
            return JsonResponse({'status': 'error', 'message': 'You cannot delete your own account!'}, status=400)
        user_to_delete.delete()
        return JsonResponse({'status': 'success'})
        
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

@login_required
def edit_user(request, user_id):
    if not request.user.is_superuser:
        return redirect('dashboard_selector')
        
    user_profile = get_object_or_404(User, id=user_id)
    
    if request.method == "POST":
        user_profile.full_name = request.POST.get('full_name')
        user_profile.email = request.POST.get('email') or request.POST.get('deped_email')
        user_profile.personal_email = request.POST.get('personal_email')
        user_profile.position = request.POST.get('position')
        user_profile.education_level = request.POST.get('education_level')
        user_profile.employee_id = request.POST.get('employee_id')
        user_profile.contact_no = request.POST.get('contact_no')
        user_profile.year_graduated = request.POST.get('year_graduated')

        school_id = request.POST.get('school')
        if school_id:
            try:
                school_obj = School.objects.get(id=school_id)
                user_profile.school = school_obj
            except (School.DoesNotExist, ValueError):
                pass

        if 'profile_picture' in request.FILES:
            user_profile.profile_picture = request.FILES['profile_picture']
            
        user_profile.save()
        messages.success(request, f"Profile of {user_profile.full_name} has been updated!")
        return redirect('user_management')

    all_schools = School.objects.all().order_by('name')
    context = {
        'user_profile': user_profile,
        'schools': all_schools,
    }
    return render(request, 'edit_user.html', context)

# --- DASHBOARDS ---

@login_required
def admin_dashboard(request):
    if not (getattr(request.user, 'is_deped_secretary', False) or request.user.is_superuser):
        return redirect('dashboard_selector')
    memos = Document.objects.all().order_by('-date_uploaded')
    return render(request, 'deped_dashboard.html', {'memos': memos, 'title': "DepEd Secretary Dashboard"})

@login_required
def school_head_dashboard(request):
    if not (getattr(request.user, 'is_school_head', False) or request.user.is_superuser):
        return redirect('dashboard_selector')
    memos = Document.objects.all().order_by('-date_uploaded')
    school_name = request.user.school.name if request.user.school else "No School Assigned"
    return render(request, 'school_head_dashboard.html', {'memos': memos, 'title': f"Portal: {school_name}"})

@login_required
def employee_profile(request):
    user = request.user
    if request.method == 'POST':
        user.full_name = request.POST.get('full_name', user.full_name)
        user.contact_no = request.POST.get('contact', user.contact_no)
        user.position = request.POST.get('position', user.position)
        user.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('employee_profile')
    return render(request, 'employee_profile.html', {'user': user})

@login_required
def received_documents(request):
    if request.user.is_superuser:
        memos = Document.objects.all().order_by('-date_uploaded')
    else:
        memos = Document.objects.filter(school=request.user.school).order_by('-date_uploaded')
    return render(request, 'received_documents.html', {'memos': memos})