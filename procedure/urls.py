# urls.py
from django.urls import path, include
from . import views

urlpatterns = [
    # ... vos autres URLs ...
    
    # Gestion des comptes (Login, Logout, Reset Password) gérée par Django
    path('accounts/', include('django.contrib.auth.urls')),
    
    # Notre URL personnalisée pour l'inscription
    path('accounts/signup/', views.signup, name='signup'),
    
    # Espace client (déjà fait précédemment)
    path('mon-espace/', views.tableau_bord, name='tableau_bord'),
    path('dossier/<int:dossier_id>/paiement/', views.choix_offre, name='choix_offre'),
    path('dossier/<int:dossier_id>/paiement/valider/<int:offre_id>/', views.valider_paiement, name='valider_paiement'),
]