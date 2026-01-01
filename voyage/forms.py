from django import forms
from .models import Simulation

class ContactForm(forms.Form):
    SUJETS = [
        ('', 'Choisissez un sujet...'),
        ('etudiant', 'Visa Étudiant'),
        ('travail', 'Permis de Travail'),
        ('tourisme', 'Tourisme / Vacances'),
        ('partenariat', 'Partenariat / Affaires'),
        ('autre', 'Autre demande'),
    ]

    nom = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 py-3',
            'placeholder': 'Votre nom complet'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 py-3',
            'placeholder': 'exemple@email.com'
        })
    )
    telephone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 py-3',
            'placeholder': '+243 ...'
        })
    )
    sujet = forms.ChoiceField(
        choices=SUJETS,
        widget=forms.Select(attrs={
            'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 py-3'
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            'rows': 5,
            'placeholder': 'Expliquez-nous votre projet de voyage...'
        })
    )

class SimulationForm(forms.ModelForm):
    class Meta:
        model = Simulation
        fields = ['nom_complet', 'telephone', 'age', 'niveau_etudes', 'destination', 'situation_financiere']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # On applique le style Tailwind à tous les champs automatiquement
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'w-full px-4 py-3 rounded-lg border-2 border-gray-200 focus:border-blue-500 focus:ring-0 transition duration-200 bg-gray-50'
            })