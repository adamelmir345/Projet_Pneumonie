import random
import logging
from decimal import Decimal
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from finance.models import Tarif, Facture, LigneFacture, Paiement
from medical_app.models import Patient

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Génère des données financières aléatoires mais réalistes (factures, lignes, paiements) pour les 6 derniers mois."

    def handle(self, *args, **options):
        self.stdout.write("Suppression des anciennes données financières...")
        Paiement.objects.all().delete()
        LigneFacture.objects.all().delete()
        Facture.objects.all().delete()

        patients = list(Patient.objects.all())
        if not patients:
            self.stdout.write(self.style.ERROR("Aucun patient trouvé. Veuillez d'abord ajouter des patients."))
            return

        emetteur = User.objects.first()
        if not emetteur:
            self.stdout.write(self.style.ERROR("Aucun utilisateur (médecin) trouvé."))
            return

        tarifs = list(Tarif.objects.filter(actif=True))
        if not tarifs:
            self.stdout.write(self.style.ERROR("Aucun tarif trouvé. Lancez 'python manage.py seed_tarifs' d'abord."))
            return

        methodes_paiement = ['ESPECES', 'CARTE', 'CARTE', 'CARTE', 'VIREMENT', 'ASSURANCE', 'ASSURANCE']

        now = timezone.now()
        start_date = now - timedelta(days=180)  # 6 derniers mois

        nb_factures = random.randint(60, 80)
        self.stdout.write(f"Génération de {nb_factures} factures...")

        for _ in range(nb_factures):
            # Date aléatoire dans les 6 derniers mois
            random_days = random.randint(0, 180)
            date_emission = start_date + timedelta(days=random_days)

            patient = random.choice(patients)
            
            facture = Facture.objects.create(
                patient=patient,
                medecin_emetteur=emetteur,
                notes="Consultation de routine" if random.random() > 0.5 else ""
            )
            
            # Modifier la date d'émission manuellement (auto_now_add écrase normalement cela)
            Facture.objects.filter(pk=facture.pk).update(date_emission=date_emission)
            facture.refresh_from_db()

            # Ajouter 1 à 3 lignes
            nb_lignes = random.choices([1, 2, 3], weights=[0.6, 0.3, 0.1])[0]
            lignes_tarifs = random.sample(tarifs, nb_lignes)
            
            for tarif in lignes_tarifs:
                qte = 1 if tarif.nom_acte != 'Radiographie thoracique' else random.randint(1, 2)
                LigneFacture.objects.create(
                    facture=facture,
                    tarif=tarif,
                    quantite=qte,
                    prix_unitaire_snapshot=tarif.prix
                )
            
            facture.calculer_montant_total()

            # Probabilités des statuts : 70% Payée, 15% Partielle, 10% En attente, 5% Annulée
            statut_rand = random.random()
            
            if statut_rand < 0.70:
                # PAYEE (1 ou 2 paiements)
                methode = random.choice(methodes_paiement)
                if random.random() < 0.8:
                    p = Paiement.objects.create(
                        facture=facture,
                        montant=facture.montant_total,
                        methode=methode,
                        enregistre_par=emetteur
                    )
                    Paiement.objects.filter(pk=p.pk).update(date_paiement=date_emission + timedelta(minutes=15))
                else:
                    # Paiement en 2 fois
                    moitie = round(facture.montant_total / Decimal('2'), 2)
                    p1 = Paiement.objects.create(
                        facture=facture, montant=moitie, methode=methode, enregistre_par=emetteur
                    )
                    Paiement.objects.filter(pk=p1.pk).update(date_paiement=date_emission + timedelta(minutes=15))
                    
                    p2 = Paiement.objects.create(
                        facture=facture, montant=facture.montant_total - moitie, methode=methode, enregistre_par=emetteur
                    )
                    Paiement.objects.filter(pk=p2.pk).update(date_paiement=date_emission + timedelta(days=7))

            elif statut_rand < 0.85:
                # PARTIELLE (Paiement inférieur au total)
                pourcentage = Decimal(random.uniform(0.3, 0.8))
                montant_partiel = round(facture.montant_total * pourcentage, 2)
                
                # Éviter un montant de 0 si la facture est très petite
                if montant_partiel >= Decimal('0.01'):
                    p = Paiement.objects.create(
                        facture=facture,
                        montant=montant_partiel,
                        methode=random.choice(methodes_paiement),
                        enregistre_par=emetteur
                    )
                    Paiement.objects.filter(pk=p.pk).update(date_paiement=date_emission + timedelta(hours=1))

            elif statut_rand < 0.95:
                # EN_ATTENTE
                pass  # Aucun paiement

            else:
                # ANNULEE
                facture.statut = 'ANNULEE'
                facture.save(update_fields=['statut'])

            # Ne pas oublier de recalculer le statut après les paiements !
            facture.refresh_from_db()
            if facture.statut != 'ANNULEE':
                facture.recalculer_statut()

        self.stdout.write(self.style.SUCCESS(f"✅ Génération terminée avec succès !"))
