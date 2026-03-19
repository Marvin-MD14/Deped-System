from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import views as auth_views
from django.db.models import Count
from django.core.paginator import Paginator
from .models import School, Document, ReceivedDocument
# Imports para sa models at forms
from .models import User, School, Document, ReceivedDocument
from .forms import EmployeeRegistrationForm, CustomPasswordResetForm
User = get_user_model()
# Kunin ang official User model
User = get_object_or_404(get_user_model()) if not hasattr(get_user_model(), 'objects') else get_user_model()

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
            messages.success(request, f'Welcome {user.full_name}! Your registration is pending for approval. You will receive a notification via your Gmail once approved.')
            return redirect('login')
        else:
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
def superadmin_dashboard(request):
    """
    Dashboard para sa System Administrator na may Charts at Pending Requests.
    Nagpapakita ng kabuuang bilang ng users, schools, memos, at file distribution.
    """
    # 1. Security Check
    if not request.user.is_superuser:
        return redirect('dashboard_selector')

    # 2. Query para sa FlexCards (Statistics Overview)
    total_users = User.objects.count()
    total_schools = School.objects.count()
    total_memos = Document.objects.count()
    
    # Bilang ng mga dokumentong hindi pa nababasa
    unread_requests_count = ReceivedDocument.objects.filter(is_read=False).count()
    
    # Bilang ng mga Users na pending approval (is_active=False) 
    # Ito ang gagamitin para mag-sync sa sidebar badge mo
    pending_approvals_count = User.objects.filter(is_active=False).count()

    # 3. Query para sa Charts (File Distribution base sa Extension)
    pdf_count = Document.objects.filter(file__icontains='.pdf').count()
    word_count = Document.objects.filter(file__icontains='.doc').count()
    excel_count = Document.objects.filter(file__icontains='.xls').count()
    ppt_count = Document.objects.filter(file__icontains='.ppt').count()

    # 4. Recent Data (Limitado sa huling 5 entries)
    recent_uploads = Document.objects.all().order_by('-date_uploaded')[:5]
    pending_requests_list = ReceivedDocument.objects.filter(is_read=False).order_by('-date_received')[:5]

    # 5. Context Construction
    context = {
        # Card Counts
        'total_users': total_users,
        'total_schools': total_schools,
        'total_memos': total_memos,
        'unread_count': unread_requests_count,
        'pending_count': pending_approvals_count, # Para sa badge sa sidebar
        
        # Chart Data
        'pdf_count': pdf_count,
        'word_count': word_count,
        'excel_count': excel_count,
        'ppt_count': ppt_count,
        
        # Tables/Lists
        'recent_uploads': recent_uploads,
        'pending_requests': pending_requests_list,
        
        # Page Meta
        'title': "System Super Admin"
    }
    
    return render(request, 'superadmin_dashboard.html', context)

@login_required
def user_management(request):
    # Proteksyon: Siguraduhin na Super Admin lang ang makakapasok
    if not request.user.is_superuser:
        return redirect('dashboard_selector')
    
    # Kuhanin lahat ng users EXCEPT ang sarili mo (optional pero recommended)
    # Inalis natin ang filters para lumabas ang Secretary, School Heads, atbp.
    user_list = User.objects.all().exclude(id=request.user.id).order_by('-date_joined')

    # Pagination: 10 users kada page
    paginator = Paginator(user_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'user_management.html', {'page_obj': page_obj})

    # 2. Pagination Logic
    paginator = Paginator(user_list, 10) # 10 users kada page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 3. I-pass ang 'page_obj' sa template
    return render(request, 'user_management.html', {'page_obj': page_obj})

@login_required
def add_user(request):
    if not request.user.is_superuser:
        return redirect('dashboard_selector')

    if request.method == 'POST':
        form = EmployeeRegistrationForm(request.POST)
        if form.is_valid():
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

Your account has been successfully created and ACTIVATED in the Systematic Memorandum Automation & Reporting Services (DMS).

Login ID: {deped_email}
Status: Active

