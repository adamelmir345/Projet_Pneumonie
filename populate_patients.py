import os
import django
import random
from datetime import datetime, timedelta

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from medical_app.models import Patient

# Données marocaines réalistes
prenoms_masculins = ["Youssef", "Mohammed", "Ahmed", "Ali", "Hassan", "Omar", "Rachid", "Karim", "Amine", "Mehdi", "Yassine", "Othmane", "Hamza", "Anas", "Ilyas", "Saad", "Hicham", "Nabil", "Ayoub", "Walid", "Tarik", "Kamal", "Mourad", "Zakaria", "Ismail", "Bilal", "Adil", "Badr", "Soufiane", "Reda"]
prenoms_feminins = ["Fatima", "Khadija", "Aicha", "Amina", "Zineb", "Meriem", "Salma", "Sara", "Hiba", "Noura", "Imane", "Sanae", "Nadia", "Hanane", "Asmae", "Meryem", "Samira", "Leila", "Boutaina", "Chaimae", "Saloua", "Ihssane"]
noms = ["Alaoui", "El Fassi", "Benjelloun", "Tazi", "Bennis", "Lahlou", "El Amrani", "Bennani", "Chraibi", "Kabbaj", "Guessous", "Sqalli", "Berrada", "El Idrissi", "Benkirane", "El Ouazzani", "Ammor", "Sefrioui", "Tahiri", "Idrissi", "Naciri", "El Khayat", "Jazouli", "El Malki", "Daoudi", "Benmoussa", "El Othmani", "Riffi", "El Mansouri", "Zemmouri", "Sabir", "Qasmi", "Zniber", "Benchekroun", "Filali", "El Yacoubi", "Belghiti", "Oufkir", "El Majdoub", "Elalamy", "Mansouri", "El Harti", "El Hachimi", "El Bakkali", "Boujemaa", "Chafik", "Draoui"]

antecedents_possibles = [
    "Diabète de type 2, sous traitement (Metformine).",
    "Hypertension artérielle légère.",
    "Asthme diagnostiqué à l'enfance, traitement par ventoline au besoin.",
    "Fumeur régulier (environ 10 cigarettes/jour).",
    "Ancien fumeur (sevrage depuis 5 ans).",
    "Tuberculose pulmonaire traitée et guérie en 2012.",
    "Bronchite chronique hivernale.",
    "Allergie sévère à la pénicilline.",
    "Antécédents familiaux de maladies respiratoires et cardiaques.",
    "Hypercholestérolémie.",
    "Opération de l'appendicite en 2015."
]

def generate_random_date(start_year, end_year):
    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31)
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    return start_date + timedelta(days=random_number_of_days)

print("Génération de 50 patients marocains en cours...")

for _ in range(50):
    genre = random.choice(['M', 'F'])
    prenom = random.choice(prenoms_masculins) if genre == 'M' else random.choice(prenoms_feminins)
    nom = random.choice(noms)
    # Âge entre 18 et 80 ans environ
    date_naissance = generate_random_date(1944, 2006).date()
    
    # 40% de chance de n'avoir aucun antécédent, sinon 1 ou 2
    num_antecedents = random.choices([0, 1, 2], weights=[0.4, 0.4, 0.2])[0]
    if num_antecedents == 0:
        antecedents = random.choice(["Aucun antécédent médical connu.", "RAS", "Aucun antécédent particulier."])
    else:
        antecedents = " ".join(random.sample(antecedents_possibles, num_antecedents))
    
    # Création et sauvegarde du patient dans la DB
    Patient.objects.create(
        nom=nom,
        prenom=prenom,
        date_naissance=date_naissance,
        antecedents_medicaux=antecedents
    )

print(f"✅ Succès ! 50 patients ajoutés. Total dans la base de données : {Patient.objects.count()}")
