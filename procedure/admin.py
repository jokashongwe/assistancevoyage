from django.contrib import admin
from .models import Dossier, FichierClient, TypeDocument

admin.site.register(Dossier)
admin.site.register(FichierClient)
admin.site.register(TypeDocument)


# Register your models here.
