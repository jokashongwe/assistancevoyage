# forms.py
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from .models import Dossier, Universite

class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, help_text='Requis pour recevoir les notifications de votre dossier.')

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email',)

    # On injecte le style Tailwind à tous les champs
    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'appearance-none rounded-none relative block w-full px-3 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm mb-4',
            })

# Style commun Tailwind
class TailwindForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            # Checkbox a besoin d'un style différent
            if isinstance(self.fields[field].widget, forms.CheckboxInput):
                self.fields[field].widget.attrs.update({'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'})
            else:
                self.fields[field].widget.attrs.update({
                    'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm py-3 px-4 bg-gray-50'
                })

class DossierEtape1Form(TailwindForm):
    class Meta:
        model = Dossier
        fields = ['ville_depart', 'pays_destination', 'date_prevue_voyage']
        widgets = {
            'date_prevue_voyage': forms.DateInput(attrs={'type': 'date'}),
        }

class DossierEtape3Form(TailwindForm):
    class Meta:
        model = Dossier
        fields = ['universite_choisie']

    def __init__(self, *args, **kwargs):
        # On récupère le pays choisi à l'étape 1 pour filtrer la liste
        pays = kwargs.pop('pays_filter', None)
        super().__init__(*args, **kwargs)
        if pays:
            self.fields['universite_choisie'].queryset = Universite.objects.filter(pays=pays)
            self.fields['universite_choisie'].empty_label = "Sélectionnez votre université cible..."

class DossierEtape2Form(TailwindForm):
    class Meta:
        model = Dossier
        fields = ['a_deja_voyage', 'motif_detaille']
        widgets = {
            'motif_detaille': forms.Textarea(attrs={'rows': 4}),
        }