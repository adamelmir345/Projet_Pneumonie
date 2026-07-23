from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Radiographie, Patient
from .forms import RadiographieForm, PatientForm

@login_required
def ajouter_patient(request):
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = PatientForm()
    return render(request, 'medical_app/ajouter_patient.html', {'form': form})

@login_required
def dashboard(request):
    # Récupère toutes les radiographies, de la plus récente à la plus ancienne
    radiographies = Radiographie.objects.all().order_by('-date_upload')
    return render(request, 'medical_app/dashboard.html', {'radiographies': radiographies})

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