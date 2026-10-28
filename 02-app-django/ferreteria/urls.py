"""Rutas principales: catálogo en la raíz y panel de administración en /admin/."""
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "Ferretería — Administración"
admin.site.site_title = "Ferretería"
admin.site.index_title = "Gestión del catálogo"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("catalogo.urls")),
]
