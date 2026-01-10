from django.contrib import admin
from .models import Dossier, FichierClient, TypeDocument, Offre

admin.site.register(Dossier)
admin.site.register(FichierClient)
admin.site.register(TypeDocument)
admin.site.register(Offre)


# Register your models here.
