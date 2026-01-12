"""
URL configuration for assistancevoyage project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from procedure import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('voyage.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/signup/', views.signup, name='signup'),
    path('mon-espace/', views.tableau_bord, name='tableau_bord'),
    path('nouveau-dossier/<int:categorie_id>/', views.wizard_dossier, name='creer_dossier'),
    path('dossier/<int:dossier_id>/', views.detail_dossier, name='detail_dossier'),
    path('nouveau-dossier/<int:categorie_id>/<int:dossier_id>/', views.wizard_dossier, name='wizard_dossier_step'),
    path('procedures/', include('procedure.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
