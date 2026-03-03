from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from .models import User, School, Document
from .forms import EmployeeRegistrationForm

# --- AUTHENTICATION VIEWS ---

@never_cache
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_selector')

    if request.method == 'POST':
        u = request.POST.get('username') 
        p = request.POST.get('password')
        remember_me = request.POST.get('remember')

        # --- EMAIL DOMAIN RESTRICTION ---
        # Allow superusers even without @deped.gov.ph for maintenance
        check_user = User.objects.filter(email=u).first()
        is_super = check_user.is_superuser if check_user else False

        if u and not u.lower().endswith('@deped.gov.ph') and not is_super:
            messages.error(request, "Access Denied. Only official DepEd email addresses (@deped.gov.ph) are allowed.")
            return render(request, 'login.html')

        user = authenticate(request, username=u, password=p)

        if user is not None:
            if user.is_active:
                login(request, user)
                
                # --- KEEP ME LOGGED IN LOGIC ---
                if remember_me:
                    request.session.set_expiry(1209600) # 2 weeks
                else:
                    request.session.set_expiry(0) # Browser close
                
                return redirect('dashboard_selector')
            else:
                messages.error(request, "Account disabled. Please contact the ICT Unit.")
        else:
            messages.error(request, "Incorrect email or password. Please try again.")
            
    return render(request, 'login.html')

@login_required
def logout_view(request):
    """View para sa User Logout."""
    logout(request)
    return redirect('login')

@never_cache
def register_view(request):
    """View for Employee Registration with @deped.gov.ph restriction."""
    if request.user.is_authenticated:
        return redirect('dashboard_selector')

    if request.method == 'POST':
        form = EmployeeRegistrationForm(request.POST)
        email = request.POST.get('email', '').lower()

        # --- EMAIL DOMAIN RESTRICTION ---
        if not email.endswith('@deped.gov.ph'):
            messages.error(request, "Registration Failed: Only official @deped.gov.ph emails are allowed.")
            return render(request, 'register.html', {
                'form': form,
                'schools': School.objects.all().order_by('name'),
            })

        if form.is_valid():
            user = form.save()
            messages.success(
                request, 
                f'Welcome {user.display_name}! Registration successful. You can now login.'
            )
            return redirect('login')
        else:
            if 'email' in form.errors:
                messages.error(request, form.errors['email'][0])
            else:
                messages.error(request, "Registration failed. Please check the errors in the form.")
    else:
        storage = messages.get_messages(request)
        storage.used = True
        form = EmployeeRegistrationForm()

    context = {
        'form': form,
        'schools': School.objects.all().order_by('name'),
    }
    return render(request, 'register.html', context)


# --- DASHBOARD LOGIC ---

@login_required
def dashboard_selector(request):
    user = request.user
    
    # 1. Super User (System Admin)
    if user.is_superuser:
        return redirect('superadmin_dashboard')

    # 2. DepEd Secretary (Promoted Admin Role)
    elif user.is_deped_secretary:
        return redirect('admin_dashboard')

    # 3. School Head
    elif user.is_school_head:
        return redirect('school_head_dashboard')

    # 4. Regular Employee (Default)
    else:
        return redirect('employee_profile')


# --- ROLE-BASED VIEWS ---

@login_required
def superadmin_dashboard(request):
    """Dashboard para sa System Administrator (superuser)."""
    if not request.user.is_superuser:
        return redirect('dashboard_selector')

    context = {
        'total_users': User.objects.count(),
        'total_schools': School.objects.count(),
        'total_memos': Document.objects.count(),
        'recent_users': User.objects.all().order_by('-date_joined')[:5],
        'title': "System Super Admin"
    }
    return render(request, 'superadmin_dashboard.html', context)

@login_required
def admin_dashboard(request):
    """Dashboard para sa DepEd Secretary."""
    if not (request.user.is_deped_secretary or request.user.is_superuser):
        return redirect('dashboard_selector')
        
    memos = Document.objects.all().order_by('-date_uploaded')
    context = {
        'memos': memos,
        'title': "DepEd Secretary Dashboard"
    }
    return render(request, 'deped_dashboard.html', context)

@login_required
def school_head_dashboard(request):
    """Dashboard para sa mga School Heads."""
    if not (request.user.is_school_head or request.user.is_superuser):
        return redirect('dashboard_selector')

    memos = Document.objects.all().order_by('-date_uploaded')
    school_name = request.user.school.name if request.user.school else "No School Assigned"
    
    context = {
        'memos': memos,
        'title': f"School Portal: {school_name}"
    }
    return render(request, 'school_head_dashboard.html', context)

@login_required
def employee_profile(request):
    """Landing page para sa mga regular employees."""
    user = request.user
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.contact_number = request.POST.get('contact', user.contact_number)
        user.address = request.POST.get('address', user.address)
        user.position = request.POST.get('position', user.position)
        user.save()
        
        messages.success(request, "Your profile has been updated successfully!")
        return redirect('employee_profile')
        
    return render(request, 'employee_profile.html', {'user': user})