from django import forms
from .models import Radiographie, Patient

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['nom', 'prenom', 'date_naissance', 'antecedents_medicaux']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'}),
            'date_naissance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'antecedents_medicaux': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Antécédents éventuels...'}),
        }

class RadiographieForm(forms.ModelForm):
    class Meta:
        model = Radiographie
        fields = ['patient', 'image']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }