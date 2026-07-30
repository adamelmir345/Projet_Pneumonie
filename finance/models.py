import logging
from decimal import Decimal
from django.db import models, transaction
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from medical_app.models import Patient, Radiographie

logger = logging.getLogger(__name__)


class Tarif(models.Model):
    """Catalogue des actes médicaux facturables."""
    nom_acte = models.CharField(max_length=100)
    code = models.CharField(max_length=20, blank=True, null=True, help_text="Code nomenclature (CCAM/NGAP)")
    prix = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ['nom_acte']
        verbose_name = "Tarif"
        verbose_name_plural = "Tarifs"

    def __str__(self):
        return f"{self.nom_acte} — {self.prix} MAD"


class Facture(models.Model):
    """Facture émise pour un patient."""

    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('PARTIELLE', 'Partiellement payée'),
        ('PAYEE', 'Payée'),
        ('ANNULEE', 'Annulée'),
    ]

    numero = models.CharField(max_length=20, unique=True, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='factures')
    radiographie = models.ForeignKey(
        Radiographie, null=True, blank=True, on_delete=models.SET_NULL, related_name='factures'
    )
    date_emission = models.DateTimeField(auto_now_add=True)
    date_echeance = models.DateField(null=True, blank=True)
    montant_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='EN_ATTENTE')
    medecin_emetteur = models.ForeignKey(User, on_delete=models.PROTECT, related_name='factures_emises')
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-date_emission']
        verbose_name = "Facture"
        verbose_name_plural = "Factures"

    def __str__(self):
        return f"{self.numero} — {self.patient} — {self.montant_total} MAD"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self._generer_numero()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError(
            "Les factures émises ne peuvent pas être supprimées. Utilisez l'annulation."
        )

    @staticmethod
    def _generer_numero():
        """Génère un numéro de facture atomique : FAC-YYYY-NNNN."""
        from django.utils import timezone
        annee = timezone.now().year
        prefix = f"FAC-{annee}-"

        with transaction.atomic():
            last = (
                Facture.objects
                .filter(numero__startswith=prefix)
                .select_for_update()
                .order_by('-numero')
                .first()
            )
            if last:
                last_num = int(last.numero.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1

        return f"{prefix}{new_num:04d}"

    @property
    def montant_paye(self):
        """Somme de tous les paiements liés."""
        total = self.paiements.aggregate(total=models.Sum('montant'))['total']
        return total or Decimal('0.00')

    @property
    def solde_restant(self):
        """Montant restant à payer."""
        return self.montant_total - self.montant_paye

    def recalculer_statut(self):
        """Recalcule le statut en fonction des paiements."""
        if self.statut == 'ANNULEE':
            return  # Ne jamais changer une facture annulée

        paye = self.montant_paye
        if paye <= Decimal('0.00'):
            self.statut = 'EN_ATTENTE'
        elif paye < self.montant_total:
            self.statut = 'PARTIELLE'
        else:
            self.statut = 'PAYEE'
        self.save(update_fields=['statut'])

    def calculer_montant_total(self):
        """Recalcule le montant total à partir des lignes."""
        total = Decimal('0.00')
        for ligne in self.lignes.all():
            total += ligne.prix_unitaire_snapshot * ligne.quantite
        self.montant_total = total
        self.save(update_fields=['montant_total'])


class LigneFacture(models.Model):
    """Ligne intermédiaire entre Facture et Tarif."""
    facture = models.ForeignKey(Facture, on_delete=models.CASCADE, related_name='lignes')
    tarif = models.ForeignKey(Tarif, on_delete=models.PROTECT, related_name='lignes_factures')
    quantite = models.PositiveIntegerField(default=1)
    prix_unitaire_snapshot = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="Prix unitaire au moment de la facturation (snapshot)"
    )

    class Meta:
        verbose_name = "Ligne de facture"
        verbose_name_plural = "Lignes de facture"

    def __str__(self):
        return f"{self.tarif.nom_acte} x{self.quantite} — {self.sous_total} MAD"

    @property
    def sous_total(self):
        return self.prix_unitaire_snapshot * self.quantite


class Paiement(models.Model):
    """Enregistrement d'un paiement sur une facture."""

    METHODE_CHOICES = [
        ('ESPECES', 'Espèces'),
        ('CARTE', 'Carte bancaire'),
        ('VIREMENT', 'Virement'),
        ('ASSURANCE', 'Assurance'),
        ('AUTRE', 'Autre'),
    ]

    facture = models.ForeignKey(Facture, on_delete=models.CASCADE, related_name='paiements')
    montant = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    methode = models.CharField(max_length=15, choices=METHODE_CHOICES, default='ESPECES')
    reference_transaction = models.CharField(max_length=100, blank=True, null=True)
    date_paiement = models.DateTimeField(auto_now_add=True)
    enregistre_par = models.ForeignKey(User, on_delete=models.PROTECT, related_name='paiements_enregistres')

    class Meta:
        ordering = ['-date_paiement']
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"

    def __str__(self):
        return f"Paiement {self.montant} MAD — {self.facture.numero}"
