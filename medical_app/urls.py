from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('upload/', views.upload_radiographie, name='upload_radiographie'),
    path('ajouter-patient/', views.ajouter_patient, name='ajouter_patient'),
]
