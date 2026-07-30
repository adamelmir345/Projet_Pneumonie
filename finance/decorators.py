from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def role_required(role_name):
    """
    Décorateur qui vérifie que l'utilisateur connecté appartient au groupe spécifié.
    Utilisation : @role_required('Comptable')
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.groups.filter(name=role_name).exists():
                return view_func(request, *args, **kwargs)
            messages.error(
                request,
                f"Accès refusé. Vous devez appartenir au groupe « {role_name} » pour accéder à cette page."
            )
            return redirect('dashboard')
        return _wrapped_view
    return decorator
