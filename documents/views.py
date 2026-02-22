from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache

# I-import ang iyong models at forms
from .models import User, School, Document
from .forms import EmployeeRegistrationForm

# --- AUTHENTICATION VIEWS ---

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_selector')

    if request.method == 'POST':
        # Binago: 'username' ang gamitin dahil ito ang nasa name="" ng HTML mo
        u = request.POST.get('username') 
        p = request.POST.get('password')
        
        user = authenticate(request, username=u, password=p)

        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect('dashboard_selector')
            else:
                messages.error(request, "Account disabled. Please contact the ICT Unit.")
        else:
            # Gagamit tayo ng 'error' tag para sa SweetAlert icon
            messages.error(request, "Incorrect email or password. Please try again.")
            
    return render(request, 'login.html')

@login_required
def logout_view(request):
    """View para sa User Logout."""
    logout(request)
    return redirect('login')


@never_cache
@require_http_methods(["GET", "POST"])
def register_view(request):
    """View para sa Employee Registration."""
    if request.user.is_authenticated:
        return redirect('dashboard_selector')

    if request.method == 'POST':
        form = EmployeeRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # SUCCESS MESSAGE: Babasahin ito ng SweetAlert sa login.html pagkatapos ng redirect
            messages.success(
                request, 
                f'Welcome {user.display_name}! Registration successful. You can now login.'
            )
            return redirect('login')
        else:
            # ERROR MESSAGE: Babasahin ito ng SweetAlert sa register.html
            messages.error(request, "Registration failed. Please check the errors in the form.")
    else:
        # Siguraduhin na malinis ang message storage sa bawat bagong load ng form
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
    if user.is_deped_admin or user.is_deped_secretary:
        return redirect('admin_dashboard')
    elif user.is_school_head:
        return redirect('school_head_dashboard')
    else:
        # Dito papasok ang normal employee pagka-login o pagka-register
        return redirect('employee_profile') # O kung may hiwalay kang 'employee_dashboard'

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
        # Ginagamitan ng default para hindi mag-null kung walang binago ang user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.contact_number = request.POST.get('contact', user.contact_number)
        user.address = request.POST.get('address', user.address)
        user.position = request.POST.get('position', user.position)
        user.save()
        
        messages.success(request, "Your profile has been updated successfully!")
        return redirect('employee_profile')
        
    return render(request, 'employee_profile.html', {'user': user})