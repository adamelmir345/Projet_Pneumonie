from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.http import FileResponse, Http404, JsonResponse
from django.conf import settings as django_settings
from django.db.models import Avg, Count
from django.utils import timezone
from django.core.cache import cache
from functools import wraps
import os
import threading
import logging
from .models import Radiographie, Patient
from .forms import RadiographieForm, PatientForm
from .utils import predict_pneumonia, generate_gradcam

logger = logging.getLogger(__name__)


# =============================================================================
# EXÉCUTION DE L'IA EN ARRIÈRE-PLAN (threading)
# =============================================================================
def run_ai_analysis(radio_id):
    """Lance la prédiction IA et le Grad-CAM dans un thread séparé."""
    import django
    django.db.connections.close_all()  # Fermer les connexions du thread parent
    
    try:
        radio = Radiographie.objects.get(id=radio_id)
        image_path = radio.image.path

        # 1. Prédiction IA
        classe, confiance = predict_pneumonia(image_path)
        radio.classe_predite = classe
        radio.pourcentage_confiance = confiance

        # 2. Grad-CAM
        heatmap_filename = f'heatmap_{os.path.basename(radio.image.name)}'
        heatmap_rel_path = os.path.join('heatmaps', heatmap_filename)
        heatmap_abs_path = os.path.join(django_settings.MEDIA_ROOT, heatmap_rel_path)

        if generate_gradcam(image_path, heatmap_abs_path):
            radio.heatmap_image = heatmap_rel_path

        # 3. Marquer comme terminée
        radio.statut_analyse = 'TERMINEE'
        radio.save(update_fields=['classe_predite', 'pourcentage_confiance', 'heatmap_image', 'statut_analyse'])
        logger.info(f"✅ Analyse terminée pour radio #{radio_id} → {classe} ({confiance}%)")

    except Exception as e:
        logger.error(f"❌ Erreur analyse radio #{radio_id}: {e}")
        try:
            radio = Radiographie.objects.get(id=radio_id)
            radio.statut_analyse = 'ERREUR'
            radio.save(update_fields=['statut_analyse'])
        except Exception:
            pass


# =============================================================================
# VUE PROTÉGÉE POUR LES FICHIERS MÉDIA (radiographies, photos de profil)
# =============================================================================
@login_required
def protected_media(request, path):
    """Sert les fichiers média uniquement aux utilisateurs authentifiés."""
    file_path = os.path.join(django_settings.MEDIA_ROOT, path)
    if not os.path.exists(file_path):
        raise Http404("Fichier introuvable.")
    # Vérification de sécurité : empêcher la traversée de répertoire
    real_path = os.path.realpath(file_path)
    media_root = os.path.realpath(django_settings.MEDIA_ROOT)
    if not real_path.startswith(media_root):
        raise Http404("Accès refusé.")
    return FileResponse(open(file_path, 'rb'))

def medecin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.groups.filter(name='Comptable').exists() and not request.user.groups.filter(name='Medecin').exists():
            messages.error(request, "Accès refusé. Vous êtes connecté en tant que Comptable.")
            return redirect('dashboard_finance')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@login_required
@medecin_required
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
@medecin_required
def dashboard(request):
    # Récupère toutes les radiographies pour la liste (non mis en cache car temps réel souhaité)
    radiographies = Radiographie.objects.all().order_by('-date_upload')
    
    # KPI Statistics (Mise en cache pour 5 minutes)
    kpis = cache.get('medical_dashboard_kpis')
    if not kpis:
        total_analyses = radiographies.count()
        cas_pneumonie = radiographies.filter(classe_predite='Pneumonie').count()
        today = timezone.now().date()
        cas_critiques_today = radiographies.filter(classe_predite='Pneumonie', date_upload__date=today).count()
        avg_confiance = radiographies.aggregate(avg=Avg('pourcentage_confiance'))['avg'] or 0
        total_patients = Patient.objects.count()
        
        kpis = {
            'total_analyses': total_analyses,
            'cas_pneumonie': cas_pneumonie,
            'cas_critiques_today': cas_critiques_today,
            'avg_confiance': avg_confiance,
            'total_patients': total_patients,
        }
        cache.set('medical_dashboard_kpis', kpis, 300)
    
    context = {
        'radiographies': radiographies,
        'total_analyses': kpis['total_analyses'],
        'cas_pneumonie': kpis['cas_pneumonie'],
        'cas_critiques_today': kpis['cas_critiques_today'],
        'avg_confiance': kpis['avg_confiance'],
        'total_patients': kpis['total_patients'],
    }
    return render(request, 'medical_app/dashboard.html', context)

@login_required
@medecin_required
def upload_radiographie(request):
    if request.method == 'POST':
        form = RadiographieForm(request.POST, request.FILES)
        if form.is_valid():
            radio = form.save(commit=False)
            radio.statut_analyse = 'EN_COURS'
            radio.classe_predite = 'En attente'
            radio.save()
            
            # Lancer l'IA dans un thread séparé
            thread = threading.Thread(target=run_ai_analysis, args=(radio.id,), daemon=True)
            thread.start()
            
            messages.info(request, "ANALYSE_EN_COURS")
            return redirect('dashboard')
    else:
        form = RadiographieForm()
    return render(request, 'medical_app/upload.html', {'form': form})


