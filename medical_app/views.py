from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from .models import Radiographie, Patient
from .forms import RadiographieForm, PatientForm

@login_required
def ajouter_patient(request):
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('ajouter_patient')
    else:
        form = PatientForm()
    
    patients = Patient.objects.all().order_by('-date_creation')
    total_patients = patients.count()
    # Patients with at least one pneumonia radio
    cas_critiques = Patient.objects.filter(radiographies__classe_predite='Pneumonie').distinct().count()
    # Patients with radios pending validation
    en_attente = Patient.objects.filter(radiographies__validation_medecin='En attente').distinct().count()
    
    context = {
        'form': form,
        'patients': patients,
        'total_patients': total_patients,
        'cas_critiques': cas_critiques,
        'en_attente': en_attente,
    }
    return render(request, 'medical_app/ajouter_patient.html', context)

@login_required
def dashboard(request):
    from django.utils import timezone
    from django.db.models import Avg
    # Récupère toutes les radiographies, de la plus récente à la plus ancienne
    radiographies = Radiographie.objects.all().order_by('-date_upload')
    
    # KPI Statistics
    total_analyses = radiographies.count()
    cas_pneumonie = radiographies.filter(classe_predite='Pneumonie').count()
    today = timezone.now().date()
    cas_critiques_today = radiographies.filter(classe_predite='Pneumonie', date_upload__date=today).count()
    avg_confiance = radiographies.aggregate(avg=Avg('pourcentage_confiance'))['avg'] or 0
    total_patients = Patient.objects.count()
    
    context = {
        'radiographies': radiographies,
        'total_analyses': total_analyses,
        'cas_pneumonie': cas_pneumonie,
        'cas_critiques_today': cas_critiques_today,
        'avg_confiance': avg_confiance,
        'total_patients': total_patients,
    }
    return render(request, 'medical_app/dashboard.html', context)

@login_required
def upload_radiographie(request):
    if request.method == 'POST':
        form = RadiographieForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()  # L'IA s'exécute automatiquement grâce à la méthode save() du modèle !
            return redirect('dashboard')
    else:
        form = RadiographieForm()
    return render(request, 'medical_app/upload.html', {'form': form})

