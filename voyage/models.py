from django.db import models
from ckeditor.fields import RichTextField
from django.utils import timezone
from datetime import date


class Categorie(models.Model):
    TITRES_CHOICES = [
        ('etudiant', 'Visa Étudiant'),
        ('tourisme', 'Tourisme & Vacances'),
        ('travail', 'Permis de Travail'),
        ('medical', 'Évacuation Sanitaire'),
    ]
    nom = models.CharField(max_length=50, choices=TITRES_CHOICES)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.get_nom_display()

class Guide(models.Model):
    titre = models.CharField(max_length=200, verbose_name="Titre du guide")
    destination = models.CharField(max_length=100, help_text="Ex: Canada, Chine, Dubaï")
    categorie = models.ForeignKey(Categorie, on_delete=models.CASCADE, related_name="guides")
    image_couverture = models.ImageField(upload_to='guides/covers/')
    
    # Le champ magique pour le contenu riche
    contenu = RichTextField(verbose_name="Contenu détaillé du guide")
    est_phare = models.BooleanField(default=False, verbose_name="Mettre à la une sur l'accueil ?") # NOUVEAU
    
    # Infos méta
    slug = models.SlugField(unique=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    est_actif = models.BooleanField(default=True)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('detail_guide', args=[self.slug])

    class Meta:
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.titre} - {self.destination}"

class Document(models.Model):
    guide = models.ForeignKey(Guide, related_name='documents', on_delete=models.CASCADE)
    nom = models.CharField(max_length=100, help_text="Ex: Formulaire de demande")
    fichier = models.FileField(upload_to='guides/docs/')
    date_upload = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nom

class Simulation(models.Model):
    NIVEAU_ETUDES_CHOICES = [
        ('bac', 'Diplôme d\'État (Bac)'),
        ('bac_plus_3', 'Graduat / Licence (Bac+3)'),
        ('bac_plus_5', 'Licence / Master (Bac+5)'),
        ('doctorat', 'Doctorat'),
        ('autre', 'Autre / Professionnel'),
    ]

    DESTINATION_CHOICES = [
        ('canada', 'Canada'),
        ('france', 'France'),
        ('belgique', 'Belgique'),
        ('usa', 'USA'),
        ('chine', 'Chine'),
        ('autre', 'Autre'),
    ]

    BUDGET_CHOICES = [
        ('faible', 'Je n\'ai pas encore de budget'),
        ('moyen', 'J\'ai un garant (Famille)'),
        ('fort', 'J\'ai mes propres fonds / Compte bloqué'),
    ]

    nom_complet = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20) # Important pour WhatsApp
    age = models.PositiveIntegerField()
    niveau_etudes = models.CharField(max_length=20, choices=NIVEAU_ETUDES_CHOICES)
    destination = models.CharField(max_length=20, choices=DESTINATION_CHOICES)
    situation_financiere = models.CharField(max_length=20, choices=BUDGET_CHOICES)
    
    date_simulation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nom_complet} - {self.destination}"

class Temoignage(models.Model):
    TYPE_CHOICES = [
        ('visa', 'Photo de Visa (Preuve)'),
        ('client', 'Photo Client (Avis)'),
    ]

    nom_client = models.CharField(max_length=100, help_text="Mettre un prénom ou 'Anonyme' pour la confidentialité")
    destination = models.CharField(max_length=100, help_text="Ex: Canada, Dubaï")
    type_temoignage = models.CharField(max_length=20, choices=TYPE_CHOICES, default='visa')
    photo = models.ImageField(upload_to='temoignages/')
    message = models.TextField(blank=True, help_text="Le commentaire du client ou une description courte")
    date_publication = models.DateTimeField(auto_now_add=True)
    est_actif = models.BooleanField(default=True)

    class Meta:
        ordering = ['-date_publication']

    def __str__(self):
        return f"{self.nom_client} - {self.destination}"

class FAQ(models.Model):
    question = models.CharField(max_length=255, verbose_name="Question fréquente")
    # Utiliser RichText permet de mettre des liens (ex: "Voir nos tarifs") ou du gras dans la réponse
    reponse = RichTextField(verbose_name="Réponse détaillée")
    ordre = models.PositiveIntegerField(default=0, help_text="Plus le chiffre est petit, plus la question apparaît haut")
    est_actif = models.BooleanField(default=True)

    class Meta:
        verbose_name = "FAQ"
        verbose_name_plural = "Questions Fréquentes"
        ordering = ['ordre']

    def __str__(self):
        return self.question

class TravelService(models.Model):
    titre = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    icone = models.CharField(max_length=50, help_text="Nom de l'icone (ex: user-graduate)")
    image_banniere = models.ImageField(upload_to='services/')
    resume_court = models.TextField(help_text="Pour la carte sur l'accueil")
    contenu_complet = RichTextField(help_text="Description détaillée du service")
    ordre = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.titre

class Bourse(models.Model):
    COUVERTURE_CHOICES = [
        ('totale', 'Totale (Billet + Frais + Vie)'),
        ('partielle', 'Partielle (Frais de scolarité uniquement)'),
        ('exemption', 'Exemption de frais majorés'),
    ]

    titre = models.CharField(max_length=200, verbose_name="Nom de la bourse")
    slug = models.SlugField(unique=True)
    pays = models.CharField(max_length=100, verbose_name="Pays de destination")
    niveau = models.CharField(max_length=100, help_text="Ex: Licence, Master, Doctorat")
    
    couverture = models.CharField(max_length=20, choices=COUVERTURE_CHOICES, default='totale')
    date_limite = models.DateField(verbose_name="Date limite de candidature")
    
    image = models.ImageField(upload_to='bourses/')
    contenu = RichTextField(verbose_name="Détails et Critères")
    
    date_publication = models.DateTimeField(auto_now_add=True)
    est_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['date_limite'] # Les bourses qui expirent bientôt apparaissent en premier

    def __str__(self):
        return f"{self.titre} - {self.pays}"

    # Méthode pour savoir si la bourse est encore valide
    @property
    def est_valide(self):
        return self.date_limite >= date.today()
        
    # Calcul du nombre de jours restants
    @property
    def jours_restants(self):
        delta = self.date_limite - date.today()
        return delta.days