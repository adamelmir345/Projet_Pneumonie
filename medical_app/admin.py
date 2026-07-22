from django.contrib import admin
from .models import Patient, Radiographie

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prenom', 'date_naissance', 'date_creation')
    search_fields = ('nom', 'prenom')

@admin.register(Radiographie)
class RadiographieAdmin(admin.ModelAdmin):
    list_display = ('patient', 'classe_predite', 'pourcentage_confiance', 'date_upload')
    list_filter = ('classe_predite', 'date_upload')
