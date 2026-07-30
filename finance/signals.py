from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Paiement
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Paiement)
def recalculer_statut_facture_on_save(sender, instance, created, **kwargs):
    """Recalcule le statut de la facture après chaque paiement."""
    if created:
        logger.info(
            f"[AUDIT] Paiement créé: {instance.montant} MAD sur {instance.facture.numero} "
            f"par {instance.enregistre_par.username}"
        )
    instance.facture.recalculer_statut()


@receiver(post_delete, sender=Paiement)
def recalculer_statut_facture_on_delete(sender, instance, **kwargs):
    """Recalcule le statut si un paiement est supprimé (admin uniquement)."""
    try:
        instance.facture.recalculer_statut()
    except Exception:
        pass  # La facture a peut-être été supprimée aussi
