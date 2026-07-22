from django.shortcuts import render, redirect
from .models import Radiographie, Patient
from .forms import RadiographieForm, PatientForm

def ajouter_patient(request):
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = PatientForm()
    return render(request, 'medical_app/ajouter_patient.html', {'form': form})

def dashboard(request):
    # Récupère toutes les radiographies, de la plus récente à la plus ancienne
    radiographies = Radiographie.objects.all().order_by('-date_upload')
    return render(request, 'medical_app/dashboard.html', {'radiographies': radiographies})

def upload_radiographie(request):
    if request.method == 'POST':
        form = RadiographieForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()  # L'IA s'exécute automatiquement grâce à la méthode save() du modèle !
            return redirect('dashboard')
    else:
        form = RadiographieForm()
    return render(request, 'medical_app/upload.html', {'form': form})