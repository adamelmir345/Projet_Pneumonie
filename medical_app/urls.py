from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('upload/', views.upload_radiographie, name='upload_radiographie'),
    path('ajouter-patient/', views.ajouter_patient, name='ajouter_patient'),
    path('patient/<int:patient_id>/', views.patient_detail, name='patient_detail'),
    path('valider-radio/<int:radio_id>/', views.valider_radio, name='valider_radio'),
    path('rapport-pdf/<int:radio_id>/', views.generer_rapport_pdf, name='generer_rapport_pdf'),
]