@login_required
def patient_detail(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    radiographies = patient.radiographies.all().order_by('-date_upload')
    return render(request, 'medical_app/patient_detail.html', {'patient': patient, 'radiographies': radiographies})

@login_required
def valider_radio(request, radio_id):
    if request.method == 'POST':
        radio = get_object_or_404(Radiographie, id=radio_id)
        validation = request.POST.get('validation')
        if validation in dict(Radiographie.VALIDATION_CHOICES):
            radio.validation_medecin = validation
            # Save using update_fields to avoid re-triggering AI predict in save() method if any bugs occur
            radio.save(update_fields=['validation_medecin'])
        return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
    return redirect('dashboard')

import os
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

@login_required
def generer_rapport_pdf(request, radio_id):
    radio = get_object_or_404(Radiographie, id=radio_id)
    template_path = 'medical_app/rapport_pdf.html'
    context = {'radio': radio, 'patient': radio.patient}
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Rapport_Pneumonie_{radio.patient.nom}.pdf"'
    
    template = get_template(template_path)
    html = template.render(context)
    
    # create a pdf
    pisa_status = pisa.CreatePDF(
       html, dest=response, link_callback=lambda uri, rel: os.path.join(settings.BASE_DIR, uri.replace(settings.MEDIA_URL, 'media/')))
    
    if pisa_status.err:
       return HttpResponse('Une erreur s\'est produite lors de la génération du PDF', status=500)
    return response

@login_required
def settings_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_profile':
            request.user.first_name = request.POST.get('first_name', '')
            request.user.last_name = request.POST.get('last_name', '')
            request.user.email = request.POST.get('email', '')
            request.user.save()
            messages.success(request, 'Profil mis à jour avec succès.')
            
        elif action == 'change_password':
            current_password = request.POST.get('current_password', '')
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')
            
            if not request.user.check_password(current_password):
                messages.error(request, 'Le mot de passe actuel est incorrect.')
            elif new_password != confirm_password:
                messages.error(request, 'Les nouveaux mots de passe ne correspondent pas.')
            elif len(new_password) < 8:
                messages.error(request, 'Le mot de passe doit contenir au moins 8 caractères.')
            else:
                request.user.set_password(new_password)
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Mot de passe modifié avec succès.')
        
        return redirect('settings')
    
    # Statistics for the settings page
    total_analyses = Radiographie.objects.count()
    total_patients = Patient.objects.count()
    
    context = {
        'total_analyses': total_analyses,
        'total_patients': total_patients,
    }
    return render(request, 'medical_app/settings.html', context)

@login_required
def statistics_view(request):
    from django.db.models import Count, Avg
    from django.db.models.functions import TruncMonth
    from django.utils import timezone
    import json

    # --- KPIs Globaux ---
    total_analyses = Radiographie.objects.count()
    cas_pneumonie = Radiographie.objects.filter(classe_predite='Pneumonie').count()
    cas_normal = Radiographie.objects.filter(classe_predite='Normal').count()
    taux_pneumonie = round((cas_pneumonie / total_analyses * 100), 1) if total_analyses > 0 else 0
    avg_confiance = Radiographie.objects.aggregate(avg=Avg('pourcentage_confiance'))['avg'] or 0
    total_patients = Patient.objects.count()

    # --- Analyses par mois (6 derniers mois) ---
    six_months_ago = timezone.now() - timezone.timedelta(days=180)
    analyses_par_mois = (
        Radiographie.objects
        .filter(date_upload__gte=six_months_ago)
        .annotate(mois=TruncMonth('date_upload'))
        .values('mois')
        .annotate(total=Count('id'), pneumonie=Count('id', filter=Radiographie.objects.filter(classe_predite='Pneumonie').query.where if False else None))
        .order_by('mois')
    )
    # Recalcul propre
    analyses_par_mois_data = []
    mois_labels = []
    mois_totals = []
    mois_pneumonies = []
    mois_normaux = []
    
    mois_qs = (
        Radiographie.objects
        .filter(date_upload__gte=six_months_ago)
        .annotate(mois=TruncMonth('date_upload'))
        .values('mois')
        .annotate(
            total=Count('id'),
        )
        .order_by('mois')
    )
    for entry in mois_qs:
        mois = entry['mois']
        total = entry['total']
        pneumo = Radiographie.objects.filter(
            date_upload__year=mois.year,
            date_upload__month=mois.month,
            classe_predite='Pneumonie'
        ).count()
        mois_labels.append(mois.strftime('%b %Y'))
        mois_totals.append(total)
        mois_pneumonies.append(pneumo)
        mois_normaux.append(total - pneumo)

    # --- Validation médecin ---
    validations = Radiographie.objects.values('validation_medecin').annotate(count=Count('id'))
    validation_data = {v['validation_medecin']: v['count'] for v in validations}

    # --- Démographie patients ---
    sexe_data = Patient.objects.exclude(sexe__isnull=True).exclude(sexe='').values('sexe').annotate(count=Count('id'))
    fumeur_data = Patient.objects.exclude(fumeur__isnull=True).exclude(fumeur='').values('fumeur').annotate(count=Count('id'))
    groupe_data = Patient.objects.exclude(groupe_sanguin__isnull=True).exclude(groupe_sanguin='').values('groupe_sanguin').annotate(count=Count('id'))

    context = {
        'total_analyses': total_analyses,
        'cas_pneumonie': cas_pneumonie,
        'cas_normal': cas_normal,
        'taux_pneumonie': taux_pneumonie,
        'avg_confiance': round(avg_confiance, 1),
        'total_patients': total_patients,
        # Charts data (JSON for JS)
        'mois_labels': json.dumps(mois_labels),
        'mois_totals': json.dumps(mois_totals),
        'mois_pneumonies': json.dumps(mois_pneumonies),
        'mois_normaux': json.dumps(mois_normaux),
        'validation_data': json.dumps(validation_data),
        'sexe_data': json.dumps({s['sexe']: s['count'] for s in sexe_data}),
        'fumeur_data': json.dumps({f['fumeur']: f['count'] for f in fumeur_data}),
        'groupe_data': json.dumps({g['groupe_sanguin']: g['count'] for g in groupe_data}),
    }
    return render(request, 'medical_app/statistics.html', context)