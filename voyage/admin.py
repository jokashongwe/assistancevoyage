from django.contrib import admin
from .models import Categorie, Guide, Document, TravelService, Bourse

class DocumentInline(admin.TabularInline):
    model = Document
    extra = 1 # Affiche une ligne vide par défaut pour ajouter un doc

@admin.register(Guide)
class GuideAdmin(admin.ModelAdmin):
    list_display = ('titre', 'destination', 'categorie', 'date_creation')
    list_filter = ('categorie', 'destination')
    search_fields = ('titre', 'destination')
    prepopulated_fields = {'slug': ('titre',)}
    inlines = [DocumentInline] # Intègre les documents dans la page Guide

admin.site.register(Categorie)
admin.site.register(Bourse)
admin.site.register(TravelService)