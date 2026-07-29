import os
import sys
import django
import random
from datetime import date, timedelta

# Configuration Django
sys.path.append('/Users/adamelmir/Documents/WEB_SITE/Projet_Pneumonie')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from medical_app.models import Patient, Radiographie
from django.contrib.auth.models import User

# Listes de données factices
NOMS = ['Dupont', 'Martin', 'Bernard', 'Dubois', 'Thomas', 'Robert', 'Richard', 'Petit', 'Durand', 'Leroy']
PRENOMS_HOMMES = ['Jean', 'Pierre', 'Michel', 'Philippe', 'Alain', 'Jacques', 'Bernard', 'Marcel', 'Daniel', 'René']
PRENOMS_FEMMES = ['Marie', 'Jeanne', 'Monique', 'Sylvie', 'Suzanne', 'Jacqueline', 'Catherine', 'Martine', 'Madeleine', 'Françoise']

SEXES = ['Homme', 'Femme']
GROUPES = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
FUMEURS = ['Non-fumeur', 'Fumeur', 'Ancien fumeur']

def create_dummy_data(n=20):
    for i in range(n):
        sexe = random.choice(SEXES)
        nom = random.choice(NOMS)
        prenom = random.choice(PRENOMS_HOMMES) if sexe == 'Homme' else random.choice(PRENOMS_FEMMES)
        
        # Date de naissance aléatoire entre 20 et 80 ans
        age_days = random.randint(20 * 365, 80 * 365)
        naissance = date.today() - timedelta(days=age_days)
        
        groupe = random.choice(GROUPES)
        fumeur = random.choice(FUMEURS)
        poids = round(random.uniform(50.0, 100.0), 1)
        taille = round(random.uniform(150.0, 190.0), 1)
        
        p = Patient.objects.create(
            nom=nom,
            prenom=prenom,
            date_naissance=naissance,
            sexe=sexe,
            groupe_sanguin=groupe,
            fumeur=fumeur,
            poids=poids,
            taille=taille
        )
        print(f"Patient créé: {p.nom} {p.prenom} ({p.sexe}, {p.groupe_sanguin})")

if __name__ == '__main__':
    create_dummy_data(25)
    print("25 patients factices ajoutés avec succès.")
