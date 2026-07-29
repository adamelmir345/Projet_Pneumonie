from django import forms
from .models import Radiographie, Patient

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['nom', 'prenom', 'date_naissance', 'sexe', 'telephone', 'adresse',
                  'groupe_sanguin', 'poids', 'taille', 'allergies', 'fumeur',
                  'antecedents_medicaux', 'notes_medecin']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'}),
            'date_naissance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'sexe': forms.Select(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '06 12 34 56 78'}),
            'adresse': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Adresse du patient'}),
            'groupe_sanguin': forms.Select(attrs={'class': 'form-control'}),
            'poids': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'kg', 'step': '0.1'}),
            'taille': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'cm', 'step': '0.1'}),
            'allergies': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Allergies connues...'}),
            'fumeur': forms.Select(attrs={'class': 'form-control'}),
            'antecedents_medicaux': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Antécédents éventuels...'}),
            'notes_medecin': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Notes du médecin...'}),
        }

class RadiographieForm(forms.ModelForm):
    class Meta:
        model = Radiographie
        fields = ['patient', 'image']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }