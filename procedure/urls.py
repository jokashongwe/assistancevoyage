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
]