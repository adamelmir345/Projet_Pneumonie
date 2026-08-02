import os
import json
import logging
from decimal import Decimal, InvalidOperation

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth, TruncDay
from django.utils import timezone
from django.http import HttpResponse
from django.template.loader import get_template
from django.conf import settings as django_settings
from django.core.cache import cache

from .models import Tarif, Facture, LigneFacture, Paiement
from .decorators import role_required
from medical_app.models import Patient, Radiographie

logger = logging.getLogger(__name__)


# =============================================================================
# 1. DASHBOARD FINANCE
# =============================================================================
@login_required
@role_required('Comptable')
def dashboard_finance(request):
    """Vue principale du module Finance avec KPIs et graphiques."""
    now = timezone.now()

    months_filter = request.GET.get('months', '6')
    try:
        months_filter = int(months_filter)
    except ValueError:
        months_filter = 6

    if months_filter == 999:
        time_threshold = now - timezone.timedelta(days=3650) # 10 years effectively
    else:
        time_threshold = now - timezone.timedelta(days=30 * months_filter)

    # --- KPIs globaux (Mis en cache) ---
    cache_key = f'finance_dashboard_kpis_{months_filter}'
    kpis = cache.get(cache_key)

    if not kpis:
        factures_all = Facture.objects.exclude(statut='ANNULEE').filter(date_emission__gte=time_threshold)
        ca_total = factures_all.aggregate(total=Sum('montant_total'))['total'] or Decimal('0.00')
    
        paiements_all = Paiement.objects.filter(facture__statut__in=['EN_ATTENTE', 'PARTIELLE', 'PAYEE'], facture__date_emission__gte=time_threshold)
        total_paye = paiements_all.aggregate(total=Sum('montant'))['total'] or Decimal('0.00')
    
        taux_recouvrement = round(float(total_paye) / float(ca_total) * 100, 1) if ca_total > 0 else 0
    
        factures_impayees = factures_all.filter(statut__in=['EN_ATTENTE', 'PARTIELLE'])
        nb_impayees = factures_impayees.count()
        montant_impaye = ca_total - total_paye
    
        nb_factures_mois = factures_all.filter(
            date_emission__year=now.year, date_emission__month=now.month
        ).count()
    
        # --- Évolution CA par mois ---
        ca_mois_labels = []
        ca_mois_values = []
    
        ca_mois_qs = (
            factures_all
            .annotate(mois=TruncMonth('date_emission'))
            .values('mois')
            .annotate(total=Sum('montant_total'))
            .order_by('mois')
        )
        for entry in ca_mois_qs:
            ca_mois_labels.append(entry['mois'].strftime('%b %Y'))
            ca_mois_values.append(float(entry['total']))
    
        # --- Répartition par méthode de paiement ---
        methodes_qs = (
            paiements_all
            .values('methode')
            .annotate(total=Sum('montant'))
            .order_by('-total')
        )
        methode_labels = [dict(Paiement.METHODE_CHOICES).get(m['methode'], m['methode']) for m in methodes_qs]
        methode_values = [float(m['total']) for m in methodes_qs]

        kpis = {
            'ca_total': ca_total,
            'total_paye': total_paye,
            'taux_recouvrement': taux_recouvrement,
            'nb_impayees': nb_impayees,
            'montant_impaye': montant_impaye,
            'nb_factures_mois': nb_factures_mois,
            'ca_mois_labels': ca_mois_labels,
            'ca_mois_values': ca_mois_values,
            'methode_labels': methode_labels,
            'methode_values': methode_values,
        }
        cache.set(cache_key, kpis, 300) # 5 minutes de cache

    # --- Dernières factures (temps réel, hors cache) ---
    factures_all_rt = Facture.objects.exclude(statut='ANNULEE').filter(date_emission__gte=time_threshold)
    dernieres_factures = factures_all_rt.order_by('-date_emission')[:5]

    context = {
        'ca_total': kpis['ca_total'],
        'total_paye': kpis['total_paye'],
        'taux_recouvrement': kpis['taux_recouvrement'],
        'nb_impayees': kpis['nb_impayees'],
        'montant_impaye': kpis['montant_impaye'],
        'nb_factures_mois': kpis['nb_factures_mois'],
        'dernieres_factures': dernieres_factures,
        # Charts
        'ca_mois_labels': json.dumps(kpis['ca_mois_labels']),
        'ca_mois_values': json.dumps(kpis['ca_mois_values']),
        'methode_labels': json.dumps(kpis['methode_labels']),
        'methode_values': json.dumps(kpis['methode_values']),
        'current_months': months_filter,
    }
    return render(request, 'finance/finance_dashboard.html', context)


