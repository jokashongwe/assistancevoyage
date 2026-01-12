from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from .models import Dossier, FichierClient, TypeDocument, Categorie, Offre
from django.contrib.auth import login
from .forms import SignUpForm, DossierEtape1Form, DossierEtape2Form, DossierEtape3Form
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
        if step == 2 and request.method == 'POST':
            form = DossierEtape2Form(request.POST, instance=dossier)
            if form.is_valid():
                form.save()
                dossier.etape_creation = 3 # On va vers le choix université
                dossier.save()
                return redirect('wizard_dossier_step', categorie_id=categorie.id, dossier_id=dossier.id)

        # --- ÉTAPE 3 (Université) -> ÉTAPE 4 (Génération Documents & Recap) ---
        elif step == 3 and request.method == 'POST':
            # On passe le pays pour filtrer le formulaire
            form = DossierEtape3Form(request.POST, instance=dossier, pays_filter=dossier.pays_destination)
            if form.is_valid():
                form.save()
                
                # --- FUSION DES LISTES DE DOCUMENTS ---
                # 1. Documents pour le VISA (liés à la Catégorie "Étudiant")
                docs_visa = categorie.documents_requis.all()
                
                # 2. Documents pour l'ADMISSION (liés à l'Université choisie)
                docs_uni = dossier.universite_choisie.documents_admission.all()
                
                # 3. On crée les fiches vides pour TOUS ces documents
                # L'union (|) permet d'éviter les doublons si un document est demandé par les deux
                tous_docs = docs_visa | docs_uni 
                
                for type_doc in tous_docs.distinct():
                    FichierClient.objects.get_or_create(dossier=dossier, type_document=type_doc)
                
                dossier.etape_creation = 4 # Étape finale (Recap + Upload)
                dossier.save()
                return redirect('wizard_dossier_step', categorie_id=categorie.id, dossier_id=dossier.id)
        # --- LOGIQUE GET (Affichage) ---
    else:
        if step == 1: form = DossierEtape1Form(instance=dossier)
        elif step == 2: form = DossierEtape2Form(instance=dossier)
        elif step == 3: 
            # On passe le pays pour que la liste déroulante ne montre que les universités du pays choisi
            form = DossierEtape3Form(instance=dossier, pays_filter=dossier.pays_destination)
        elif step == 4:
            # Pour la dernière étape, on n'a pas de form, on affiche le RECAP
            pass

    return render(request, 'procedure/wizard_form.html', {
        'form': form,
        'dossier': dossier,
        'step': step,
        'total_steps': 4, # On passe à 3 étapes
        'documents_attendus': documents_attendus # On envoie la liste au template
    })