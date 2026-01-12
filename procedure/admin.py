from django.contrib import admin
from .models import Dossier, FichierClient, TypeDocument, Offre, Universite

admin.site.register(Dossier)
admin.site.register(FichierClient)
admin.site.register(TypeDocument)
admin.site.register(Offre)
admin.site.register(Universite)


# Register your models here.
