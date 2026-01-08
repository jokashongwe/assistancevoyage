from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from .models import Dossier, FichierClient, TypeDocument, Categorie, Offre
from django.contrib.auth import login
from .forms import SignUpForm, DossierEtape1Form, DossierEtape2Form
from django.contrib import messages
from django.utils import timezone

@login_required
def tableau_bord(request):
    # Récupère le dossier du client ou en crée un s'il n'existe pas
    # (Pour simplifier, on suppose ici qu'il choisit sa catégorie à l'inscription ou via un bouton)
    dossiers = Dossier.objects.filter(client=request.user)
    categories = Categorie.objects.filter()
    
    return render(request, 'procedure/dashboard.html', {'dossiers': dossiers, 'categories': categories})

@login_required
def choix_offre(request, dossier_id):
    dossier = get_object_or_404(Dossier, id=dossier_id, client=request.user)
    
    # Si déjà payé, on redirige vers le dashboard
    if dossier.est_paye:
        return redirect('detail_dossier', dossier_id=dossier.id)
        
    offres = Offre.objects.all().order_by('prix')
    
    return render(request, 'procedure/pricing.html', {
        'dossier': dossier,
        'offres': offres
    })

@login_required
def valider_paiement(request, dossier_id, offre_id):
    # Simulation de paiement (Mobile Money / Carte)
    dossier = get_object_or_404(Dossier, id=dossier_id, client=request.user)
    offre = get_object_or_404(Offre, id=offre_id)
    
    # Mise à jour du dossier
    dossier.offre = offre
    dossier.est_paye = True
    dossier.credits_restants = offre.credits_inclus
    dossier.date_paiement = timezone.now()
    dossier.reference_paiement = f"PAY-{timezone.now().strftime('%Y%m%d')}-{dossier.id}" # Fausse ref
    dossier.statut = 'analyse' # On passe en mode analyse direct
    dossier.save()
    
    messages.success(request, f"Paiement confirmé ! Vous avez {dossier.credits_restants} crédits de vérification.")
    return redirect('detail_dossier', dossier_id=dossier.id)

@login_required
def detail_dossier(request, dossier_id):
    dossier = get_object_or_404(Dossier, id=dossier_id, client=request.user)
    
    # Lance l'analyse automatique
    ids_manquants = dossier.analyser_dossier()
    
    # Récupère tous les types de docs requis pour cette catégorie
    tous_docs_requis = dossier.categorie.documents_requis.all()
    
    # Prépare une liste intelligente pour le template
    liste_controle = []
    for type_doc in tous_docs_requis:
        fichier_existe = dossier.fichiers.filter(type_document=type_doc).first()
        statut = 'manquant'
        if fichier_existe:
            statut = fichier_existe.etat # attente, valide, rejete
            
        liste_controle.append({
            'type': type_doc,
            'fichier': fichier_existe,
            'statut': statut
        })

    # Gestion de l'upload
    if request.method == 'POST' and request.FILES.get('fichier'):
        type_doc_id = request.POST.get('type_doc_id')
        type_doc = get_object_or_404(TypeDocument, id=type_doc_id)
        
        # On supprime l'ancien si existe (remplacement)
        FichierClient.objects.filter(dossier=dossier, type_document=type_doc).delete()
        
        FichierClient.objects.create(
            dossier=dossier,
            type_document=type_doc,
            fichier=request.FILES['fichier']
        )
        return redirect('detail_dossier', dossier_id=dossier.id)

    return render(request, 'procedure/detail_dossier.html', {
        'dossier': dossier,
        'liste_controle': liste_controle
    })

@login_required
def creer_dossier(request, categorie_id):
    cat = get_object_or_404(Categorie, id=categorie_id)
    dossier, created = Dossier.objects.get_or_create(client=request.user, categorie=cat)
    return redirect('detail_dossier', dossier_id=dossier.id)

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # On connecte l'utilisateur directement après l'inscription
            login(request, user)
            return redirect('tableau_bord')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})


