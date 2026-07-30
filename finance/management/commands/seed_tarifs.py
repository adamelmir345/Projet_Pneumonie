from django.core.management.base import BaseCommand
from finance.models import Tarif


class Command(BaseCommand):
    help = "Peuple la base avec des tarifs médicaux de base."

    def handle(self, *args, **options):
        tarifs = [
            {"nom_acte": "Consultation médicale", "code": "CONS-01", "prix": "300.00"},
            {"nom_acte": "Radiographie thoracique", "code": "RAD-01", "prix": "500.00"},
            {"nom_acte": "Analyse IA (Diagnostic)", "code": "IA-01", "prix": "200.00"},
            {"nom_acte": "Rapport médical détaillé", "code": "RAP-01", "prix": "150.00"},
            {"nom_acte": "Consultation de suivi", "code": "CONS-02", "prix": "200.00"},
            {"nom_acte": "Échographie pulmonaire", "code": "ECH-01", "prix": "600.00"},
        ]

        created_count = 0
        for t in tarifs:
            obj, created = Tarif.objects.get_or_create(
                nom_acte=t["nom_acte"],
                defaults={"code": t["code"], "prix": t["prix"]}
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"  ✓ Tarif créé : {obj}"))
            else:
                self.stdout.write(f"  — Tarif existant : {obj}")

        self.stdout.write(self.style.SUCCESS(f"\n{created_count} tarif(s) créé(s) avec succès."))
