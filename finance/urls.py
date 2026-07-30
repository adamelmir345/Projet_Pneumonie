from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_finance, name='dashboard_finance'),
    path('factures/', views.liste_factures, name='liste_factures'),
    path('factures/creer/', views.creer_facture, name='creer_facture'),
    path('factures/<int:pk>/', views.detail_facture, name='detail_facture'),
    path('factures/<int:pk>/paiement/', views.enregistrer_paiement, name='enregistrer_paiement'),
    path('factures/<int:pk>/annuler/', views.annuler_facture, name='annuler_facture'),
    path('factures/<int:pk>/pdf/', views.facture_pdf, name='facture_pdf'),
]
