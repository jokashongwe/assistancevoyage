from django.db import models
from django.contrib.auth.models import User
from voyage.models import Categorie
# Assurez-vous d'importer votre modèle Categorie existant

# 1. Définir quels documents sont nécessaires pour quelle catégorie
# Ex: Pour "Étudiant", il faut "Passeport", "Diplôme", "Relevés de notes"
class TypeDocument(models.Model):
    nom = models.CharField(max_length=100) # Ex: Passeport
    categorie = models.ForeignKey(Categorie, on_delete=models.CASCADE, related_name='documents_requis')
    obligatoire = models.BooleanField(default=True)
    description = models.TextField(blank=True, help_text="Ex: Scannez la page avec la photo")

    def __str__(self):
        return f"{self.nom} ({self.categorie.nom})"

# 2. Le Dossier du client
class Dossier(models.Model):
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon - Incomplet'),
        ('analyse', 'En cours d\'analyse'),
        ('valide', 'Validé - Prêt pour dépôt'),
        ('refuse', 'À corriger'),
    ]
    
    client = models.ForeignKey(User, on_delete=models.CASCADE)
    categorie = models.ForeignKey(Categorie, on_delete=models.SET_NULL, null=True) # Ex: Visa Étudiant
    date_creation = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')

    etape_creation = models.PositiveIntegerField(default=1, help_text="Étape actuelle du wizard (1, 2, 3...)")

    # Infos Voyage (Step 1)
    ville_depart = models.CharField(max_length=100, blank=True, null=True)
    ville_destination = models.CharField(max_length=100, blank=True, null=True)
    date_prevue_voyage = models.DateField(blank=True, null=True)

    # Infos Complémentaires (Step 2)
    a_deja_voyage = models.BooleanField(default=False, verbose_name="Avez-vous déjà voyagé ?")
    motif_detaille = models.TextField(blank=True, null=True, help_text="Décrivez votre projet en quelques lignes")
    
    # Pour stocker le résultat de l'analyse automatique
    pourcentage_completion = models.IntegerField(default=0)

    def __str__(self):
        return f"Dossier {self.categorie} - {self.client.username}"

    # L'INTELLIGENCE DU SYSTÈME : Calculer ce qui manque
    def analyser_dossier(self):
        documents_requis = self.categorie.documents_requis.filter(obligatoire=True)
        documents_soumis = self.fichiers.all()
        
        ids_requis = set(documents_requis.values_list('id', flat=True))
        ids_soumis = set(documents_soumis.values_list('type_document_id', flat=True))
        
        manquants = ids_requis - ids_soumis
        
        # Calcul pourcentage
        total = len(ids_requis)
        fait = len(ids_requis) - len(manquants)
        if total > 0:
            self.pourcentage_completion = int((fait / total) * 100)
        else:
            self.pourcentage_completion = 100
            
        # Mise à jour statut automatique
        if self.pourcentage_completion == 100 and self.statut == 'brouillon':
            self.statut = 'analyse'
            
        self.save()
        return manquants # Retourne les IDs des docs manquants

# 3. Les fichiers uploadés par le client
class FichierClient(models.Model):
    ETAT_CHOICES = [
        ('attente', 'En attente de vérification'),
        ('valide', 'Validé par un expert'),
        ('rejete', 'Rejeté (Illisible/Incorrect)'),
    ]
    
    dossier = models.ForeignKey(Dossier, related_name='fichiers', on_delete=models.CASCADE)
    type_document = models.ForeignKey(TypeDocument, on_delete=models.CASCADE)
    fichier = models.FileField(upload_to='clients/docs/')
    etat = models.CharField(max_length=20, choices=ETAT_CHOICES, default='attente')
    commentaire_admin = models.TextField(blank=True, help_text="Raison du rejet si nécessaire")
    date_upload = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type_document.nom} - {self.dossier.client.username}"