# =============================================================================
# 2. LISTE DES FACTURES
# =============================================================================
@login_required
@role_required('Comptable')
def liste_factures(request):
    """Liste paginée avec filtres."""
    factures = Facture.objects.all()

    # Filtres GET
    statut_filter = request.GET.get('statut', '')
    patient_filter = request.GET.get('patient', '')
    date_debut = request.GET.get('date_debut', '')
    date_fin = request.GET.get('date_fin', '')

    if statut_filter:
        factures = factures.filter(statut=statut_filter)
    if patient_filter:
        factures = factures.filter(
            Q(patient__nom__icontains=patient_filter) |
            Q(patient__prenom__icontains=patient_filter)
        )
    if date_debut:
        factures = factures.filter(date_emission__date__gte=date_debut)
    if date_fin:
        factures = factures.filter(date_emission__date__lte=date_fin)

    paginator = Paginator(factures, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'statut_filter': statut_filter,
        'patient_filter': patient_filter,
        'date_debut': date_debut,
        'date_fin': date_fin,
        'statut_choices': Facture.STATUT_CHOICES,
    }
    return render(request, 'finance/liste_factures.html', context)


# =============================================================================
# 3. CRÉER UNE FACTURE
# =============================================================================
@login_required
@role_required('Comptable')
def creer_facture(request):
    """Formulaire de création de facture avec lignes dynamiques."""
    if request.method == 'POST':
        patient_id = request.POST.get('patient')
        radio_id = request.POST.get('radiographie', '')
        date_echeance = request.POST.get('date_echeance', '')
        notes = request.POST.get('notes', '')

        # Validation patient
        patient = get_object_or_404(Patient, id=patient_id)

        # Création de la facture
        facture = Facture(
            patient=patient,
            medecin_emetteur=request.user,
            notes=notes,
        )
        if radio_id:
            facture.radiographie = get_object_or_404(Radiographie, id=radio_id)
        if date_echeance:
            facture.date_echeance = date_echeance

        facture.save()

        # Récupérer les lignes dynamiques
        tarif_ids = request.POST.getlist('tarif_id[]')
        quantites = request.POST.getlist('quantite[]')

        if not tarif_ids:
            facture.delete_real()  # Supprimer si pas de lignes (avant émission)
            messages.error(request, "Vous devez ajouter au moins un acte.")
            return redirect('creer_facture')

        for tarif_id, qte in zip(tarif_ids, quantites):
            try:
                tarif = Tarif.objects.get(id=tarif_id, actif=True)
                qte_int = int(qte) if qte else 1
                if qte_int < 1:
                    qte_int = 1
                LigneFacture.objects.create(
                    facture=facture,
                    tarif=tarif,
                    quantite=qte_int,
                    prix_unitaire_snapshot=tarif.prix,
                )
            except (Tarif.DoesNotExist, ValueError):
                continue

        facture.calculer_montant_total()

        logger.info(
            f"[AUDIT] Facture {facture.numero} créée par {request.user.username} "
            f"pour {patient} — {facture.montant_total} MAD"
        )
        messages.success(request, f"Facture {facture.numero} créée avec succès.")
        return redirect('detail_facture', pk=facture.pk)

    # GET
    patients = Patient.objects.all().order_by('nom')
    tarifs = Tarif.objects.filter(actif=True)
    radiographies = Radiographie.objects.all().order_by('-date_upload')[:50]

    context = {
        'patients': patients,
        'tarifs': tarifs,
        'radiographies': radiographies,
    }
    return render(request, 'finance/creer_facture.html', context)


# =============================================================================
# 4. DÉTAIL D'UNE FACTURE
# =============================================================================
@login_required
@role_required('Comptable')
def detail_facture(request, pk):
    """Affichage complet de la facture avec paiements."""
    facture = get_object_or_404(Facture, pk=pk)
    lignes = facture.lignes.all()
    paiements = facture.paiements.all()
    methode_choices = Paiement.METHODE_CHOICES

    context = {
        'facture': facture,
        'lignes': lignes,
        'paiements': paiements,
        'methode_choices': methode_choices,
    }
    return render(request, 'finance/detail_facture.html', context)