Login here: {system_link}
            """
            try:
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [personal_email])
                messages.success(request, f"User {user.email} created and activated successfully!")
            except Exception as e:
                messages.warning(request, f"User created, but notification failed: {str(e)}")

            return redirect('user_management')
    else:
        form = EmployeeRegistrationForm()
    return render(request, 'add_user.html', {'form': form, 'title': "Create New User"})

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
            
            recipient = target_user.personal_email or target_user.email
            subject = 'Account Approved - DepEd DMS'
            message = f"Dear {target_user.full_name},\n\nYour registration has been APPROVED. You can now log in using your DepEd email."
            
            try:
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient])
            except:
                pass
                
            return JsonResponse({'status': 'success', 'message': 'User approved!'})
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
            return JsonResponse({'status': 'error', 'message': 'You cannot delete yourself!'}, status=400)
        user_to_delete.delete()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def edit_user(request, user_id):
    if not request.user.is_superuser:
        return redirect('dashboard_selector')
        
    user_profile = get_object_or_404(User, id=user_id)
    
    if request.method == "POST":
        # Text Fields
        user_profile.full_name = request.POST.get('full_name')
        user_profile.deped_email = request.POST.get('deped_email') # Tiyaking 'deped_email' ang name sa HTML
        user_profile.personal_email = request.POST.get('personal_email')
        user_profile.position = request.POST.get('position')
        user_profile.education_level = request.POST.get('education_level')
        user_profile.employee_id = request.POST.get('employee_id')
        user_profile.contact_no = request.POST.get('contact_no')
        user_profile.year_graduated = request.POST.get('year_graduated')
        
        # Foreign Key: School
        school_id = request.POST.get('school')
        if school_id:
            user_profile.school = School.objects.filter(id=school_id).first()
            
        # File Field: Profile Picture
        if 'profile_picture' in request.FILES:
            user_profile.profile_picture = request.FILES['profile_picture']
            
        user_profile.save()
        messages.success(request, f"Profile of {user_profile.full_name} updated successfully!")
        
        # Mas mainam i-redirect sa parehong page para makita agad ang update
        return redirect('edit_user', user_id=user_id)

    return render(request, 'edit_user.html', {
        'user_profile': user_profile, 
        'schools': School.objects.all().order_by('name')
    })
# --- OTHER DASHBOARDS ---

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

# --- DOCUMENT LOGIC ---

@login_required
def received_documents(request):
    if request.user.is_superuser:
        memos = Document.objects.all().order_by('-date_uploaded')
    else:
        memos = Document.objects.filter(school=request.user.school).order_by('-date_uploaded')
    return render(request, 'received_documents.html', {'memos': memos})
@login_required
def upload_document(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        category = request.POST.get('category')
        uploaded_file = request.FILES.get('file')

        if not title or not uploaded_file:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': 'Required fields missing.'}, status=400)
            messages.error(request, "Title and File are required.")
        else:
            try:
                Document.objects.create(
                    uploaded_by=request.user,
                    title=title,
                    category=category,
                    file=uploaded_file,
                    school=request.user.school
                )
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'success', 'message': 'Uploaded successfully!'})
                messages.success(request, "Document uploaded successfully!")
                return redirect('upload_document')
            except Exception as e:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
                messages.error(request, f"Error: {str(e)}")

    # 1. Kunin ang mga dokumento ng current user
    user_docs = Document.objects.filter(uploaded_by=request.user).order_by('-date_uploaded')
    
    # 2. Kunin ang bilang ng mga users na pending (is_active=False)
    # Gagamitin ito para sa badge sa iyong sidebar
    pending_count = User.objects.filter(is_active=False).count()

    # 3. I-pass lahat sa context
    context = {
        'recent_logs': user_docs,
        'word_count': user_docs.filter(category='word').count(),
        'excel_count': user_docs.filter(category='excel').count(),
        'pdf_count': user_docs.filter(category='pdf').count(),
        'ppt_count': user_docs.filter(category='ppt').count(),
        'staff_users': User.objects.filter(is_active=True).exclude(id=request.user.id).order_by('full_name'),
        'unread_received_count': ReceivedDocument.objects.filter(recipient=request.user, is_read=False).count(),
        'unread_docs': ReceivedDocument.objects.filter(recipient=request.user, is_read=False).order_by('-date_received'),
        'pending_count': pending_count, # Siniguro kong may comma (,) sa dulo ng line bago ito
    }
    return render(request, 'upload_document.html', context)

@login_required
def delete_document(request, doc_id):
    if request.method == 'POST':
        doc = get_object_or_404(Document, id=doc_id)
        if doc.uploaded_by == request.user or request.user.is_superuser:
            doc.delete()
            return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)

@login_required
def send_document(request):
    if request.method == 'POST':
        document_id = request.POST.get('document_id')
        # Kinukuha ang listahan ng IDs mula sa checkboxes (recipient_ids[])
        recipient_ids = request.POST.getlist('recipient_ids[]')
        
        if not document_id or not recipient_ids:
            messages.error(request, "Pumili ng dokumento at mga tatanggap.")
            return redirect('upload_document')

        document = get_object_or_404(Document, id=document_id)
        
        for r_id in recipient_ids:
            recipient = User.objects.filter(id=r_id).first()
            if recipient:
                # Gagamit ng get_or_create para maiwasan ang duplicate sending ng parehong file
                ReceivedDocument.objects.get_or_create(
                    document=document,
                    recipient=recipient,
                    sender=request.user # Sinave natin ang nag-send
                )
        
        messages.success(request, f"Ang '{document.title}' ay matagumpay na naipadala.")
        return redirect('upload_document')
    
    return redirect('upload_document')
@login_required
def internal_chat(request):
    # Dito natin kukunin ang lahat ng users para sa sidebar ng messenger
    # Maliban sa sarili mo (request.user)
    users = User.objects.exclude(id=request.user.id)
    
    context = {
        'users': users,
        'segment': 'messenger', # Para sa active state ng sidebar
    }
    return render(request, 'internal_chat.html', context)