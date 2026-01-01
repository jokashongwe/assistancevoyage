from django.shortcuts import render, get_object_or_404, redirect
from .models import Guide, Temoignage, FAQ, TravelService, Bourse
from django.utils import timezone
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .forms import ContactForm, SimulationForm

def accueil(request):
    # Récupérer les guides marqués comme "Phares" (limité à 3 ou 6 pour le design)
    guides_phares = Guide.objects.filter(est_actif=True, est_phare=True).order_by('-date_creation')[:3]
    
    # Récupérer les autres guides récents (exclure ceux qui sont déjà phares)
    guides_recents = Guide.objects.filter(est_actif=True, est_phare=False).order_by('-date_creation')[:6]

    temoignages = Temoignage.objects.filter(est_actif=True).order_by('-date_publication')[:4]
    services = TravelService.objects.all().order_by('ordre')

    context = {
        'services': services, # Ajoutez ceci
        'guides_phares': guides_phares,
        'guides_recents': guides_recents,
        'temoignages': temoignages
    }
    return render(request, 'voyage/accueil.html', context)

def page_faq(request):
    # On récupère les questions actives, triées par ordre
    faqs = FAQ.objects.filter(est_actif=True).order_by('ordre')
    return render(request, 'voyage/faq.html', {'faqs': faqs})

def detail_guide(request, slug):
    # Récupère le guide ou renvoie une erreur 404 si le slug n'existe pas
    guide = get_object_or_404(Guide, slug=slug, est_actif=True)
    
    # Pas besoin de récupérer 'documents' séparément, on utilisera guide.documents.all dans le template
    
    context = {
        'guide': guide,
    }
    return render(request, 'voyage/detail_guide.html', context)

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Récupération des données
            nom = form.cleaned_data['nom']
            email = form.cleaned_data['email']
            phone = form.cleaned_data['telephone']
            sujet = form.cleaned_data['sujet']
            message = form.cleaned_data['message']

            # Construction de l'email pour l'administrateur
            email_body = f"""
            Nouveau message via le site web :
            
            Nom : {nom}
            Email : {email}
            Téléphone : {phone}
            Sujet : {sujet}
            
            Message :
            {message}
            """

            try:
                # Envoi de l'email (configurez SMTP dans settings.py)
                send_mail(
                    f'Nouveau Contact Site Web : {nom}',
                    email_body,
                    email, # De (l'utilisateur)
                    [settings.DEFAULT_FROM_EMAIL], # Vers (l'admin)
                    fail_silently=False,
                )
                messages.success(request, "Votre message a bien été envoyé ! Un conseiller vous répondra sous 24h.")
                return redirect('contact')
            except Exception as e:
                messages.error(request, "Une erreur est survenue lors de l'envoi. Veuillez réessayer.")
    else:
        form = ContactForm()

    return render(request, 'voyage/contact.html', {'form': form})

def simulateur(request):
    # 1. GESTION DU PRÉ-REMPLISSAGE (GET)
    initial_data = {}
    if 'dest' in request.GET:
        # On récupère le paramètre ?dest=canada et on l'injecte dans le formulaire
        initial_data['destination'] = request.GET.get('dest')

    resultat = None
    guide_suggere = None # Nouveau : pour stocker le guide trouvé
    couleur = "gray"
    
    if request.method == 'POST':
        form = SimulationForm(request.POST)
        if form.is_valid():
            sim = form.save()
            
            # --- PETITE LOGIQUE D'ANALYSE (Algorithme simple) ---
            score = 0
            
            # Critère financier (Le plus important)
            if sim.situation_financiere == 'fort':
                score += 5
            elif sim.situation_financiere == 'moyen':
                score += 3
            
            # Critère âge/études (Exemple : Moins de 30 ans pour Licence est mieux)
            if sim.age < 30 and sim.niveau_etudes in ['bac_plus_3', 'bac_plus_5']:
                score += 3
            elif sim.age < 22 and sim.niveau_etudes == 'bac':
                score += 3
            
            # Détermination du message
            if score >= 6:
                titre = "Profil Excellent !"
                msg = "Votre profil semble très solide pour obtenir un visa. Ne perdez pas de temps."
                couleur = "green"
            elif score >= 3:
                titre = "Profil Prometteur"
                msg = "Vous avez des atouts, mais certains points (comme le garant ou l'âge) doivent être bien justifiés."
                couleur = "yellow"
            else:
                titre = "Profil à Analyser"
                msg = "Votre projet est ambitieux. Il faudra une stratégie spécifique pour convaincre l'ambassade."
                couleur = "red"
            
            # --- 2. RECHERCHE INTELLIGENTE DU GUIDE ---
            # On essaye de trouver un guide dont le titre ou la destination correspond au choix
            # Mapping simple : valeur du select -> mot clé à chercher dans Guide
            mots_cles = {
                'canada': 'Canada',
                'france': 'France',
                'belgique': 'Belgique',
                'usa': 'USA',
                'chine': 'Chine',
                'autre': 'Dubaï' # Par exemple
            }

            mot_cle = mots_cles.get(sim.destination, '')

            if mot_cle:
                # On cherche le premier guide qui contient ce pays dans sa destination
                guide_suggere = Guide.objects.filter(
                    destination__icontains=mot_cle, 
                    est_actif=True
                ).first()

            return render(request, 'voyage/resultat_simulation.html', {
                'titre': titre, 
                'msg': msg, 
                'couleur': couleur, 
                'sim': sim,
                'guide_suggere': guide_suggere
            })
    else:
        form = SimulationForm(initial=initial_data)

    return render(request, 'voyage/simulateur.html', {'form': form})

def detail_service(request, slug):
    service = get_object_or_404(TravelService, slug=slug)
    autres_services = TravelService.objects.exclude(id=service.id) # Pour la sidebar
    return render(request, 'voyage/detail_service.html', {
        'service': service,
        'autres_services': autres_services
    })

def liste_bourses(request):
    # On affiche seulement les bourses dont la date limite n'est pas passée
    aujourdhui = timezone.now().date()
    bourses = Bourse.objects.filter(est_active=True, date_limite__gte=aujourdhui).order_by('date_limite')
    
    return render(request, 'voyage/liste_bourses.html', {'bourses': bourses})

def detail_bourse(request, slug):
    bourse = get_object_or_404(Bourse, slug=slug)
    # On réutilise le CTA existant, donc pas besoin de logique complexe ici
    return render(request, 'voyage/detail_bourse.html', {'bourse': bourse})