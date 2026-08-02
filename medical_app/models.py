from django.db import models
from .utils import predict_pneumonia, generate_gradcam
from django.core.files.uploadedfile import InMemoryUploadedFile
from io import BytesIO
from PIL import Image
import sys
import os

class Patient(models.Model):
    SEXE_CHOICES = [
        ('Homme', 'Homme'),
        ('Femme', 'Femme'),
    ]
    GROUPE_SANGUIN_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]
    FUMEUR_CHOICES = [
        ('Non-fumeur', 'Non-fumeur'),
        ('Fumeur', 'Fumeur'),
        ('Ancien fumeur', 'Ancien fumeur'),
    ]

    # Identité
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField()
    sexe = models.CharField(max_length=10, choices=SEXE_CHOICES, blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    adresse = models.TextField(blank=True, null=True)

    # Médical
    groupe_sanguin = models.CharField(max_length=5, choices=GROUPE_SANGUIN_CHOICES, blank=True, null=True)
    poids = models.FloatField(blank=True, null=True, help_text="Poids en kg")
    taille = models.FloatField(blank=True, null=True, help_text="Taille en cm")
    allergies = models.TextField(blank=True, null=True)
    fumeur = models.CharField(max_length=20, choices=FUMEUR_CHOICES, blank=True, null=True)
    antecedents_medicaux = models.TextField(blank=True, null=True)
    notes_medecin = models.TextField(blank=True, null=True)

    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nom} {self.prenom}"


class Radiographie(models.Model):
    RESULTAT_CHOICES = [
        ('Normal', 'Normal (Sain)'),
        ('Pneumonie', 'Pneumonie'),
        ('En attente', 'En attente'),
    ]

    STATUT_ANALYSE_CHOICES = [
        ('EN_COURS', 'Analyse en cours'),
        ('TERMINEE', 'Analyse terminée'),
        ('ERREUR', 'Erreur'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='radiographies')
    image = models.ImageField(upload_to='radiographies/')
    image_thumbnail = models.ImageField(upload_to='radiographies/thumbnails/', null=True, blank=True)
    heatmap_image = models.ImageField(upload_to='heatmaps/', null=True, blank=True)
    date_upload = models.DateTimeField(auto_now_add=True)
    
    # Résultats de l'IA
    classe_predite = models.CharField(max_length=20, choices=RESULTAT_CHOICES, default='En attente')
    pourcentage_confiance = models.FloatField(null=True, blank=True)
    statut_analyse = models.CharField(max_length=20, choices=STATUT_ANALYSE_CHOICES, default='TERMINEE')

    # Validation par le médecin
    VALIDATION_CHOICES = [
        ('En attente', 'En attente'),
        ('Confirmé', 'Confirmé (L\'IA a raison)'),
        ('Corrigé (Normal)', 'Corrigé (C\'est Normal)'),
        ('Corrigé (Pneumonie)', 'Corrigé (C\'est une Pneumonie)'),
    ]
    validation_medecin = models.CharField(max_length=30, choices=VALIDATION_CHOICES, default='En attente')

    def save(self, *args, **kwargs):
        # Créer la miniature si l'image principale existe et que la miniature n'existe pas
        if self.image and not self.image_thumbnail:
            try:
                # Ouvrir l'image
                img = Image.open(self.image)
                # Convertir en RGB si nécessaire (pour éviter des soucis avec les PNG)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Redimensionner l'image (200x200 max)
                img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                
                # Sauvegarder dans un buffer en mémoire
                output = BytesIO()
                img.save(output, format='JPEG', quality=85)
                output.seek(0)
                
                # Générer le nom de fichier
                filename = os.path.basename(self.image.name)
                name, _ = os.path.splitext(filename)
                thumb_filename = f"{name}_thumb.jpg"
                
                # Assigner le fichier généré au champ
                self.image_thumbnail = InMemoryUploadedFile(
                    output, 'ImageField', thumb_filename,
                    'image/jpeg', sys.getsizeof(output), None
                )
            except Exception as e:
                print(f"Erreur lors de la génération de la miniature : {e}")

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Radio de {self.patient.nom} - {self.classe_predite} ({self.pourcentage_confiance}%)"
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class MedecinProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    photo_profil = models.ImageField(upload_to='profils/', blank=True, null=True)
    specialite = models.CharField(max_length=100, default='Pneumologue', blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    inpe = models.CharField(max_length=50, blank=True, verbose_name="INPE")
    adresse_cabinet = models.TextField(blank=True)

    def __str__(self):
        return f"Profil de {self.user.username}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        MedecinProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if not hasattr(instance, 'profile'):
        MedecinProfile.objects.get_or_create(user=instance)
    instance.profile.save()