@login_required
def wizard_dossier(request, categorie_id, dossier_id=None):
    categorie = get_object_or_404(Categorie, id=categorie_id)
    
    # Récupération ou Création
    if dossier_id:
        dossier = get_object_or_404(Dossier, id=dossier_id, client=request.user)
    else:
        dossier = Dossier.objects.create(
            client=request.user, 
            categorie=categorie,
            statut='brouillon',
            etape_creation=1
        )
        return redirect('wizard_dossier_step', categorie_id=categorie.id, dossier_id=dossier.id)

    step = dossier.etape_creation
    form = None
    # Pour l'étape 3, on n'utilise pas un "Form" Django classique mais une liste d'objets
    documents_attendus = [] 

    # --- LOGIQUE POST (Traitement) ---
    if request.method == 'POST':
        
        # Bouton "Sauvegarder et quitter"
        if 'sauvegarder_quitter' in request.POST:
             # (Votre code existant pour sauver et redirect dashboard...)
             return redirect('tableau_bord')

        # --- ÉTAPE 1 -> 2 ---
        if step == 1:
            form = DossierEtape1Form(request.POST, instance=dossier)
            if form.is_valid():
                form.save()
                dossier.etape_creation = 2
                dossier.save()
                return redirect('wizard_dossier_step', categorie_id=categorie.id, dossier_id=dossier.id)
        
        # --- ÉTAPE 2 -> 3 (Génération des requis) ---
        elif step == 2:
            form = DossierEtape2Form(request.POST, instance=dossier)
            if form.is_valid():
                form.save()
                
                # C'EST ICI QUE LA MAGIE OPÈRE :
                # 1. On récupère les types de documents obligatoires pour cette catégorie
                types_requis = categorie.documents_requis.all()
                
                # 2. On pré-crée les lignes FichierClient si elles n'existent pas encore
                for type_doc in types_requis:
                    FichierClient.objects.get_or_create(
                        dossier=dossier,
                        type_document=type_doc
                    )
                
                dossier.etape_creation = 3 # On passe à l'étape upload
                dossier.save()
                return redirect('wizard_dossier_step', categorie_id=categorie.id, dossier_id=dossier.id)

        # --- ÉTAPE 3 (Upload Final) ---
        elif step == 3:
            # Ici, pas de "form.is_valid()". On traite les fichiers manuellement.
            
            # On récupère tous les fichiers attendus pour ce dossier
            fichiers_attendus = FichierClient.objects.filter(dossier=dossier)
            
            fichiers_recus = 0
            
            for attente in fichiers_attendus:
                # Dans le HTML, le champ input aura le name="doc_ID" (ex: doc_12)
                input_name = f"doc_{attente.id}"
                
                if request.FILES.get(input_name):
                    attente.fichier = request.FILES[input_name]
                    attente.etat = 'attente' # On met en statut "à vérifier"
                    attente.save()
                    fichiers_recus += 1
            
            # On vérifie si au moins un fichier a été envoyé (ou tous, selon votre sévérité)
            if fichiers_recus > 0:
                dossier.analyser_dossier() # Met à jour le %
                messages.success(request, f"Bravo ! {fichiers_recus} documents ont été ajoutés.")
                #return redirect('detail_dossier', dossier_id=dossier.id)
                return redirect('choix_offre', dossier_id=dossier.id)
            else:
                messages.warning(request, "Veuillez télécharger au moins un document pour continuer.")

    # --- LOGIQUE GET (Affichage) ---
    else:
        if step == 1:
            form = DossierEtape1Form(instance=dossier)
        elif step == 2:
            form = DossierEtape2Form(instance=dossier)
        elif step == 3:
            # Pour l'étape 3, on récupère la liste des FichierClient créés à la fin de l'étape 2
            documents_attendus = FichierClient.objects.filter(dossier=dossier)

    return render(request, 'procedure/wizard_form.html', {
        'form': form,
        'dossier': dossier,
        'step': step,
        'total_steps': 3, # On passe à 3 étapes
        'documents_attendus': documents_attendus # On envoie la liste au template
    })