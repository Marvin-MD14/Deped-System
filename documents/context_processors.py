from django.contrib.auth import get_user_model

User = get_user_model()

def global_user_counts(request):
    """
    Ito ang magbibigay ng 'pending_count' sa lahat ng templates 
    para sa Superadmin side navigation badge.
    """
    if request.user.is_authenticated and request.user.is_superuser:
        # Bilangin ang mga users na is_active=False (Pending Approval)
        count = User.objects.filter(is_active=False).count()
        return {
            'pending_count': count
        }
    
    # Kapag hindi logged in o hindi superuser, default ay 0
    return {'pending_count': 0}