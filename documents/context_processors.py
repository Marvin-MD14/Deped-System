from django.contrib.auth import get_user_model

User = get_user_model()

def global_user_counts(request):
    """
    Ito ang magbibigay ng 'pending_count' sa lahat ng templates.
    """
    if request.user.is_authenticated and request.user.is_superuser:
        # Bilangin ang mga users na is_active=False
        return {
            'pending_count': User.objects.filter(is_active=False).count()
        }
    return {'pending_count': 0}