# =============================================================================
# 5. ENREGISTRER UN PAIEMENT
# =============================================================================
@login_required
@role_required('Comptable')
def enregistrer_paiement(request, pk):
    """POST: crée un paiement et recalcule le statut."""
    facture = get_object_or_404(Facture, pk=pk)

    if request.method != 'POST':
        return redirect('detail_facture', pk=pk)

    if facture.statut == 'ANNULEE':
        messages.error(request, "Impossible de payer une facture annulée.")
        return redirect('detail_facture', pk=pk)

    if facture.statut == 'PAYEE':
        messages.error(request, "Cette facture est déjà entièrement payée.")
        return redirect('detail_facture', pk=pk)

    try:
        montant = Decimal(request.POST.get('montant', '0'))
    except (InvalidOperation, ValueError):
        messages.error(request, "Montant invalide.")
        return redirect('detail_facture', pk=pk)

    if montant <= 0:
        messages.error(request, "Le montant doit être strictement positif.")
        return redirect('detail_facture', pk=pk)

    solde = facture.solde_restant
    if montant > solde:
        messages.error(request, f"Le montant ({montant} MAD) dépasse le solde restant ({solde} MAD).")
        return redirect('detail_facture', pk=pk)

    methode = request.POST.get('methode', 'ESPECES')
    reference = request.POST.get('reference_transaction', '')

    Paiement.objects.create(
        facture=facture,
        montant=montant,
        methode=methode,
        reference_transaction=reference,
        enregistre_par=request.user,
    )

    logger.info(
        f"[AUDIT] Paiement {montant} MAD enregistré sur {facture.numero} "
        f"par {request.user.username} (méthode: {methode})"
    )
    messages.success(request, f"Paiement de {montant} MAD enregistré avec succès.")
    return redirect('detail_facture', pk=pk)


# =============================================================================
# 6. ANNULER UNE FACTURE
# =============================================================================
@login_required
@role_required('Comptable')
def annuler_facture(request, pk):
    """POST: passe le statut à ANNULEE."""
    facture = get_object_or_404(Facture, pk=pk)

    if request.method != 'POST':
        return redirect('detail_facture', pk=pk)

    if facture.statut == 'ANNULEE':
        messages.warning(request, "Cette facture est déjà annulée.")
        return redirect('detail_facture', pk=pk)

    facture.statut = 'ANNULEE'
    facture.save(update_fields=['statut'])

    logger.info(
        f"[AUDIT] Facture {facture.numero} annulée par {request.user.username}"
    )
    messages.success(request, f"Facture {facture.numero} annulée.")
    return redirect('liste_factures')


# =============================================================================
# 7. GÉNÉRATION PDF
# =============================================================================
@login_required
@role_required('Comptable')
def facture_pdf(request, pk):
    """Génère un PDF de la facture via xhtml2pdf."""
    from xhtml2pdf import pisa

    facture = get_object_or_404(Facture, pk=pk)
    template_path = 'finance/facture_pdf.html'

    # Récupérer le profil du médecin émetteur
    medecin = facture.medecin_emetteur
    medecin_profile = None
    if hasattr(medecin, 'profile'):
        medecin_profile = medecin.profile

    context = {
        'facture': facture,
        'lignes': facture.lignes.all(),
        'paiements': facture.paiements.all(),
        'patient': facture.patient,
        'medecin_profile': medecin_profile,
        'logo_path': os.path.join(django_settings.BASE_DIR, 'medical_app', 'static', 'img', 'logo.jpg'),
    }

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Facture_{facture.numero}.pdf"'

    template = get_template(template_path)
    html = template.render(context)

    pisa_status = pisa.CreatePDF(
        html, dest=response,
        link_callback=lambda uri, rel: os.path.join(
            django_settings.BASE_DIR, uri.replace(django_settings.MEDIA_URL, 'media/')
        )
    )

    if pisa_status.err:
        return HttpResponse("Erreur lors de la génération du PDF.", status=500)
    return response
