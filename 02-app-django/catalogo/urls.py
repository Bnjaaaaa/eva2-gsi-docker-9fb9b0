from django.urls import path

from . import views

app_name = "catalogo"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("producto/<str:codigo>/", views.detalle, name="detalle"),
    path("salud/", views.salud, name="salud"),
]
