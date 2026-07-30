def finance_context(request):
    """Expose les rôles aux templates pour conditionner l'affichage des liens dans la barre latérale."""
    if request.user.is_authenticated:
        is_comptable = request.user.groups.filter(name='Comptable').exists()
        is_medecin = request.user.groups.filter(name='Medecin').exists()
        return {
            'is_comptable': is_comptable,
            'is_medecin': is_medecin,
            'is_pure_comptable': is_comptable and not is_medecin,
        }
    return {'is_comptable': False, 'is_medecin': False, 'is_pure_comptable': False}
