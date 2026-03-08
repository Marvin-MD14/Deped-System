from .models import User

def global_user_counts(request):
    """
    Ito ang magbibigay ng 'pending_count' sa lahat ng templates,
    lalo na sa sidebar para sa Super Admin notification badge.
    """
    if request.user.is_authenticated:
        # Bilangin ang mga users na hindi pa active (for approval)
        return {
            'pending_count': User.objects.filter(is_active=False).count()
        }
    return {'pending_count': 0}