# =============================================================================
# ENDPOINT AJAX — Vérification du statut d'analyse
# =============================================================================
@login_required
def check_analysis_status(request):
    """Endpoint AJAX appelé par le dashboard pour vérifier les analyses en cours."""
    pending = Radiographie.objects.filter(statut_analyse='EN_COURS').values_list('id', flat=True)
    completed = []
    
    # Vérifier les radios dont le statut vient de passer à TERMINEE
    radio_ids = request.GET.get('ids', '')
    if radio_ids:
        ids = [int(i) for i in radio_ids.split(',') if i.isdigit()]
        done = Radiographie.objects.filter(id__in=ids, statut_analyse='TERMINEE')
        for r in done:
            completed.append({
                'id': r.id,
                'classe': r.classe_predite,
                'confiance': r.pourcentage_confiance,
                'patient': f"{r.patient.nom} {r.patient.prenom}",
            })
    
    return JsonResponse({
        'pending': list(pending),
        'completed': completed,
    })

@login_required
@medecin_required
def patient_detail(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    radiographies = patient.radiographies.all().order_by('-date_upload')
    return render(request, 'medical_app/patient_detail.html', {'patient': patient, 'radiographies': radiographies})

@login_required
@medecin_required
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
@medecin_required
def generer_rapport_pdf(request, radio_id):
    radio = get_object_or_404(Radiographie, id=radio_id)
    template_path = 'medical_app/rapport_pdf.html'
    context = {
        'radio': radio, 
        'patient': radio.patient,
    }
    
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
            
            if hasattr(request.user, 'profile'):
                request.user.profile.specialite = request.POST.get('specialite', '')
                request.user.profile.telephone = request.POST.get('telephone', '')
                request.user.profile.inpe = request.POST.get('inpe', '')
                request.user.profile.adresse_cabinet = request.POST.get('adresse_cabinet', '')
                if 'photo_profil' in request.FILES:
                    request.user.profile.photo_profil = request.FILES['photo_profil']
                request.user.profile.save()
                
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
@medecin_required
def statistics_view(request):
    from django.db.models import Count, Avg
    from django.db.models.functions import TruncMonth, TruncDay
    from django.utils import timezone
    import json

    # On met en cache tout le contexte des statistiques pour 5 minutes
    context = cache.get('medical_statistics_context')
    
    if not context:
        # --- KPIs Globaux ---
        total_analyses = Radiographie.objects.count()
        cas_pneumonie = Radiographie.objects.filter(classe_predite='Pneumonie').count()
        cas_normal = Radiographie.objects.filter(classe_predite='Normal').count()
        taux_pneumonie = round((cas_pneumonie / total_analyses * 100), 1) if total_analyses > 0 else 0
        avg_confiance = Radiographie.objects.aggregate(avg=Avg('pourcentage_confiance'))['avg'] or 0
        total_patients = Patient.objects.count()
    
        # --- Analyses par mois (6 derniers mois) ---
        six_months_ago = timezone.now() - timezone.timedelta(days=180)
        
        mois_labels = []
        mois_pneumonies = []
        mois_normaux = []
        
        mois_qs = (
            Radiographie.objects
            .filter(date_upload__gte=six_months_ago)
            .annotate(mois=TruncMonth('date_upload'))
            .values('mois')
            .annotate(total=Count('id'))
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
            mois_pneumonies.append(pneumo)
            mois_normaux.append(total - pneumo)
    
        # --- Analyses 30 derniers jours ---
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        jours30_labels = []
        jours30_pneumonies = []
        jours30_normaux = []
        
        jours30_qs = (
            Radiographie.objects
            .filter(date_upload__gte=thirty_days_ago)
            .annotate(jour=TruncDay('date_upload'))
            .values('jour')
            .annotate(total=Count('id'))
            .order_by('jour')
        )
        for entry in jours30_qs:
            jour = entry['jour']
            total = entry['total']
            pneumo = Radiographie.objects.filter(
                date_upload__year=jour.year,
                date_upload__month=jour.month,
                date_upload__day=jour.day,
                classe_predite='Pneumonie'
            ).count()
            jours30_labels.append(jour.strftime('%d %b'))
            jours30_pneumonies.append(pneumo)
            jours30_normaux.append(total - pneumo)
    
        # --- Analyses 7 derniers jours ---
        seven_days_ago = timezone.now() - timezone.timedelta(days=7)
        jours7_labels = []
        jours7_pneumonies = []
        jours7_normaux = []
        
        jours7_qs = (
            Radiographie.objects
            .filter(date_upload__gte=seven_days_ago)
            .annotate(jour=TruncDay('date_upload'))
            .values('jour')
            .annotate(total=Count('id'))
            .order_by('jour')
        )
        for entry in jours7_qs:
            jour = entry['jour']
            total = entry['total']
            pneumo = Radiographie.objects.filter(
                date_upload__year=jour.year,
                date_upload__month=jour.month,
                date_upload__day=jour.day,
                classe_predite='Pneumonie'
            ).count()
            jours7_labels.append(jour.strftime('%d %b'))
            jours7_pneumonies.append(pneumo)
            jours7_normaux.append(total - pneumo)
    
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
            'mois_pneumonies': json.dumps(mois_pneumonies),
            'mois_normaux': json.dumps(mois_normaux),
            'jours30_labels': json.dumps(jours30_labels),
            'jours30_pneumonies': json.dumps(jours30_pneumonies),
            'jours30_normaux': json.dumps(jours30_normaux),
            'jours7_labels': json.dumps(jours7_labels),
            'jours7_pneumonies': json.dumps(jours7_pneumonies),
            'jours7_normaux': json.dumps(jours7_normaux),
            'validation_data': json.dumps(validation_data),
            'sexe_data': json.dumps({s['sexe']: s['count'] for s in sexe_data}),
            'fumeur_data': json.dumps({f['fumeur']: f['count'] for f in fumeur_data}),
            'groupe_data': json.dumps({g['groupe_sanguin']: g['count'] for g in groupe_data}),
        }
        cache.set('medical_statistics_context', context, 300)
    return render(request, 'medical_app/statistics.html', context)