from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages

# I-import ang lahat ng kailangan mula sa iyong models, forms, at choices
from .models import User, School, Document
from .forms import EmployeeRegistrationForm
from .choices import SCHOOL_CHOICES, GENDER_CHOICES

# --- AUTHENTICATION VIEWS ---

def login_view(request):
    """View para sa User Login."""
    if request.user.is_authenticated:
        return redirect('dashboard_selector')

    if request.method == 'POST':
        u = request.POST.get('email')  # Siguraduhing 'email' ang name sa HTML input mo
        p = request.POST.get('password')
        
        # Tandaan: Sa custom user, email ang madalas na ginagamit na username field
        user = authenticate(request, username=u, password=p)

        if user is not None:
            if user.is_active:
                login(request, user)
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
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from .forms import EmployeeRegistrationForm
from .models import School


@never_cache
@require_http_methods(["GET", "POST"])
def register_view(request):
    # Remove old messages to prevent duplicates
    storage = messages.get_messages(request)
    for message in storage:
        pass
    storage.used = True

    if request.method == 'POST':
        form = EmployeeRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            messages.success(
                request, 
                f'Welcome {user.display_name}! Registration successful. You can now login.'
            )
            return redirect('login')
        # If form invalid, Django errors will be shown automatically in template
    else:
        form = EmployeeRegistrationForm()

    context = {
        'form': form,
        'schools': School.objects.all().order_by('name'),  # FIXED: No is_active filter
    }
    
    return render(request, 'register.html', context)
# --- DASHBOARD LOGIC ---

@login_required
def dashboard_selector(request):
    """Traffic Controller: Idinidirekta ang user base sa kanilang role."""
    user = request.user
    if user.is_deped_admin or user.is_deped_secretary:
        return redirect('admin_dashboard')
    elif user.is_school_head:
        return redirect('school_head_dashboard')
    else:
        return redirect('employee_profile')

# --- ROLE-BASED VIEWS ---

@login_required
def admin_dashboard(request):
    """View para sa Superadmin at DepEd Secretary."""
    if not (request.user.is_deped_admin or request.user.is_deped_secretary):
        return redirect('dashboard_selector')
        
    memos = Document.objects.all().order_by('-date_uploaded')
    context = {
        'memos': memos,
        'title': "DepEd Central Dashboard"
    }
    return render(request, 'deped_dashboard.html', context)

@login_required
def school_head_dashboard(request):
    """View para sa mga School Heads."""
    if not request.user.is_school_head:
        return redirect('dashboard_selector')

    memos = Document.objects.all().order_by('-date_uploaded')
    
    # Kuhanin ang pangalan ng school para sa title
    school_name = request.user.school.name if request.user.school else "No School Assigned"
    
    context = {
        'memos': memos,
        'title': f"School Portal: {school_name}"
    }
    return render(request, 'school_head_dashboard.html', context)

@login_required
def employee_profile(request):
    """Dashboard ng Natural Employee para sa personal updates."""
    user = request.user
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.contact_number = request.POST.get('contact')
        user.address = request.POST.get('address')
        user.position = request.POST.get('position')
        user.save()
        messages.success(request, "Your profile has been updated successfully!")
        return redirect('employee_profile')
        
    return render(request, 'employee_profile.html', {'user': user})