from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from .models import Dossier, FichierClient, TypeDocument, Categorie
from django.contrib.auth import login
from .forms import SignUpForm, DossierEtape1Form, DossierEtape2Form
from django.contrib import messages

@login_required
def tableau_bord(request):
    # Récupère le dossier du client ou en crée un s'il n'existe pas
    # (Pour simplifier, on suppose ici qu'il choisit sa catégorie à l'inscription ou via un bouton)
    dossiers = Dossier.objects.filter(client=request.user)
    categories = Categorie.objects.filter()
    
    return render(request, 'procedure/dashboard.html', {'dossiers': dossiers, 'categories': categories})

@login_required
def creer_dossier(request, categorie_id):
    cat = get_object_or_404(Categorie, id=categorie_id)
    dossier, created = Dossier.objects.get_or_create(client=request.user, categorie=cat)
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
    # 1. Récupération ou Création du brouillon
    categorie = get_object_or_404(Categorie, id=categorie_id)
    
    if dossier_id:
        dossier = get_object_or_404(Dossier, id=dossier_id, client=request.user)
    else:
        # Création initiale
        dossier = Dossier.objects.create(
            client=request.user, 
            categorie=categorie,
            statut='brouillon',
            etape_creation=1
        )
        return redirect('wizard_dossier_step', categorie_id=categorie.id, dossier_id=dossier.id)

    # Déterminer l'étape courante (soit via l'URL si on gérait des URLs distinctes, soit via le modèle)
    # Ici on utilise une logique simple basée sur POST
    
    step = dossier.etape_creation
    form = None

    if request.method == 'POST':
        # --- TRAITEMENT DES DONNÉES ---
        if 'sauvegarder_quitter' in request.POST:
             # L'utilisateur veut juste sauver l'état actuel et partir
             if step == 1: form = DossierEtape1Form(request.POST, instance=dossier)
             elif step == 2: form = DossierEtape2Form(request.POST, instance=dossier)
             
             if form.is_valid():
                 form.save()
                 messages.success(request, "Progression sauvegardée.")
                 return redirect('tableau_bord')

        # Navigation "Suivant"
        if step == 1:
            form = DossierEtape1Form(request.POST, instance=dossier)
            if form.is_valid():
                form.save()
                dossier.etape_creation = 2
                dossier.save()
                return redirect('wizard_dossier_step', categorie_id=categorie.id, dossier_id=dossier.id)
        
        elif step == 2:
            form = DossierEtape2Form(request.POST, instance=dossier)
            if form.is_valid():
                form.save()
                # Fin du wizard, on passe à l'analyse ou au tableau de bord
                dossier.etape_creation = 3 # Marqueur de fin
                dossier.save()
                # On lance une première analyse pour générer la liste des docs
                dossier.analyser_dossier() 
                messages.success(request, "Dossier initialisé avec succès ! Ajoutez maintenant vos documents.")
                return redirect('detail_dossier', dossier_id=dossier.id)

    else:
        # --- AFFICHAGE DU FORMULAIRE (GET) ---
        if step == 1:
            form = DossierEtape1Form(instance=dossier)
        elif step == 2:
            form = DossierEtape2Form(instance=dossier)
        else:
            # Si le wizard est fini (étape 3), on redirige vers le détail
            return redirect('detail_dossier', dossier_id=dossier.id)

    return render(request, 'procedure/wizard_form.html', {
        'form': form,
        'dossier': dossier,
        'step': step,
        'total_steps': 2
    })