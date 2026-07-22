from django.db import models
from .utils import predict_pneumonia

class Patient(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField()
    antecedents_medicaux = models.TextField(blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nom} {self.prenom}"

class Radiographie(models.Model):
    RESULTAT_CHOICES = [
        ('Normal', 'Normal (Sain)'),
        ('Pneumonie', 'Pneumonie'),
        ('En attente', 'En attente'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='radiographies')
    image = models.ImageField(upload_to='radiographies/')
    date_upload = models.DateTimeField(auto_now_add=True)
    
    # Résultats de l'IA
    classe_predite = models.CharField(max_length=20, choices=RESULTAT_CHOICES, default='En attente')
    pourcentage_confiance = models.FloatField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Sauvegarde d'abord pour que le fichier image soit physiquement enregistré sur le disque
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Si c'est une nouvelle radio, on lance l'IA automatiquement
        if is_new and self.image:
            image_path = self.image.path
            classe, confiance = predict_pneumonia(image_path)
            self.classe_predite = classe
            self.pourcentage_confiance = confiance
            # Sauvegarde à nouveau pour mettre à jour les champs de l'IA sans réitérer la boucle
            super().save(update_fields=['classe_predite', 'pourcentage_confiance'])

    def __str__(self):
        return f"Radio de {self.patient.nom} - {self.classe_predite} ({self.pourcentage_confiance}%)"