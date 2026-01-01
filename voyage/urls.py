from django.urls import path
from . import views

urlpatterns = [
    path('', views.accueil, name='accueil'),
    path('guide/<slug:slug>/', views.detail_guide, name='detail_guide'),
    path('contact/', views.contact, name='contact'),
    path('simulation/', views.simulateur, name='simulateur'),
    path('faq/', views.page_faq, name='faq'),
    path('services/<slug:slug>/', views.detail_service, name='detail_service'),
    path('bourses/', views.liste_bourses, name='liste_bourses'),
    path('bourses/<slug:slug>/', views.detail_bourse, name='detail_bourse'),
]